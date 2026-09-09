"""Controlled and opt-in integration coverage for the Replay QuestDB source."""

from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

import pytest


class _Frame:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def to_dict(self, *, orient: str) -> list[dict[str, Any]]:
        assert orient == "records"
        return self._rows


class _Result:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def to_pandas(self) -> _Frame:
        return _Frame(self._rows)


class _Database:
    def __init__(
        self,
        *,
        evidence: list[dict[str, Any]] | None = None,
        truth: list[dict[str, Any]] | None = None,
        availability: list[dict[str, Any]] | None = None,
        tables: list[dict[str, Any]] | None = None,
    ) -> None:
        self.queries: list[tuple[str, list[Any]]] = []
        self.evidence = list(evidence or [])
        self.truth = list(truth or [])
        self.availability = list(availability or [])
        self.tables = tables

    def query(self, sql: str, binds: list[Any]) -> _Result:
        self.queries.append((sql, binds))
        if "FROM tables()" in sql:
            if self.tables is not None:
                return _Result(self.tables)
            return _Result(
                [
                    {
                        "table_name": "evidence",
                        "designatedTimestamp": "received_timestamp",
                        "partitionBy": "DAY",
                        "walEnabled": True,
                        "dedup": True,
                    },
                    {
                        "table_name": "truth",
                        "designatedTimestamp": "physical_written_at",
                        "partitionBy": "DAY",
                        "walEnabled": True,
                        "dedup": False,
                    },
                    {
                        "table_name": "availability",
                        "designatedTimestamp": "written_at_ns",
                        "partitionBy": "DAY",
                        "walEnabled": True,
                        "dedup": False,
                    },
                ]
            )
        if "FROM table_columns" in sql:
            table = sql.split("table_columns('", 1)[1].split("')", 1)[0]
            columns = {
                "evidence": {
                    "capture_id": "VARCHAR",
                    "asset": "SYMBOL",
                    "provider": "SYMBOL",
                    "source_id": "VARCHAR",
                    "channel": "SYMBOL",
                    "message_type": "VARCHAR",
                    "event_subtype": "VARCHAR",
                    "sid": "LONG",
                    "seq": "LONG",
                    "provider_timestamp": "TIMESTAMP_NS",
                    "schema_version": "VARCHAR",
                    "payload": "VARCHAR",
                    "received_timestamp": "TIMESTAMP_NS",
                },
                "truth": {
                    "policy_version": "VARCHAR",
                    "subject_capture_id": "VARCHAR",
                    "category": "VARCHAR",
                    "contributing_capture_ids": "VARCHAR",
                    "reason": "VARCHAR",
                    "event_provider": "VARCHAR",
                    "event_source_id": "VARCHAR",
                    "event_message_type": "VARCHAR",
                    "event_trade_id": "VARCHAR",
                    "physical_written_at": "TIMESTAMP_NS",
                },
                "availability": {
                    "kind": "VARCHAR",
                    "capture_id": "VARCHAR",
                    "policy_version": "VARCHAR",
                    "available_at_ns": "TIMESTAMP_NS",
                    "proof_schema_version": "VARCHAR",
                    "source_authority_identity": "VARCHAR",
                    "written_at_ns": "TIMESTAMP_NS",
                },
            }[table]
            return _Result(
                [
                    {
                        "column": name,
                        "type": value,
                        "designated": name
                        in {
                            "received_timestamp",
                            "physical_written_at",
                            "written_at_ns",
                        },
                        "upsertKey": table == "evidence"
                        and name in {"received_timestamp", "capture_id"},
                    }
                    for name, value in columns.items()
                ]
            )
        if "FROM truth" in sql:
            return _Result(
                [row for row in self.truth if row["policy_version"] == binds[0]]
            )
        if "FROM evidence" in sql:
            return _Result(
                [row for row in self.evidence if row["capture_id"] == binds[0]]
            )
        if "FROM availability" in sql:
            rows = [
                row
                for row in self.availability
                if row["kind"] == binds[0] and row["capture_id"] == binds[1]
            ]
            policy = None if "IS NULL" in sql else binds[2]
            return _Result([row for row in rows if row["policy_version"] == policy])
        return _Result([])

    def close(self) -> None:
        pass


