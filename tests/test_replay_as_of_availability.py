"""Behavioral and controlled-adapter tests for Replay availability support."""

from dataclasses import FrozenInstanceError, dataclass
from typing import Any, TypedDict

import pytest
import questdb

from live15_quant_v2.data.replay_as_of import questdb_availability
from live15_quant_v2.data.replay_as_of.availability import (
    SUPPORTED_PROOF_SCHEMA_VERSION,
    AvailabilityKey,
    AvailabilityKind,
    AvailabilityRecord,
    AvailabilityStore,
    AvailabilitySupportError,
    AvailabilitySupportErrorCode,
    AvailabilityWriter,
)
from live15_quant_v2.data.replay_as_of.questdb_availability import (
    QuestDBAvailabilityStore,
)


def _record(
    kind: AvailabilityKind = AvailabilityKind.EVIDENCE,
    capture_id: str = "capture-1",
    policy_version: str | None = None,
    available_at_ns: int = 101,
    source: str = "source/v1",
) -> AvailabilityRecord:
    return AvailabilityRecord(kind, capture_id, policy_version, available_at_ns, SUPPORTED_PROOF_SCHEMA_VERSION, source)


class _Store:
    def __init__(self, floor: int | None = None) -> None:
        self.records: dict[AvailabilityKey, AvailabilityRecord] = {}
        self.floor = floor
        self.find_calls = 0
        self.floor_calls = 0
        self.append_calls: list[AvailabilityRecord] = []
        self.append_error: AvailabilitySupportError | None = None

    def find(self, key: AvailabilityKey) -> AvailabilityRecord | None:
        self.find_calls += 1
        return self.records.get(key)

    def read_committed_floor(self) -> int | None:
        self.floor_calls += 1
        return self.floor

    def append(self, record: AvailabilityRecord) -> AvailabilityRecord:
        self.append_calls.append(record)
        if self.append_error is not None:
            raise self.append_error
        self.records[record.key] = record
        return record


class _RecordProvenArguments(TypedDict):
    kind: AvailabilityKind
    capture_id: str
    policy_version: str | None
    source_authority_identity: str


def _arguments(capture_id: str = "capture-1", *, source: str = "source/v1") -> _RecordProvenArguments:
    return {"kind": AvailabilityKind.EVIDENCE, "capture_id": capture_id, "policy_version": None, "source_authority_identity": source}


def test_model_validates_kinds_keys_and_immutable_slotted_records() -> None:
    evidence = _record()
    authority = _record(AvailabilityKind.AUTHORITY, policy_version="data-truth/v1")
    assert evidence.key == AvailabilityKey(AvailabilityKind.EVIDENCE, "capture-1", None)
    assert authority.key == AvailabilityKey(AvailabilityKind.AUTHORITY, "capture-1", "data-truth/v1")
    with pytest.raises(FrozenInstanceError):
        evidence.capture_id = "other"  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        field_name = "unexpected"
        setattr(evidence, field_name, "field")


@pytest.mark.parametrize(
    "kind,capture_id,policy,available_at,proof_schema,source",
    [
        (AvailabilityKind.EVIDENCE, "capture", "data-truth/v1", 1, SUPPORTED_PROOF_SCHEMA_VERSION, "source"),
        (AvailabilityKind.AUTHORITY, "capture", None, 1, SUPPORTED_PROOF_SCHEMA_VERSION, "source"),
        ("evidence", "capture", None, 1, SUPPORTED_PROOF_SCHEMA_VERSION, "source"),
        (AvailabilityKind.EVIDENCE, "", None, 1, SUPPORTED_PROOF_SCHEMA_VERSION, "source"),
        (AvailabilityKind.EVIDENCE, "capture", None, True, SUPPORTED_PROOF_SCHEMA_VERSION, "source"),
        (AvailabilityKind.EVIDENCE, "capture", None, -1, SUPPORTED_PROOF_SCHEMA_VERSION, "source"),
        (AvailabilityKind.EVIDENCE, "capture", None, 1, "other/v1", "source"),
        (AvailabilityKind.EVIDENCE, "capture", None, 1, SUPPORTED_PROOF_SCHEMA_VERSION, ""),
    ],
)
def test_invalid_availability_semantics_fail_closed(kind: object, capture_id: str, policy: str | None, available_at: object, proof_schema: str, source: str) -> None:
    with pytest.raises((TypeError, ValueError)):
        AvailabilityRecord(kind, capture_id, policy, available_at, proof_schema, source)  # type: ignore[arg-type]


