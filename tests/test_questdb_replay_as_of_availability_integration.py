"""Opt-in disposable QuestDB acceptance for Replay availability support."""

import os
import time
from uuid import uuid4

import pytest
import questdb
from test_questdb_truth_history_integration import _assert_lifecycle, _server

from live15_quant_v2.data.replay_as_of.availability import (
    SUPPORTED_PROOF_SCHEMA_VERSION,
    AvailabilityKind,
    AvailabilityRecord,
    AvailabilitySupportError,
    AvailabilitySupportErrorCode,
)
from live15_quant_v2.data.replay_as_of.questdb_availability import (
    QuestDBAvailabilityStore,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("LIVE15_RUN_REPLAY_AVAILABILITY_QUESTDB_INTEGRATION") != "1",
    reason="set LIVE15_RUN_REPLAY_AVAILABILITY_QUESTDB_INTEGRATION=1 for task-owned QuestDB",
)


def _record(kind: AvailabilityKind, capture_id: str, policy: str | None, at: int) -> AvailabilityRecord:
    return AvailabilityRecord(kind, capture_id, policy, at, SUPPORTED_PROOF_SCHEMA_VERSION, "source/v1")


def _rows(database: questdb.QuestDB, sql: str) -> list[dict[str, object]]:
    return database.query(sql, []).to_pandas().to_dict(orient="records")


def _semantic_count(database: questdb.QuestDB, table: str, capture_id: str) -> int:
    rows = _rows(database, f"SELECT count() AS row_count FROM {table} WHERE kind = 'evidence' AND capture_id = '{capture_id}' AND policy_version IS NULL")
    row_count = rows[0]["row_count"]
    assert isinstance(row_count, int)
    return row_count


def _inject_physical_row(connection_string: str, table: str, record: AvailabilityRecord) -> None:
    database = questdb.connect(connection_string, auto_flush=False)
    sender = database.sender()
    try:
        sender.row(table, columns=QuestDBAvailabilityStore._fields(record), at=questdb.TimestampNanos(time.time_ns()))
        fsn = sender.flush_and_get_fsn()
        assert fsn is not None
        assert sender.await_acked_fsn(fsn, timeout_millis=5_000)
        visibility = _rows(database, f"SELECT wait_wal_table('{table}')")
        assert len(visibility) == 1 and next(iter(visibility[0].values())) is True
    finally:
        sender.close(flush=False)
        database.close()


def test_disposable_schema_append_idempotency_duplicates_and_incompatible_table_fail_closed(tmp_path) -> None:
    table = f"replay_availability_{uuid4().hex}"
    with _server(tmp_path) as server:
        adapter = QuestDBAvailabilityStore(server.connection_string, table_name=table, acknowledgement_timeout_millis=5_000)
        evidence = _record(AvailabilityKind.EVIDENCE, "capture-1", None, 11)
        authority = _record(AvailabilityKind.AUTHORITY, "capture-1", "data-truth/v1", 17)
        assert adapter.append(evidence) == evidence
        assert adapter.append(authority) == authority
        assert server.database is not None
        metadata = [row for row in _rows(server.database, "SELECT table_name, walEnabled, dedup, partitionBy, designatedTimestamp FROM tables()") if row["table_name"] == table]
        assert metadata == [{"table_name": table, "walEnabled": True, "dedup": False, "partitionBy": "DAY", "designatedTimestamp": "written_at_ns"}]
        columns = _rows(server.database, f"SELECT \"column\", type, designated, upsertKey FROM table_columns('{table}')")
        types = {str(row["column"]): row["type"] for row in columns}
        assert types == {
            "kind": "VARCHAR", "capture_id": "VARCHAR", "policy_version": "VARCHAR",
            "available_at_ns": "TIMESTAMP_NS", "proof_schema_version": "VARCHAR",
            "source_authority_identity": "VARCHAR", "written_at_ns": "TIMESTAMP_NS",
        }
        assert next(row for row in columns if row["column"] == "written_at_ns")["designated"] is True
        assert not any(row["upsertKey"] is True for row in columns)
        assert adapter.find(evidence.key) == evidence
        assert adapter.find(authority.key) == authority
        assert adapter.read_committed_floor() == 17
        assert adapter.append(evidence) == evidence
        assert _semantic_count(server.database, table, evidence.capture_id) == 1
        with pytest.raises(AvailabilitySupportError) as error:
            adapter.append(_record(AvailabilityKind.EVIDENCE, "capture-1", None, 19))
        assert error.value.code is AvailabilitySupportErrorCode.INVARIANT_CONFLICT
        adapter.close()
        reopened = QuestDBAvailabilityStore(server.connection_string, table_name=table, acknowledgement_timeout_millis=5_000)
        assert reopened.find(authority.key) == authority
        assert reopened.read_committed_floor() == 17
        duplicate = _record(AvailabilityKind.EVIDENCE, "duplicate", None, 23)
        _inject_physical_row(server.connection_string, table, duplicate)
        _inject_physical_row(server.connection_string, table, duplicate)
        with pytest.raises(AvailabilitySupportError) as error:
            reopened.find(duplicate.key)
        assert error.value.code is AvailabilitySupportErrorCode.INVARIANT_CONFLICT
        with pytest.raises(AvailabilitySupportError) as error:
            reopened.read_committed_floor()
        assert error.value.code is AvailabilitySupportErrorCode.INVARIANT_CONFLICT
        reopened.close()

        incompatible = f"replay_availability_incompatible_{uuid4().hex}"
        server.database.execute(f"CREATE TABLE {incompatible} (wrong VARCHAR, written_at_ns TIMESTAMP_NS) TIMESTAMP(written_at_ns) PARTITION BY DAY WAL")
        before = _rows(server.database, f"SELECT \"column\", type, designated, upsertKey FROM table_columns('{incompatible}')")
        bad = QuestDBAvailabilityStore(server.connection_string, table_name=incompatible, acknowledgement_timeout_millis=5_000)
        with pytest.raises(AvailabilitySupportError) as error:
            bad.find(evidence.key)
        assert error.value.code is AvailabilitySupportErrorCode.SOURCE_UNAVAILABLE
        after = _rows(server.database, f"SELECT \"column\", type, designated, upsertKey FROM table_columns('{incompatible}')")
        assert after == before
        bad.close()
    _assert_lifecycle(server)
