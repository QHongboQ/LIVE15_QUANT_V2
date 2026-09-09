"""Disposable QuestDB persistence for Replay availability markers."""

import math
import re
import time
from typing import Any

import questdb

from live15_quant_v2.data.replay_as_of.availability import (
    AvailabilityKey,
    AvailabilityKind,
    AvailabilityRecord,
    AvailabilitySupportError,
    AvailabilitySupportErrorCode,
)

_TABLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_COLUMNS = {
    "kind": "VARCHAR", "capture_id": "VARCHAR", "policy_version": "VARCHAR",
    "available_at_ns": "TIMESTAMP_NS", "proof_schema_version": "VARCHAR",
    "source_authority_identity": "VARCHAR", "written_at_ns": "TIMESTAMP_NS",
}


class QuestDBAvailabilityStore:
    """Append-only store for one explicitly named, disposable availability table."""

    def __init__(self, connection_string: str, *, table_name: str, acknowledgement_timeout_millis: int) -> None:
        if not _TABLE_NAME.fullmatch(table_name):
            raise ValueError("table_name must be a simple SQL identifier")
        if not isinstance(acknowledgement_timeout_millis, int) or isinstance(acknowledgement_timeout_millis, bool):
            raise TypeError("acknowledgement_timeout_millis must be an int")
        if acknowledgement_timeout_millis < 0:
            raise ValueError("acknowledgement_timeout_millis must be non-negative")
        self._connection_string = connection_string
        self._table_name = table_name
        self._timeout = acknowledgement_timeout_millis
        self._database: questdb.QuestDB | None = None
        self._schema_ready = False
        self._in_doubt: set[AvailabilityKey] = set()

    def close(self) -> None:
        if self._database is not None:
            self._database.close()
            self._database = None
            self._schema_ready = False

    def find(self, key: AvailabilityKey) -> AvailabilityRecord | None:
        policy_sql, binds = ("policy_version IS NULL", [key.kind.value, key.capture_id]) if key.kind is AvailabilityKind.EVIDENCE else ("policy_version = $3", [key.kind.value, key.capture_id, key.policy_version])
        rows = self._rows(f"SELECT kind, capture_id, policy_version, available_at_ns, proof_schema_version, source_authority_identity FROM {self._table_name} WHERE kind = $1 AND capture_id = $2 AND {policy_sql}", binds)
        if not rows:
            return None
        if len(rows) != 1:
            self._conflict("multiple records for semantic key")
        record = self._decode(rows[0])
        if record.key != key:
            self._conflict("stored record has wrong semantic key")
        return record

    def read_committed_floor(self) -> int | None:
        rows = self._rows(f"SELECT kind, capture_id, policy_version, available_at_ns, proof_schema_version, source_authority_identity FROM {self._table_name}", [])
        seen: dict[AvailabilityKey, AvailabilityRecord] = {}
        for row in rows:
            record = self._decode(row)
            if record.key in seen:
                self._conflict("duplicate semantic key")
            seen[record.key] = record
        return max((record.available_at_ns for record in seen.values()), default=None)

    def append(self, record: AvailabilityRecord) -> AvailabilityRecord:
        existing = self.find(record.key)
        if existing is not None:
            if existing != record:
                self._conflict("immutable record conflict")
            return existing
        if record.key in self._in_doubt:
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "append remains unresolved")
        sender: Any | None = None
        try:
            database = self._database_for_use()
            sender = database.sender()
            database_dropped = database.error_events_dropped
            sender_dropped = sender.error_events_dropped()
            sender.row(self._table_name, columns=self._fields(record), at=questdb.TimestampNanos(time.time_ns()))
            fsn = sender.flush_and_get_fsn()
        except (OSError, questdb.QuestDBError) as error:
            self._close_sender(sender)
            self._raise_prepublication(error)
        if fsn is None:
            self._close_sender(sender)
            self._in_doubt.add(record.key)
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "append has no FSN")
        assert sender is not None
        try:
            acknowledged = sender.await_acked_fsn(fsn, timeout_millis=self._timeout)
            pending = any(True for error in _sender_errors(sender) if error.from_fsn <= fsn <= error.to_fsn)
            lost = sender.error_events_dropped() != sender_dropped or database.error_events_dropped != database_dropped
        except (OSError, questdb.QuestDBError) as error:
            self._close_sender(sender); self._in_doubt.add(record.key)
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "acknowledgement is in doubt") from error
        self._close_sender(sender)
        if lost or pending or not acknowledged:
            self._in_doubt.add(record.key)
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "append acknowledgement is in doubt")
        try:
            self._wait_visibility(database)
            verified = self.find(record.key)
        except AvailabilitySupportError:
            self._in_doubt.add(record.key)
            raise
        if verified != record:
            self._in_doubt.add(record.key)
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "append was not exactly visible")
        return verified

    def _database_for_use(self) -> questdb.QuestDB:
        if self._database is None:
            self._database = questdb.connect(self._connection_string, auto_flush=False)
        if not self._schema_ready:
            if not self._table_exists():
                self._database.execute(self._create_sql())
            self._verify_schema()
            self._schema_ready = True
        return self._database

    def _table_exists(self) -> bool:
        return any(row.get("table_name") == self._table_name for row in self._metadata("SELECT table_name, designatedTimestamp, partitionBy, walEnabled, dedup FROM tables()"))

    def _verify_schema(self) -> None:
        tables = [row for row in self._metadata("SELECT table_name, designatedTimestamp, partitionBy, walEnabled, dedup FROM tables()") if row.get("table_name") == self._table_name]
        if len(tables) != 1 or tables[0].get("walEnabled") is not True or tables[0].get("dedup") is not False or tables[0].get("partitionBy") != "DAY" or tables[0].get("designatedTimestamp") != "written_at_ns":
            self._source("incompatible availability schema")
        columns = {row.get("column"): row for row in self._metadata(f"SELECT \"column\", type, designated, upsertKey FROM table_columns('{self._table_name}')")}
        if any(columns.get(name, {}).get("type") != kind for name, kind in _COLUMNS.items()) or columns.get("written_at_ns", {}).get("designated") is not True or any(row.get("upsertKey") is True for row in columns.values()):
            self._source("incompatible availability columns")

    def _rows(self, sql: str, binds: list[Any]) -> list[dict[str, Any]]:
        try:
            return self._database_for_use().query(sql, binds).to_pandas().to_dict(orient="records")
        except (OSError, questdb.QuestDBError) as error:
            self._source("availability read failed", error)
        raise AssertionError("unreachable")

    def _metadata(self, sql: str) -> list[dict[str, Any]]:
        database = self._database
        if database is None:
            self._source("availability database unavailable")
        assert database is not None
        return database.query(sql, []).to_pandas().to_dict(orient="records")

    @staticmethod
    def _fields(record: AvailabilityRecord) -> dict[str, Any]:
        return {"kind": record.kind.value, "capture_id": record.capture_id, "policy_version": record.policy_version, "available_at_ns": record.available_at_ns, "proof_schema_version": record.proof_schema_version, "source_authority_identity": record.source_authority_identity}

    @staticmethod
    def _decode(row: dict[str, Any]) -> AvailabilityRecord:
        try:
            timestamp = row["available_at_ns"]
            value = timestamp if isinstance(timestamp, int) else getattr(timestamp, "value", None)
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError("stored available_at_ns is not an integer")
            policy = row["policy_version"]
            if isinstance(policy, float) and math.isnan(policy):
                policy = None
            return AvailabilityRecord(AvailabilityKind(row["kind"]), row["capture_id"], policy, value, row["proof_schema_version"], row["source_authority_identity"])
        except (KeyError, TypeError, ValueError) as error:
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.INVARIANT_CONFLICT, "malformed availability row") from error

    def _wait_visibility(self, database: questdb.QuestDB) -> None:
        rows = database.query(f"SELECT wait_wal_table('{self._table_name}')", []).to_pandas().to_dict(orient="records")
        if len(rows) != 1 or len(rows[0]) != 1 or next(iter(rows[0].values())) is not True:
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "WAL visibility unavailable")

    def _create_sql(self) -> str:
        return f"CREATE TABLE {self._table_name} (kind VARCHAR, capture_id VARCHAR, policy_version VARCHAR, available_at_ns TIMESTAMP_NS, proof_schema_version VARCHAR, source_authority_identity VARCHAR, written_at_ns TIMESTAMP_NS) TIMESTAMP(written_at_ns) PARTITION BY DAY WAL"

    @staticmethod
    def _close_sender(sender: Any | None) -> None:
        if sender is not None: sender.close(flush=False)

    def _raise_prepublication(self, error: BaseException) -> None:
        code = AvailabilitySupportErrorCode.IN_DOUBT if getattr(error, "in_doubt", False) else AvailabilitySupportErrorCode.DEFINITE_PREPUBLICATION_FAILURE
        raise AvailabilitySupportError(code, "QuestDB append failed before publication") from error

    def _conflict(self, message: str) -> None:
        raise AvailabilitySupportError(AvailabilitySupportErrorCode.INVARIANT_CONFLICT, message)

    def _source(self, message: str, error: BaseException | None = None) -> None:
        exception = AvailabilitySupportError(AvailabilitySupportErrorCode.SOURCE_UNAVAILABLE, message)
        if error is None: raise exception
        raise exception from error


def _sender_errors(sender: Any):
    while (error := sender.poll_error()) is not None:
        yield error