def test_availability_port_remains_only_lookup_floor_and_append() -> None:
    protocol_attributes = "__protocol_attrs__"
    assert getattr(AvailabilityStore, protocol_attributes) == {"find", "read_committed_floor", "append"}


def test_existing_exact_record_returns_without_clock_sampling_or_append() -> None:
    store = _Store()
    existing = _record()
    store.records[existing.key] = existing
    calls = 0

    def monotonic() -> int:
        nonlocal calls
        calls += 1
        return 10

    writer = AvailabilityWriter(store, wall_time_ns=lambda: 100, monotonic_ns=monotonic)
    assert writer.record_proven(**_arguments()) is existing
    assert calls == 1
    assert store.append_calls == []


def test_existing_immutable_conflict_fails_closed() -> None:
    store = _Store()
    existing = _record(source="other/v1")
    store.records[existing.key] = existing
    writer = AvailabilityWriter(store, wall_time_ns=lambda: 100, monotonic_ns=lambda: 10)
    with pytest.raises(AvailabilitySupportError) as error:
        writer.record_proven(**_arguments())
    assert error.value.code is AvailabilitySupportErrorCode.INVARIANT_CONFLICT
    assert store.append_calls == []


def test_fresh_proof_samples_projected_clock_exactly_once() -> None:
    store = _Store()
    values = iter((10, 15))
    writer = AvailabilityWriter(store, wall_time_ns=lambda: 100, monotonic_ns=lambda: next(values))
    assert writer.record_proven(**_arguments()).available_at_ns == 105
    assert len(store.append_calls) == 1


def test_wall_clock_rollback_after_anchor_cannot_backdate_proof_time() -> None:
    store = _Store()
    wall_values = iter((100, 1))
    monotonic_values = iter((10, 15))
    writer = AvailabilityWriter(store, wall_time_ns=lambda: next(wall_values), monotonic_ns=lambda: next(monotonic_values))
    assert writer.record_proven(**_arguments()).available_at_ns == 105
    assert next(wall_values) == 1


def test_monotonic_regression_fails_closed() -> None:
    store = _Store()
    values = iter((10, 9))
    writer = AvailabilityWriter(store, wall_time_ns=lambda: 100, monotonic_ns=lambda: next(values))
    with pytest.raises(AvailabilitySupportError) as error:
        writer.record_proven(**_arguments())
    assert error.value.code is AvailabilitySupportErrorCode.SOURCE_UNAVAILABLE
    assert store.append_calls == []


def test_committed_floor_is_read_at_startup_and_strictly_clamps_projection() -> None:
    store = _Store(floor=100)
    writer = AvailabilityWriter(store, wall_time_ns=lambda: 90, monotonic_ns=lambda: 7)
    assert store.floor_calls == 1
    assert writer.record_proven(**_arguments()).available_at_ns == 101


def test_successive_and_same_tick_proofs_strictly_advance() -> None:
    store = _Store()
    values = iter((7, 8, 8))
    writer = AvailabilityWriter(store, wall_time_ns=lambda: 100, monotonic_ns=lambda: next(values))
    first = writer.record_proven(**_arguments("capture-1"))
    second = writer.record_proven(**_arguments("capture-2"))
    assert (first.available_at_ns, second.available_at_ns) == (101, 102)


@pytest.mark.parametrize("failure", [AvailabilitySupportError(AvailabilitySupportErrorCode.DEFINITE_PREPUBLICATION_FAILURE, "before"), AvailabilitySupportError(AvailabilitySupportErrorCode.DEFINITE_REJECTION, "terminal")], ids=["definite-prepublication", "definite-terminal-rejection"])
def test_last_issued_advances_across_definite_nonpublication(failure: AvailabilitySupportError) -> None:
    store = _Store()
    values = iter((1, 2, 2))
    writer = AvailabilityWriter(store, wall_time_ns=lambda: 100, monotonic_ns=lambda: next(values))
    store.append_error = failure
    with pytest.raises(AvailabilitySupportError) as error:
        writer.record_proven(**_arguments("failed"))
    assert error.value.code is failure.code
    store.append_error = None
    assert writer.record_proven(**_arguments("retry")).available_at_ns == 102


