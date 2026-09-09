"""Unit tests for the explicit QuestDB TruthDecision-history adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest
import questdb

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.data_truth import (
    EventIdentity,
    TradeNotAcceptedReason,
    TruthDecision,
    TruthDecisionAppendInDoubtError,
    TruthDecisionAppendRejectedError,
    TruthDecisionCategory,
    TruthDecisionInvariantError,
    TruthDecisionVerificationError,
)
from live15_quant_v2.data.data_truth.questdb_history import QuestDBTruthDecisionHistory
from live15_quant_v2.data.storage.capture import CaptureFact


class _Frame:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def to_dict(self, *, orient: str) -> list[dict[str, Any]]:
        assert orient == "records"
        return self._rows


class _QueryResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def to_pandas(self) -> _Frame:
        return _Frame(self._rows)


class _Sender:
    def __init__(
        self,
        *,
        acknowledged: bool = True,
        fsn: int | None = 7,
        row_error: BaseException | None = None,
        flush_error: BaseException | None = None,
        await_error: BaseException | None = None,
        errors: list[_SenderError] | None = None,
        dropped: list[int] | None = None,
    ) -> None:
        self.acknowledged = acknowledged
        self.fsn = fsn
        self.row_error = row_error
        self.flush_error = flush_error
        self.await_error = await_error
        self.errors = list(errors or [])
        self._dropped = iter(dropped or [0])
        self._last_dropped = 0
        self.row_calls: list[dict[str, Any]] = []
        self.flush_calls = 0
        self.closed = False

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
            self._last_dropped = next(self._dropped)
        except StopIteration:
            pass
        return self._last_dropped

    def close(self, *, flush: bool) -> None:
        assert flush is False
        self.closed = True


@dataclass(frozen=True)
class _SenderError:
    from_fsn: int
    to_fsn: int
    applied_policy: questdb.SenderErrorPolicy


class _Database:
    def __init__(
        self,
        *,
        sender: _Sender | None = None,
        rows: list[dict[str, Any]] | None = None,
        table_exists: bool = True,
        columns: dict[str, str] | None = None,
        dedup: bool = False,
        database_dropped: list[int] | None = None,
        visibility_rows: list[dict[str, object]] | None = None,
        visibility_error: BaseException | None = None,
    ) -> None:
        self.rows = list(rows or [])
        self._sender = sender or _Sender()
        self.table_exists = table_exists
        self.columns = columns or _column_types()
        self.dedup = dedup
        self.executed: list[str] = []
        self._database_dropped = iter(database_dropped or [0])
        self._last_database_dropped = 0
        self.visibility_rows = (
            [{"wait_wal_table": True}] if visibility_rows is None else visibility_rows
        )
        self.visibility_error = visibility_error
        self.wait_wal_table_calls: list[str] = []
        self.queries: list[str] = []
        self.closed = False

    @property
    def error_events_dropped(self) -> int:
        try:
            self._last_database_dropped = next(self._database_dropped)
        except StopIteration:
            pass
        return self._last_database_dropped

    def query(self, sql: str, binds: list[Any]) -> _QueryResult:
        self.queries.append(sql)
        if "wait_wal_table" in sql:
            self.wait_wal_table_calls.append(sql)
            if self.visibility_error is not None:
                raise self.visibility_error
            return _QueryResult(self.visibility_rows)
        if "FROM tables()" in sql:
            return _QueryResult([] if not self.table_exists else [
                    {
                        "table_name": "truth_history_test",
                        "designatedTimestamp": "physical_written_at",
                        "partitionBy": "DAY",
                        "walEnabled": True,
                        "dedup": self.dedup,
                    }
                ])
        if "FROM table_columns" in sql:
            return _QueryResult(
                [
                    {
                        "column": name,
                        "type": column_type,
                        "designated": name == "physical_written_at",
                        "upsertKey": False,
                    }
                    for name, column_type in self.columns.items()
                ]
            )
        rows = self.rows
        if "subject_capture_id = $2" in sql:
            rows = [row for row in rows if (row.get("policy_version"), row.get("subject_capture_id")) == tuple(binds)]
        elif "event_trade_id = $5" in sql:
            rows = [
                row for row in rows
                if (row.get("category"), row.get("event_provider"), row.get("event_source_id"), row.get("event_message_type"), row.get("event_trade_id")) == tuple(binds)
            ]
        return _QueryResult(rows)

    def execute(self, sql: str) -> None:
        self.executed.append(sql)
        self.table_exists = True

    def sender(self) -> _Sender:
        return self._sender

    def close(self) -> None:
        self.closed = True


class _HotStore:
    max_batch_rows = 1

    def __init__(self, fact: CaptureFact | None = None, error: BaseException | None = None) -> None:
        self.fact = fact
        self.error = error

    def read_capture(self, capture_id: str) -> CaptureFact | None:
        if self.error is not None:
            raise self.error
        return self.fact


def _column_types() -> dict[str, str]:
    return {
        "policy_version": "VARCHAR", "subject_capture_id": "VARCHAR", "category": "VARCHAR",
        "contributing_capture_ids": "VARCHAR", "reason": "VARCHAR", "event_provider": "VARCHAR",
        "event_source_id": "VARCHAR", "event_message_type": "VARCHAR", "event_trade_id": "VARCHAR",
        "physical_written_at": "TIMESTAMP_NS",
    }


def _decision(*, event: bool = True, subject: str = "capture-1") -> TruthDecision:
    identity = EventIdentity("kalshi", "KXBTC", "trade", "trade-1") if event else None
    return TruthDecision(subject, TruthDecisionCategory.ACCEPTED, "data-truth/v1", (subject, "evidence-1"), None, identity)


def _row(decision: TruthDecision) -> dict[str, Any]:
    event = decision.event_identity
    return {
        "policy_version": decision.policy_version, "subject_capture_id": decision.subject_capture_id,
        "category": decision.category.value, "contributing_capture_ids": json.dumps(decision.contributing_capture_ids, separators=(",", ":")),
        "reason": None if decision.reason is None else decision.reason.value,
        "event_provider": None if event is None else event.provider, "event_source_id": None if event is None else event.source_id,
        "event_message_type": None if event is None else event.message_type, "event_trade_id": None if event is None else event.trade_id,
    }


def _capture(capture_id: str = "capture-1") -> CaptureFact:
    return CaptureFact(capture_id, AssetId.BTC, "kalshi", "KXBTC", "trade", "trade", None, 1, None, None, 2, "market-ingress/v1", "{}")


def _history_for(monkeypatch: pytest.MonkeyPatch, database: _Database, hot_store: _HotStore | None = None) -> QuestDBTruthDecisionHistory:
    from live15_quant_v2.data.data_truth import questdb_history
    monkeypatch.setattr(questdb_history.questdb, "connect", lambda _: database)
    return QuestDBTruthDecisionHistory("ws::addr=127.0.0.1:9000;", table_name="truth_history_test", hot_store=hot_store or _HotStore(), acknowledgement_timeout_millis=10)


@pytest.fixture
def history(monkeypatch: pytest.MonkeyPatch) -> QuestDBTruthDecisionHistory:
    return _history_for(monkeypatch, _Database())


def test_subject_lookup_returns_none_when_authority_is_absent(
    history: QuestDBTruthDecisionHistory,
) -> None:
    assert history.find_subject_decision("data-truth/v1", "missing") is None


def test_subject_lookup_decodes_the_exact_stored_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    decision = _decision()
    history = _history_for(monkeypatch, _Database(rows=[_row(decision)]))

    assert history.find_subject_decision("data-truth/v1", "capture-1") == decision


def test_subject_lookup_fails_closed_for_multiple_authority_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    decision = _decision()
    history = _history_for(monkeypatch, _Database(rows=[_row(decision), _row(decision)]))

    with pytest.raises(TruthDecisionInvariantError, match="multiple"):
        history.find_subject_decision("data-truth/v1", "capture-1")


@pytest.mark.parametrize("field,value", [("category", "other"), ("contributing_capture_ids", "{}")])
def test_subject_lookup_fails_closed_for_malformed_authority_rows(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    row = _row(_decision())
    row[field] = value
    history = _history_for(monkeypatch, _Database(rows=[row]))

    with pytest.raises(TruthDecisionInvariantError, match="malformed"):
        history.find_subject_decision("data-truth/v1", "capture-1")


def test_accepted_event_lookup_returns_anchor_with_hot_store_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    decision = _decision()
    history = _history_for(monkeypatch, _Database(rows=[_row(decision)]), _HotStore(_capture()))

    assert history.find_accepted_event(decision.event_identity) is not None
    assert history.find_accepted_event(decision.event_identity).accepted_decision == decision


def test_accepted_event_lookup_returns_none_when_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    history = _history_for(monkeypatch, _Database())

    assert history.find_accepted_event(_decision().event_identity) is None


def test_accepted_event_lookup_fails_closed_for_multiple_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    decision = _decision()
    history = _history_for(
        monkeypatch, _Database(rows=[_row(decision), _row(decision)]), _HotStore(_capture())
    )

    with pytest.raises(TruthDecisionInvariantError, match="multiple"):
        history.find_accepted_event(decision.event_identity)


def test_accepted_event_lookup_fails_closed_for_malformed_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    row = _row(_decision())
    row["contributing_capture_ids"] = "not-json"
    history = _history_for(monkeypatch, _Database(rows=[row]), _HotStore(_capture()))

    with pytest.raises(TruthDecisionInvariantError, match="malformed"):
        history.find_accepted_event(_decision().event_identity)


@pytest.mark.parametrize("hot_store", [_HotStore(), _HotStore(error=RuntimeError("offline"))])
def test_accepted_event_lookup_maps_missing_or_unavailable_evidence(
    monkeypatch: pytest.MonkeyPatch, hot_store: _HotStore
) -> None:
    decision = _decision()
    history = _history_for(monkeypatch, _Database(rows=[_row(decision)]), hot_store)

    with pytest.raises(TruthDecisionVerificationError):
        history.find_accepted_event(decision.event_identity)


def test_accepted_event_lookup_rejects_contradictory_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    decision = _decision()
    history = _history_for(monkeypatch, _Database(rows=[_row(decision)]), _HotStore(_capture("other")))

    with pytest.raises(TruthDecisionInvariantError, match="contradicts"):
        history.find_accepted_event(decision.event_identity)


def test_acknowledged_append_publishes_exactly_once(monkeypatch: pytest.MonkeyPatch) -> None:
    sender = _Sender()
    database = _Database(sender=sender)
    history = _history_for(monkeypatch, database)

    history.append(_decision())

    assert len(sender.row_calls) == 1
    assert sender.flush_calls == 1
    assert sender.row_calls[0]["columns"]["contributing_capture_ids"] == '["capture-1","evidence-1"]'
    assert database.wait_wal_table_calls == [
        "SELECT wait_wal_table('truth_history_test')"
    ]
    assert not any("subject_capture_id = $2" in sql for sql in database.queries)


@pytest.mark.parametrize(
    "sender,error_type",
    [
        (_Sender(row_error=OSError("before")), TruthDecisionAppendRejectedError),
        (_Sender(row_error=type("InDoubt", (OSError,), {"in_doubt": True})("ambiguous")), TruthDecisionAppendInDoubtError),
        (_Sender(fsn=None), TruthDecisionAppendInDoubtError),
        (_Sender(acknowledged=False), TruthDecisionAppendInDoubtError),
        (_Sender(await_error=OSError("after")), TruthDecisionAppendInDoubtError),
        (_Sender(errors=[_SenderError(7, 7, questdb.SenderErrorPolicy.Terminal)]), TruthDecisionAppendRejectedError),
        (_Sender(errors=[_SenderError(7, 7, questdb.SenderErrorPolicy.Retriable)]), TruthDecisionAppendInDoubtError),
        (_Sender(dropped=[0, 1]), TruthDecisionAppendInDoubtError),
    ],
    ids=["pre-publication", "explicit-in-doubt", "no-fsn", "ack-false", "ack-exception", "terminal", "retriable", "diagnostic-loss"],
)
def test_append_maps_each_non_successful_upstream_outcome(
    monkeypatch: pytest.MonkeyPatch, sender: _Sender, error_type: type[Exception]
) -> None:
    database = _Database(sender=sender)
    history = _history_for(monkeypatch, database)

    with pytest.raises(error_type):
        history.append(_decision())
    assert len(sender.row_calls) <= 1
    assert sender.flush_calls <= 1
    assert database.wait_wal_table_calls == []


@pytest.mark.parametrize(
    "visibility_rows,error",
    [
        ([{"wait_wal_table": False}], None),
        ([], None),
        ([{"wait_wal_table": True}, {"wait_wal_table": True}], None),
        ([{"wait_wal_table": "true"}], None),
        (None, OSError("barrier unavailable")),
    ],
    ids=["false", "empty", "multiple", "non-boolean", "query-error"],
)
def test_append_fails_in_doubt_when_post_ack_visibility_barrier_is_not_exactly_true(
    monkeypatch: pytest.MonkeyPatch,
    visibility_rows: list[dict[str, object]] | None,
    error: BaseException | None,
) -> None:
    sender = _Sender()
    database = _Database(
        sender=sender,
        visibility_rows=visibility_rows,
        visibility_error=error,
    )
    history = _history_for(monkeypatch, database)

    with pytest.raises(TruthDecisionAppendInDoubtError, match="visibility"):
        history.append(_decision())

    assert len(sender.row_calls) == 1
    assert sender.flush_calls == 1
    assert len(database.wait_wal_table_calls) == 1


def test_decoder_round_trips_optional_identity_and_bounded_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    decision = TruthDecision(
        "capture-2", TruthDecisionCategory.NOT_ACCEPTED, "data-truth/v1", ("capture-2",),
        TradeNotAcceptedReason.INVALID_TRADE_EVIDENCE, None,
    )
    history = _history_for(monkeypatch, _Database(rows=[_row(decision)]))

    assert history.find_subject_decision("data-truth/v1", "capture-2") == decision


@pytest.mark.parametrize("field,value", [("event_trade_id", None), ("category", "unknown"), ("reason", "unknown")])
def test_decoder_fails_closed_for_partial_identity_or_unknown_vocabulary(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    row = _row(_decision())
    row[field] = value
    history = _history_for(monkeypatch, _Database(rows=[row]))

    with pytest.raises(TruthDecisionInvariantError, match="malformed"):
        history.find_subject_decision("data-truth/v1", "capture-1")


@pytest.mark.parametrize("table_name", ["bad-name", "bad name", "1bad", "bad;drop"])
def test_invalid_table_names_are_rejected(table_name: str) -> None:
    with pytest.raises(ValueError):
        QuestDBTruthDecisionHistory("ws::", table_name=table_name, hot_store=_HotStore(), acknowledgement_timeout_millis=1)


@pytest.mark.parametrize("timeout,error_type", [(True, TypeError), (-1, ValueError), ("1", TypeError)])
def test_acknowledgement_timeout_is_validated(timeout: object, error_type: type[Exception]) -> None:
    with pytest.raises(error_type):
        QuestDBTruthDecisionHistory("ws::", table_name="truth_history_test", hot_store=_HotStore(), acknowledgement_timeout_millis=timeout)  # type: ignore[arg-type]


def test_close_releases_connected_database_without_publishing(monkeypatch: pytest.MonkeyPatch) -> None:
    database = _Database()
    history = _history_for(monkeypatch, database)

    history.find_subject_decision("data-truth/v1", "missing")
    history.close()
    history.close()

    assert database.closed is True
    assert database._sender.row_calls == []