def _source(
    monkeypatch: pytest.MonkeyPatch,
    connection: str = "ws::addr=127.0.0.1:9000;",
    database: _Database | None = None,
) -> tuple[Any, _Database]:
    from live15_quant_v2.data.replay_as_of import questdb_source

    database = database or _Database()
    monkeypatch.setattr(
        questdb_source.questdb, "connect", lambda *_args, **_kwargs: database
    )
    source = questdb_source.QuestDBReplaySource(
        connection,
        evidence_table="evidence",
        truth_decision_table="truth",
        availability_table="availability",
        evidence_authority_identity="capture-authority/v1",
        truth_decision_authority_identity="truth-authority/v1",
        availability_authority_identity="availability-authority/v1",
    )
    return source, database


def test_authority_identities_are_stable_and_exclude_connection_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, _ = _source(monkeypatch, "ws::addr=127.0.0.1:9000;user=secret;")
    second, _ = _source(monkeypatch, "ws::addr=elsewhere:9000;user=other;")

    assert first.source_authorities() == second.source_authorities()
    assert all(
        len(value) == 64
        for value in (
            first.source_authorities().evidence,
            first.source_authorities().truth_decision,
            first.source_authorities().availability,
        )
    )


def _scope() -> Any:
    from live15_quant_v2.data.replay_as_of.models import ReplayOrdering, SelectionAxis
    from live15_quant_v2.data.replay_as_of.source import ReplayCandidateScope

    return ReplayCandidateScope(
        "data-truth/v1",
        20,
        SelectionAxis.ARRIVAL_TIME,
        0,
        30,
        None,
        None,
        ReplayOrdering.ARRIVAL,
    )


def _evidence(capture_id: str = "capture-1") -> dict[str, Any]:
    return {
        "capture_id": capture_id,
        "asset": "BTC",
        "provider": "kalshi",
        "source_id": "KXBTC",
        "channel": "trade",
        "message_type": "trade",
        "event_subtype": None,
        "sid": 1,
        "seq": None,
        "provider_timestamp": None,
        "schema_version": "market-ingress/v1",
        "payload": "{}",
        "received_timestamp": 5,
    }


def _truth(capture_id: str = "capture-1", category: str = "accepted") -> dict[str, Any]:
    return {
        "policy_version": "data-truth/v1",
        "subject_capture_id": capture_id,
        "category": category,
        "contributing_capture_ids": '["capture-1"]',
        "reason": None,
        "event_provider": None,
        "event_source_id": None,
        "event_message_type": None,
        "event_trade_id": None,
    }


def _availability(
    kind: str, capture_id: str, policy: str | None, identity: str
) -> dict[str, Any]:
    return {
        "kind": kind,
        "capture_id": capture_id,
        "policy_version": policy,
        "available_at_ns": 10,
        "proof_schema_version": "replay-availability-proof/v1",
        "source_authority_identity": identity,
    }


def test_candidate_records_decode_physical_authorities_and_are_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = _Database(evidence=[_evidence()], truth=[_truth()])
    source, _ = _source(monkeypatch, database=database)
    identities = source.source_authorities()
    database.availability.extend(
        [
            _availability("evidence", "capture-1", None, identities.evidence),
            _availability(
                "authority", "capture-1", "data-truth/v1", identities.truth_decision
            ),
        ]
    )

    records = source.candidate_records(_scope())

    assert len(records) == 1
    assert records[0].capture_fact.capture_id == "capture-1"
    assert records[0].truth_decision.category.value == "accepted"
    assert records[0].evidence_availability.available_at_ns == 10
    assert records[0].authority_availability.reference is not None
    assert all(
        "SELECT" in sql or "tables()" in sql or "table_columns" in sql
        for sql, _ in database.queries
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("sid", True),
        ("asset", "not-an-asset"),
        ("seq", True),
        ("received_timestamp", None),
    ],
)
def test_malformed_evidence_has_bounded_error(
    monkeypatch: pytest.MonkeyPatch, field: str, value: Any
) -> None:
    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )

    evidence = _evidence()
    evidence[field] = value
    source, _ = _source(
        monkeypatch, database=_Database(evidence=[evidence], truth=[_truth()])
    )
    with pytest.raises(ReplayAsOfError) as raised:
        source.candidate_records(_scope())
    assert raised.value.code is ReplayErrorCode.MALFORMED_EVIDENCE