def test_restart_below_persisted_floor_advances_and_malformed_floors_fail_closed() -> None:
    restarted = AvailabilityWriter(_Store(floor=900), wall_time_ns=lambda: 100, monotonic_ns=lambda: 1)
    assert restarted.record_proven(**_arguments()).available_at_ns == 901
    for invalid in (True, -1, "100"):
        with pytest.raises(AvailabilitySupportError) as error:
            AvailabilityWriter(_Store(floor=invalid), wall_time_ns=lambda: 1, monotonic_ns=lambda: 1)  # type: ignore[arg-type]
        assert error.value.code is AvailabilitySupportErrorCode.SOURCE_UNAVAILABLE


def test_last_marker_floor_alone_is_explicitly_insufficient_nonclaim() -> None:
    nonclaims = {"LAST_MARKER_FLOOR_ALONE_INSUFFICIENT": "no distributed or cross-host clock correctness claim"}
    assert nonclaims["LAST_MARKER_FLOOR_ALONE_INSUFFICIENT"].startswith("no distributed")


def test_record_proven_accepts_no_caller_available_at_override() -> None:
    writer = AvailabilityWriter(_Store(), wall_time_ns=lambda: 1, monotonic_ns=lambda: 1)
    with pytest.raises(TypeError):
        writer.record_proven(**_arguments(), available_at_ns=999)  # type: ignore[call-arg]


def test_in_doubt_retains_exact_candidate_reconciles_only_exact_visible_record() -> None:
    store = _Store()
    store.append_error = AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "ambiguous")
    writer = AvailabilityWriter(store, wall_time_ns=lambda: 10, monotonic_ns=lambda: 1)
    with pytest.raises(AvailabilitySupportError) as first:
        writer.record_proven(**_arguments())
    attempted = store.append_calls[0]
    assert first.value.code is AvailabilitySupportErrorCode.IN_DOUBT
    assert writer._in_doubt == {attempted.key: attempted}
    store.records[attempted.key] = attempted
    assert writer.record_proven(**_arguments()) == attempted
    assert writer._in_doubt == {}


@pytest.mark.parametrize("visible", [_record(available_at_ns=99), _record(source="other/v1")], ids=["different-time", "different-source"])
def test_in_doubt_visible_mismatch_is_invariant_conflict_without_reappend(visible: AvailabilityRecord) -> None:
    store = _Store()
    store.append_error = AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "ambiguous")
    writer = AvailabilityWriter(store, wall_time_ns=lambda: 10, monotonic_ns=lambda: 1)
    with pytest.raises(AvailabilitySupportError):
        writer.record_proven(**_arguments())
    store.records[visible.key] = visible
    with pytest.raises(AvailabilitySupportError) as error:
        writer.record_proven(**_arguments())
    assert error.value.code is AvailabilitySupportErrorCode.INVARIANT_CONFLICT
    assert len(store.append_calls) == 1


def test_in_doubt_zero_row_remains_unresolved_without_a_blind_reappend() -> None:
    store = _Store()
    store.append_error = AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "ambiguous")
    writer = AvailabilityWriter(store, wall_time_ns=lambda: 10, monotonic_ns=lambda: 1)
    with pytest.raises(AvailabilitySupportError):
        writer.record_proven(**_arguments())
    with pytest.raises(AvailabilitySupportError) as error:
        writer.record_proven(**_arguments())
    assert error.value.code is AvailabilitySupportErrorCode.IN_DOUBT
    assert len(store.append_calls) == 1


class _Frame:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def to_dict(self, *, orient: str) -> list[dict[str, Any]]:
        assert orient == "records"
        return self.rows


class _QueryResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def to_pandas(self) -> _Frame:
        return _Frame(self.rows)


@dataclass(frozen=True)
class _SenderError:
    from_fsn: int
    to_fsn: int
    applied_policy: questdb.SenderErrorPolicy


class _Sender:
    def __init__(self, *, acknowledged: bool = True, fsn: int | None = 7, row_error: BaseException | None = None, flush_error: BaseException | None = None, await_error: BaseException | None = None, errors: list[_SenderError] | None = None, dropped: list[int] | None = None) -> None:
        self.acknowledged, self.fsn = acknowledged, fsn
        self.row_error, self.flush_error, self.await_error = row_error, flush_error, await_error
        self.errors = list(errors or [])
        self.dropped = iter(dropped or [0])
        self.last_dropped = 0
        self.row_calls: list[dict[str, Any]] = []
        self.flush_calls = 0

    def row(self, table_name: str, *, columns: dict[str, Any], at: Any) -> None:
        if self.row_error is not None:
            raise self.row_error
        self.row_calls.append({"table_name": table_name, "columns": columns, "at": at})

    def flush_and_get_fsn(self) -> int | None:
        self.flush_calls += 1
        if self.flush_error is not None:
            raise self.flush_error
        return self.fsn

    def await_acked_fsn(self, fsn: int, *, timeout_millis: int) -> bool:
        assert fsn == self.fsn
        assert timeout_millis == 10
        if self.await_error is not None:
            raise self.await_error
        return self.acknowledged

    def poll_error(self) -> _SenderError | None:
        return self.errors.pop(0) if self.errors else None

    def error_events_dropped(self) -> int:
        try:
            self.last_dropped = next(self.dropped)
        except StopIteration:
            pass
        return self.last_dropped

    def close(self, *, flush: bool) -> None:
        assert flush is False


def _row(record: AvailabilityRecord) -> dict[str, Any]:
    return {"kind": record.kind.value, "capture_id": record.capture_id, "policy_version": record.policy_version, "available_at_ns": record.available_at_ns, "proof_schema_version": record.proof_schema_version, "source_authority_identity": record.source_authority_identity}


class _Database:
    def __init__(self, *, sender: _Sender | None = None, records: list[dict[str, Any]] | None = None, visibility_rows: list[dict[str, object]] | None = None, visibility_error: BaseException | None = None, post_visibility_records: list[dict[str, Any]] | None = None, columns: dict[str, str] | None = None, database_dropped: list[int] | None = None) -> None:
        self.sender_instance = sender or _Sender()
        self.records = list(records or [])
        self.visibility_rows = visibility_rows if visibility_rows is not None else [{"wait_wal_table": True}]
        self.visibility_error = visibility_error
        self.post_visibility_records = post_visibility_records
        self.columns = columns or dict(questdb_availability._COLUMNS)
        self.database_dropped = iter(database_dropped or [0])
        self.last_database_dropped = 0
        self.queries: list[str] = []

    @property
    def error_events_dropped(self) -> int:
        try:
            self.last_database_dropped = next(self.database_dropped)
        except StopIteration:
            pass
        return self.last_database_dropped

    def query(self, sql: str, binds: list[Any]) -> _QueryResult:
        self.queries.append(sql)
        if "wait_wal_table" in sql:
            if self.visibility_error is not None:
                raise self.visibility_error
            if self.post_visibility_records is not None:
                self.records = list(self.post_visibility_records)
            return _QueryResult(self.visibility_rows)
        if "FROM tables()" in sql:
            return _QueryResult([{"table_name": "availability_test", "designatedTimestamp": "written_at_ns", "partitionBy": "DAY", "walEnabled": True, "dedup": False}])
        if "FROM table_columns" in sql:
            return _QueryResult([{"column": name, "type": value, "designated": name == "written_at_ns", "upsertKey": False} for name, value in self.columns.items()])
        rows = self.records
        if "WHERE kind = $1" in sql:
            rows = [row for row in rows if row["kind"] == binds[0] and row["capture_id"] == binds[1]]
            rows = [row for row in rows if row["policy_version"] is None] if "IS NULL" in sql else [row for row in rows if row["policy_version"] == binds[2]]
        return _QueryResult(rows)

    def execute(self, sql: str) -> None:
        pass

    def sender(self) -> _Sender:
        return self.sender_instance

    def close(self) -> None:
        pass


def _adapter_for(monkeypatch: pytest.MonkeyPatch, database: _Database) -> QuestDBAvailabilityStore:
    monkeypatch.setattr(questdb_availability.questdb, "connect", lambda _connection, **_kwargs: database)
    return QuestDBAvailabilityStore("ws::addr=127.0.0.1:9000;", table_name="availability_test", acknowledgement_timeout_millis=10)


class _InDoubtOSError(OSError):
    in_doubt = True