@pytest.mark.parametrize(
    "field,value",
    [
        ("category", "unexpected"),
        ("contributing_capture_ids", "{}"),
        ("event_provider", "kalshi"),
    ],
)
def test_malformed_truth_authority_has_bounded_error(
    monkeypatch: pytest.MonkeyPatch, field: str, value: Any
) -> None:
    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )

    truth = _truth()
    truth[field] = value
    source, _ = _source(
        monkeypatch, database=_Database(evidence=[_evidence()], truth=[truth])
    )
    with pytest.raises(ReplayAsOfError) as raised:
        source.candidate_records(_scope())
    assert raised.value.code is ReplayErrorCode.MALFORMED_AUTHORITY


@pytest.mark.parametrize(
    "category", ["accepted", "duplicate", "conflict", "not_accepted"]
)
def test_every_truth_category_decodes(
    monkeypatch: pytest.MonkeyPatch, category: str
) -> None:
    source, _ = _source(
        monkeypatch,
        database=_Database(evidence=[_evidence()], truth=[_truth(category=category)]),
    )

    assert (
        source.candidate_records(_scope())[0].truth_decision.category.value == category
    )


def test_duplicate_truth_subject_is_authority_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )

    source, _ = _source(
        monkeypatch,
        database=_Database(evidence=[_evidence()], truth=[_truth(), _truth()]),
    )
    with pytest.raises(ReplayAsOfError) as raised:
        source.candidate_records(_scope())
    assert raised.value.code is ReplayErrorCode.AUTHORITY_CONFLICT


@pytest.mark.parametrize(
    "field,value",
    [
        ("proof_schema_version", "unknown/v1"),
        ("source_authority_identity", "wrong-authority"),
        ("available_at_ns", True),
    ],
)
def test_malformed_availability_marker_is_bounded_failure(
    monkeypatch: pytest.MonkeyPatch, field: str, value: Any
) -> None:
    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )

    database = _Database(evidence=[_evidence()], truth=[_truth()])
    source, _ = _source(monkeypatch, database=database)
    marker = _availability(
        "evidence", "capture-1", None, source.source_authorities().evidence
    )
    marker[field] = value
    database.availability.append(marker)
    with pytest.raises(ReplayAsOfError) as raised:
        source.candidate_records(_scope())
    assert raised.value.code is ReplayErrorCode.AVAILABILITY_EVIDENCE_MISSING


def test_missing_markers_are_absent_not_synthetic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, _ = _source(
        monkeypatch, database=_Database(evidence=[_evidence()], truth=[_truth()])
    )

    record = source.candidate_records(_scope())[0]

    assert record.evidence_availability.available_at_ns is None
    assert record.evidence_availability.reference is None
    assert record.authority_availability.available_at_ns is None
    assert record.authority_availability.reference is None


def test_missing_or_incompatible_schema_is_source_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )

    database = _Database(
        tables=[
            {
                "table_name": "evidence",
                "designatedTimestamp": "received_timestamp",
                "partitionBy": "DAY",
                "walEnabled": True,
                "dedup": False,
            }
        ]
    )
    source, _ = _source(monkeypatch, database=database)

    with pytest.raises(ReplayAsOfError) as raised:
        source.source_authorities()

    assert raised.value.code is ReplayErrorCode.SOURCE_UNAVAILABLE


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("LIVE15_RUN_REPLAY_SOURCE_QUESTDB_INTEGRATION") != "1",
    reason="set LIVE15_RUN_REPLAY_SOURCE_QUESTDB_INTEGRATION=1 to run task-owned QuestDB",
)
def test_real_task_owned_questdb_source_drives_arrival_replay(tmp_path: Any) -> None:
    """Exercise the adapter only against UUID-named tables in a Job-contained server."""
    import questdb
    from test_questdb_truth_history_integration import _assert_lifecycle, _server

    from live15_quant_v2.data.replay_as_of.models import (
        AsOfRequest,
        ReplayOrdering,
        SelectionAxis,
        SelectionWindow,
    )
    from live15_quant_v2.data.replay_as_of.questdb_source import QuestDBReplaySource
    from live15_quant_v2.data.replay_as_of.service import ReplayAsOf

    suffix = uuid4().hex
    evidence, truth, availability = (
        f"replay_evidence_{suffix}",
        f"replay_truth_{suffix}",
        f"replay_availability_{suffix}",
    )
    with _server(tmp_path) as server:
        assert server.database is not None
        database = server.database
        database.execute(
            f"CREATE TABLE {evidence} (capture_id VARCHAR, asset SYMBOL, provider SYMBOL, source_id VARCHAR, channel SYMBOL, message_type VARCHAR, event_subtype VARCHAR, sid LONG, seq LONG, provider_timestamp TIMESTAMP_NS, schema_version VARCHAR, payload VARCHAR, received_timestamp TIMESTAMP_NS) TIMESTAMP(received_timestamp) PARTITION BY DAY WAL DEDUP UPSERT KEYS(received_timestamp, capture_id)"
        )
        database.execute(
            f"CREATE TABLE {truth} (policy_version VARCHAR, subject_capture_id VARCHAR, category VARCHAR, contributing_capture_ids VARCHAR, reason VARCHAR, event_provider VARCHAR, event_source_id VARCHAR, event_message_type VARCHAR, event_trade_id VARCHAR, physical_written_at TIMESTAMP_NS) TIMESTAMP(physical_written_at) PARTITION BY DAY WAL"
        )
        database.execute(
            f"CREATE TABLE {availability} (kind VARCHAR, capture_id VARCHAR, policy_version VARCHAR, available_at_ns TIMESTAMP_NS, proof_schema_version VARCHAR, source_authority_identity VARCHAR, written_at_ns TIMESTAMP_NS) TIMESTAMP(written_at_ns) PARTITION BY DAY WAL"
        )
        source = QuestDBReplaySource(
            server.connection_string,
            evidence_table=evidence,
            truth_decision_table=truth,
            availability_table=availability,
            evidence_authority_identity="capture-authority/v1",
            truth_decision_authority_identity="truth-authority/v1",
            availability_authority_identity="availability-authority/v1",
        )
        with database.sender() as sender:
            sender.row(
                evidence,
                columns={
                    "capture_id": "capture-1",
                    "asset": "BTC",
                    "provider": "kalshi",
                    "source_id": "KXBTC",
                    "channel": "trade",
                    "message_type": "trade",
                    "event_subtype": None,
                    "sid": 1,
                    "seq": None,
                    "provider_timestamp": None,
                    "schema_version": "market-ingress/v1",
                    "payload": "{}",
                },
                at=questdb.TimestampNanos(5),
            )
            sender.row(
                truth,
                columns={
                    "policy_version": "data-truth/v1",
                    "subject_capture_id": "capture-1",
                    "category": "accepted",
                    "contributing_capture_ids": '["capture-1"]',
                    "reason": None,
                    "event_provider": None,
                    "event_source_id": None,
                    "event_message_type": None,
                    "event_trade_id": None,
                },
                at=questdb.TimestampNanos(6),
            )
            fsn = sender.flush_and_get_fsn()
            assert fsn is not None and sender.await_acked_fsn(
                fsn, timeout_millis=15_000
            )
        assert source.source_authorities().evidence
        identities = source.source_authorities()
        with database.sender() as sender:
            sender.row(
                availability,
                columns={
                    "kind": "evidence",
                    "capture_id": "capture-1",
                    "policy_version": None,
                    "available_at_ns": questdb.TimestampNanos(10),
                    "proof_schema_version": "replay-availability-proof/v1",
                    "source_authority_identity": identities.evidence,
                },
                at=questdb.TimestampNanos(11),
            )
            sender.row(
                availability,
                columns={
                    "kind": "authority",
                    "capture_id": "capture-1",
                    "policy_version": "data-truth/v1",
                    "available_at_ns": questdb.TimestampNanos(10),
                    "proof_schema_version": "replay-availability-proof/v1",
                    "source_authority_identity": identities.truth_decision,
                },
                at=questdb.TimestampNanos(12),
            )
            fsn = sender.flush_and_get_fsn()
            assert fsn is not None and sender.await_acked_fsn(
                fsn, timeout_millis=15_000
            )
        for table in (evidence, truth, availability):
            assert (
                database.query(f"SELECT wait_wal_table('{table}')", [])
                .to_pandas()
                .to_dict(orient="records")[0]
            )
        view = ReplayAsOf(source, max_page_size=10).read(
            AsOfRequest(
                20,
                "data-truth/v1",
                SelectionWindow(SelectionAxis.ARRIVAL_TIME, 0, 20),
                ReplayOrdering.ARRIVAL,
                None,
                None,
                10,
                None,
            )
        )
        assert [record.capture_fact.capture_id for record in view.records] == [
            "capture-1"
        ]
        source.close()
    _assert_lifecycle(server)