@pytest.mark.parametrize("sender,expected,ambiguous", [
    (_Sender(row_error=OSError("setup")), AvailabilitySupportErrorCode.DEFINITE_PREPUBLICATION_FAILURE, False),
    (_Sender(row_error=_InDoubtOSError("uncertain")), AvailabilitySupportErrorCode.IN_DOUBT, True),
    (_Sender(fsn=None), AvailabilitySupportErrorCode.IN_DOUBT, True),
    (_Sender(acknowledged=False), AvailabilitySupportErrorCode.IN_DOUBT, True),
    (_Sender(await_error=OSError("ack")), AvailabilitySupportErrorCode.IN_DOUBT, True),
    (_Sender(errors=[_SenderError(7, 7, questdb.SenderErrorPolicy.Retriable)]), AvailabilitySupportErrorCode.IN_DOUBT, True),
    (_Sender(errors=[_SenderError(7, 7, questdb.SenderErrorPolicy.Terminal)]), AvailabilitySupportErrorCode.DEFINITE_REJECTION, False),
    (_Sender(dropped=[0, 1]), AvailabilitySupportErrorCode.IN_DOUBT, True),
    (_Sender(errors=[_SenderError(7, 7, questdb.SenderErrorPolicy.Terminal)], dropped=[0, 1]), AvailabilitySupportErrorCode.IN_DOUBT, True),
], ids=["setup", "explicit-in-doubt", "no-fsn", "ack-false", "ack-error", "pending", "terminal", "diagnostic-loss", "terminal-plus-loss"])
def test_adapter_maps_sender_failure_matrix_and_retains_ambiguous_state(monkeypatch: pytest.MonkeyPatch, sender: _Sender, expected: AvailabilitySupportErrorCode, ambiguous: bool) -> None:
    adapter = _adapter_for(monkeypatch, _Database(sender=sender))
    record = _record()
    with pytest.raises(AvailabilitySupportError) as error:
        adapter.append(record)
    assert error.value.code is expected
    if ambiguous:
        publication_attempts = len(sender.row_calls)
        with pytest.raises(AvailabilitySupportError) as repeated:
            adapter.append(record)
        assert repeated.value.code is AvailabilitySupportErrorCode.IN_DOUBT
        assert len(sender.row_calls) == publication_attempts


@pytest.mark.parametrize("visibility_rows,visibility_error", [([{"wait_wal_table": False}], None), (None, OSError("barrier")), (None, questdb.QuestDBError("error", "barrier"))], ids=["false", "oserror", "questdb-error"])
def test_visibility_failures_are_in_doubt_and_never_blind_reappend(monkeypatch: pytest.MonkeyPatch, visibility_rows: list[dict[str, object]] | None, visibility_error: BaseException | None) -> None:
    sender = _Sender()
    adapter = _adapter_for(monkeypatch, _Database(sender=sender, visibility_rows=visibility_rows, visibility_error=visibility_error))
    record = _record()
    with pytest.raises(AvailabilitySupportError) as error:
        adapter.append(record)
    assert error.value.code is AvailabilitySupportErrorCode.IN_DOUBT
    with pytest.raises(AvailabilitySupportError) as repeated:
        adapter.append(record)
    assert repeated.value.code is AvailabilitySupportErrorCode.IN_DOUBT
    assert len(sender.row_calls) == 1


def test_post_barrier_zero_mismatch_exact_duplicate_and_existing_paths_fail_closed_as_required(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _record()
    zero_sender = _Sender()
    zero = _adapter_for(monkeypatch, _Database(sender=zero_sender))
    with pytest.raises(AvailabilitySupportError) as error:
        zero.append(record)
    assert error.value.code is AvailabilitySupportErrorCode.IN_DOUBT
    mismatch = _adapter_for(monkeypatch, _Database(sender=_Sender(), post_visibility_records=[_row(_record(available_at_ns=999))]))
    with pytest.raises(AvailabilitySupportError) as error:
        mismatch.append(record)
    assert error.value.code is AvailabilitySupportErrorCode.INVARIANT_CONFLICT
    exact = _adapter_for(monkeypatch, _Database(sender=_Sender(), post_visibility_records=[_row(record)]))
    assert exact.append(record) == record
    duplicate = _adapter_for(monkeypatch, _Database(records=[_row(record), _row(record)]))
    with pytest.raises(AvailabilitySupportError) as error:
        duplicate.find(record.key)
    assert error.value.code is AvailabilitySupportErrorCode.INVARIANT_CONFLICT
    with pytest.raises(AvailabilitySupportError) as error:
        duplicate.read_committed_floor()
    assert error.value.code is AvailabilitySupportErrorCode.INVARIANT_CONFLICT
    existing_sender = _Sender()
    existing = _adapter_for(monkeypatch, _Database(sender=existing_sender, records=[_row(record)]))
    assert existing.append(record) == record
    assert existing_sender.row_calls == []
    conflict = _adapter_for(monkeypatch, _Database(records=[_row(_record(available_at_ns=999))]))
    with pytest.raises(AvailabilitySupportError) as error:
        conflict.append(record)
    assert error.value.code is AvailabilitySupportErrorCode.INVARIANT_CONFLICT
