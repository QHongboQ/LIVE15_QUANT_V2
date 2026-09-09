"""Controlled and opt-in integration coverage for the Replay QuestDB source."""

from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

import pytest

_LOGICAL_EVIDENCE_AUTHORITY = "capture-authority/v1"
_LOGICAL_TRUTH_AUTHORITY = "truth-authority/v1"
_LOGICAL_AVAILABILITY_AUTHORITY = "availability-authority/v1"


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
        table_names: tuple[str, str, str] = ("evidence", "truth", "availability"),
    ) -> None:
        self.queries: list[tuple[str, list[Any]]] = []
        self.evidence = list(evidence or [])
        self.truth = list(truth or [])
        self.availability = list(availability or [])
        self.tables = tables
        self.table_names = table_names

    def query(self, sql: str, binds: list[Any]) -> _Result:
        self.queries.append((sql, binds))
        if "FROM tables()" in sql:
            if self.tables is not None:
                return _Result(self.tables)
            return _Result(
                [
                    {
                        "table_name": self.table_names[0],
                        "designatedTimestamp": "received_timestamp",
                        "partitionBy": "DAY",
                        "walEnabled": True,
                        "dedup": True,
                    },
                    {
                        "table_name": self.table_names[1],
                        "designatedTimestamp": "physical_written_at",
                        "partitionBy": "DAY",
                        "walEnabled": True,
                        "dedup": False,
                    },
                    {
                        "table_name": self.table_names[2],
                        "designatedTimestamp": "written_at_ns",
                        "partitionBy": "DAY",
                        "walEnabled": True,
                        "dedup": False,
                    },
                ]
            )
        if "FROM table_columns" in sql:
            table = sql.split("table_columns('", 1)[1].split("')", 1)[0]
            evidence_name, truth_name, availability_name = self.table_names
            columns = {
                evidence_name: {
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
                truth_name: {
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
                availability_name: {
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
                        "upsertKey": table == evidence_name
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
    evidence_table: str = "evidence",
    truth_decision_table: str = "truth",
    availability_table: str = "availability",
    evidence_authority_identity: str = _LOGICAL_EVIDENCE_AUTHORITY,
    truth_decision_authority_identity: str = _LOGICAL_TRUTH_AUTHORITY,
    availability_authority_identity: str = _LOGICAL_AVAILABILITY_AUTHORITY,
) -> tuple[Any, _Database]:
    from live15_quant_v2.data.replay_as_of import questdb_source

    database = database or _Database(
        table_names=(evidence_table, truth_decision_table, availability_table)
    )
    monkeypatch.setattr(
        questdb_source.questdb, "connect", lambda *_args, **_kwargs: database
    )
    source = questdb_source.QuestDBReplaySource(
        connection,
        evidence_table=evidence_table,
        truth_decision_table=truth_decision_table,
        availability_table=availability_table,
        evidence_authority_identity=evidence_authority_identity,
        truth_decision_authority_identity=truth_decision_authority_identity,
        availability_authority_identity=availability_authority_identity,
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


def _paired_database(
    *rows: tuple[str, int, int | None, str, int, int],
) -> _Database:
    evidence: list[dict[str, Any]] = []
    truth: list[dict[str, Any]] = []
    availability: list[dict[str, Any]] = []
    for (
        capture_id,
        received,
        provider_time,
        category,
        evidence_time,
        authority_time,
    ) in rows:
        fact = _evidence(capture_id)
        fact["received_timestamp"] = received
        fact["provider_timestamp"] = provider_time
        decision = _truth(capture_id, category)
        decision["contributing_capture_ids"] = f'["{capture_id}"]'
        evidence.append(fact)
        truth.append(decision)
        availability.extend(
            [
                _availability("evidence", capture_id, None, _LOGICAL_EVIDENCE_AUTHORITY)
                | {"available_at_ns": evidence_time},
                _availability(
                    "authority",
                    capture_id,
                    "data-truth/v1",
                    _LOGICAL_TRUTH_AUTHORITY,
                )
                | {"available_at_ns": authority_time},
            ]
        )
    return _Database(evidence=evidence, truth=truth, availability=availability)


def _request(
    *,
    axis: str = "arrival",
    ordering: str = "arrival",
    page_size: int = 10,
    cursor: str | None = None,
) -> Any:
    from live15_quant_v2.data.replay_as_of.models import (
        AsOfRequest,
        ReplayOrdering,
        SelectionAxis,
        SelectionWindow,
    )

    selection_axis = (
        SelectionAxis.ARRIVAL_TIME if axis == "arrival" else SelectionAxis.EVENT_TIME
    )
    replay_ordering = (
        ReplayOrdering.ARRIVAL if ordering == "arrival" else ReplayOrdering.STRICT_EVENT
    )
    return AsOfRequest(
        20,
        "data-truth/v1",
        SelectionWindow(selection_axis, 0, 30),
        replay_ordering,
        None,
        None,
        page_size,
        cursor,
    )


def test_candidate_records_decode_physical_authorities_and_are_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = _Database(evidence=[_evidence()], truth=[_truth()])
    source, _ = _source(monkeypatch, database=database)
    database.availability.extend(
        [
            _availability("evidence", "capture-1", None, _LOGICAL_EVIDENCE_AUTHORITY),
            _availability(
                "authority",
                "capture-1",
                "data-truth/v1",
                _LOGICAL_TRUTH_AUTHORITY,
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


@pytest.mark.parametrize("kind", ["evidence", "authority"])
def test_composite_source_identity_is_rejected_as_an_availability_marker(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )

    database = _Database(evidence=[_evidence()], truth=[_truth()])
    source, _ = _source(monkeypatch, database=database)
    composite = source.source_authorities()
    if kind == "evidence":
        database.availability.extend(
            [
                _availability("evidence", "capture-1", None, composite.evidence),
                _availability(
                    "authority",
                    "capture-1",
                    "data-truth/v1",
                    _LOGICAL_TRUTH_AUTHORITY,
                ),
            ]
        )
    else:
        database.availability.extend(
            [
                _availability(
                    "evidence", "capture-1", None, _LOGICAL_EVIDENCE_AUTHORITY
                ),
                _availability(
                    "authority",
                    "capture-1",
                    "data-truth/v1",
                    composite.truth_decision,
                ),
            ]
        )

    with pytest.raises(ReplayAsOfError) as raised:
        source.candidate_records(_scope())

    assert raised.value.code is ReplayErrorCode.AVAILABILITY_EVIDENCE_MISSING


@pytest.mark.parametrize("kind", ["evidence", "authority"])
def test_negative_availability_marker_is_rejected(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )

    database = _Database(evidence=[_evidence()], truth=[_truth()])
    source, _ = _source(monkeypatch, database=database)
    evidence_marker = _availability(
        "evidence", "capture-1", None, _LOGICAL_EVIDENCE_AUTHORITY
    )
    authority_marker = _availability(
        "authority", "capture-1", "data-truth/v1", _LOGICAL_TRUTH_AUTHORITY
    )
    (evidence_marker if kind == "evidence" else authority_marker)[
        "available_at_ns"
    ] = -1
    database.availability.extend([evidence_marker, authority_marker])

    with pytest.raises(ReplayAsOfError) as raised:
        source.candidate_records(_scope())

    assert raised.value.code is ReplayErrorCode.AVAILABILITY_EVIDENCE_MISSING


def test_slice_two_logical_availability_records_remain_readable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from live15_quant_v2.data.replay_as_of.availability import (
        SUPPORTED_PROOF_SCHEMA_VERSION,
        AvailabilityKind,
        AvailabilityRecord,
    )

    evidence_marker = AvailabilityRecord(
        AvailabilityKind.EVIDENCE,
        "capture-1",
        None,
        10,
        SUPPORTED_PROOF_SCHEMA_VERSION,
        _LOGICAL_EVIDENCE_AUTHORITY,
    )
    authority_marker = AvailabilityRecord(
        AvailabilityKind.AUTHORITY,
        "capture-1",
        "data-truth/v1",
        11,
        SUPPORTED_PROOF_SCHEMA_VERSION,
        _LOGICAL_TRUTH_AUTHORITY,
    )
    database = _Database(
        evidence=[_evidence()],
        truth=[_truth()],
        availability=[
            _availability(
                evidence_marker.kind.value,
                evidence_marker.capture_id,
                evidence_marker.policy_version,
                evidence_marker.source_authority_identity,
            ),
            _availability(
                authority_marker.kind.value,
                authority_marker.capture_id,
                authority_marker.policy_version,
                authority_marker.source_authority_identity,
            ),
        ],
    )
    database.availability[0]["available_at_ns"] = evidence_marker.available_at_ns
    database.availability[1]["available_at_ns"] = authority_marker.available_at_ns
    source, _ = _source(monkeypatch, database=database)

    record = source.candidate_records(_scope())[0]

    assert record.evidence_availability.available_at_ns == 10
    assert record.authority_availability.available_at_ns == 11


def test_replay_as_of_preserves_categories_and_fails_closed_for_null_event_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )
    from live15_quant_v2.data.replay_as_of.service import ReplayAsOf

    source, _ = _source(
        monkeypatch,
        database=_paired_database(
            ("capture-a", 1, None, "accepted", 10, 10),
            ("capture-b", 2, 2, "duplicate", 10, 10),
            ("capture-c", 3, 3, "conflict", 10, 10),
            ("capture-d", 4, 4, "not_accepted", 10, 10),
        ),
    )
    replay = ReplayAsOf(source, max_page_size=10)

    arrival = replay.read(_request())
    assert [record.truth_decision.category.value for record in arrival.records] == [
        "accepted",
        "duplicate",
        "conflict",
        "not_accepted",
    ]
    with pytest.raises(ReplayAsOfError) as event:
        replay.read(_request(axis="event"))
    with pytest.raises(ReplayAsOfError) as strict:
        replay.read(_request(ordering="strict"))
    assert event.value.code is ReplayErrorCode.UNSUPPORTED_EVENT_TIME
    assert strict.value.code is ReplayErrorCode.UNSUPPORTED_EVENT_TIME


def test_pagination_restart_and_membership_drift_are_bound_to_source_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )
    from live15_quant_v2.data.replay_as_of.service import ReplayAsOf

    database = _paired_database(
        ("capture-a", 1, 1, "accepted", 10, 10),
        ("capture-b", 2, 2, "duplicate", 10, 10),
    )
    first_source, _ = _source(monkeypatch, database=database)
    first_page = ReplayAsOf(first_source, max_page_size=10).read(_request(page_size=1))
    assert first_page.next_cursor is not None
    first_source.close()
    restarted_source, _ = _source(monkeypatch, database=database)
    restarted_page = ReplayAsOf(restarted_source, max_page_size=10).read(
        _request(page_size=1, cursor=first_page.next_cursor)
    )
    assert [record.capture_fact.capture_id for record in restarted_page.records] == [
        "capture-b"
    ]
    assert (
        restarted_page.source_snapshot_identity == first_page.source_snapshot_identity
    )

    future = _paired_database(("capture-future", 3, 3, "conflict", 21, 21))
    database.evidence.extend(future.evidence)
    database.truth.extend(future.truth)
    database.availability.extend(future.availability)
    continued = ReplayAsOf(restarted_source, max_page_size=10).read(
        _request(page_size=1, cursor=first_page.next_cursor)
    )
    assert [record.capture_fact.capture_id for record in continued.records] == [
        "capture-b"
    ]
    assert continued.source_snapshot_identity == first_page.source_snapshot_identity

    backdated = _paired_database(("capture-backdated", 4, 4, "conflict", 10, 10))
    database.evidence.extend(backdated.evidence)
    database.truth.extend(backdated.truth)
    database.availability.extend(backdated.availability)
    with pytest.raises(ReplayAsOfError) as raised:
        ReplayAsOf(restarted_source, max_page_size=10).read(
            _request(page_size=1, cursor=first_page.next_cursor)
        )
    assert raised.value.code is ReplayErrorCode.SOURCE_UNAVAILABLE


def test_table_reconfiguration_rejects_a_previously_bound_cursor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )
    from live15_quant_v2.data.replay_as_of.service import ReplayAsOf

    first_database = _paired_database(
        ("capture-a", 1, 1, "accepted", 10, 10),
        ("capture-b", 2, 2, "duplicate", 10, 10),
    )
    first_source, _ = _source(monkeypatch, database=first_database)
    first_page = ReplayAsOf(first_source, max_page_size=10).read(_request(page_size=1))
    replacement_database = _paired_database(
        ("capture-a", 1, 1, "accepted", 10, 10),
        ("capture-b", 2, 2, "duplicate", 10, 10),
    )
    replacement_database.table_names = ("evidence_alt", "truth", "availability")
    replacement_source, _ = _source(
        monkeypatch,
        database=replacement_database,
        evidence_table="evidence_alt",
    )

    with pytest.raises(ReplayAsOfError) as raised:
        ReplayAsOf(replacement_source, max_page_size=10).read(
            _request(page_size=1, cursor=first_page.next_cursor)
        )
    assert raised.value.code is ReplayErrorCode.SOURCE_UNAVAILABLE


def test_logical_and_table_reconfiguration_change_only_the_relevant_composite_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline, _ = _source(monkeypatch)
    base = baseline.source_authorities()
    changed_evidence_logical, _ = _source(
        monkeypatch, evidence_authority_identity="capture-authority/v2"
    )
    evidence_logical = changed_evidence_logical.source_authorities()
    changed_truth_logical, _ = _source(
        monkeypatch, truth_decision_authority_identity="truth-authority/v2"
    )
    truth_logical = changed_truth_logical.source_authorities()
    changed_availability_logical, _ = _source(
        monkeypatch, availability_authority_identity="availability-authority/v2"
    )
    availability_logical = changed_availability_logical.source_authorities()
    changed_evidence_table, _ = _source(monkeypatch, evidence_table="evidence_alt")
    evidence_table = changed_evidence_table.source_authorities()
    changed_truth_table, _ = _source(monkeypatch, truth_decision_table="truth_alt")
    truth_table = changed_truth_table.source_authorities()
    changed_availability_table, _ = _source(
        monkeypatch, availability_table="availability_alt"
    )
    availability_table = changed_availability_table.source_authorities()

    assert evidence_logical == type(base)(
        evidence_logical.evidence,
        base.truth_decision,
        base.availability,
    )
    assert truth_logical == type(base)(
        base.evidence,
        truth_logical.truth_decision,
        base.availability,
    )
    assert availability_logical == type(base)(
        base.evidence,
        base.truth_decision,
        availability_logical.availability,
    )
    assert evidence_table == type(base)(
        evidence_table.evidence,
        base.truth_decision,
        base.availability,
    )
    assert truth_table == type(base)(
        base.evidence, truth_table.truth_decision, base.availability
    )
    assert availability_table == type(base)(
        base.evidence, base.truth_decision, availability_table.availability
    )


def test_close_and_recreate_preserves_identical_source_authorities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, _ = _source(monkeypatch)
    expected = first.source_authorities()
    first.close()
    recreated, _ = _source(monkeypatch)

    assert recreated.source_authorities() == expected


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


@pytest.mark.parametrize("facts", [[], [_evidence(), _evidence()]])
def test_absent_or_duplicate_physical_evidence_is_malformed(
    monkeypatch: pytest.MonkeyPatch, facts: list[dict[str, Any]]
) -> None:
    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )

    source, _ = _source(
        monkeypatch, database=_Database(evidence=facts, truth=[_truth()])
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
        ("reason", "unexpected"),
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


def test_complete_event_identity_and_other_policy_rows_are_not_latest_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exact = _truth()
    exact.update(
        {
            "event_provider": "kalshi",
            "event_source_id": "KXBTC",
            "event_message_type": "trade",
            "event_trade_id": "trade-1",
        }
    )
    other = _truth()
    other["policy_version"] = "other-policy/v1"
    source, _ = _source(
        monkeypatch, database=_Database(evidence=[_evidence()], truth=[exact, other])
    )

    records = source.candidate_records(_scope())

    assert len(records) == 1
    assert records[0].truth_decision.event_identity is not None
    assert records[0].truth_decision.policy_version == "data-truth/v1"


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
    marker = _availability("evidence", "capture-1", None, _LOGICAL_EVIDENCE_AUTHORITY)
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


@pytest.mark.parametrize("missing", ["evidence", "truth", "availability"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("walEnabled", False),
        ("dedup", True),
        ("partitionBy", "MONTH"),
        ("designatedTimestamp", "wrong_timestamp"),
    ],
)
def test_missing_or_wrong_physical_table_metadata_is_source_unavailable(
    monkeypatch: pytest.MonkeyPatch, missing: str, field: str, value: Any
) -> None:
    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )

    database = _Database()
    tables = (
        database.query("SELECT table_name FROM tables()", [])
        .to_pandas()
        .to_dict(orient="records")
    )
    if missing == "evidence":
        tables = [row for row in tables if row["table_name"] != "evidence"]
    elif missing == "truth":
        tables = [row for row in tables if row["table_name"] != "truth"]
    else:
        tables = [row for row in tables if row["table_name"] != "availability"]
    missing_source, _ = _source(monkeypatch, database=_Database(tables=tables))
    with pytest.raises(ReplayAsOfError) as missing_error:
        missing_source.source_authorities()
    assert missing_error.value.code is ReplayErrorCode.SOURCE_UNAVAILABLE

    incompatible = _Database()
    incompatible_tables = (
        incompatible.query("SELECT table_name FROM tables()", [])
        .to_pandas()
        .to_dict(orient="records")
    )
    incompatible_tables[1 if field == "dedup" else 0][field] = value
    incompatible_source, _ = _source(
        monkeypatch, database=_Database(tables=incompatible_tables)
    )
    with pytest.raises(ReplayAsOfError) as incompatible_error:
        incompatible_source.source_authorities()
    assert incompatible_error.value.code is ReplayErrorCode.SOURCE_UNAVAILABLE


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
        ReplayAsOfError,
        ReplayErrorCode,
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
            evidence_authority_identity=_LOGICAL_EVIDENCE_AUTHORITY,
            truth_decision_authority_identity=_LOGICAL_TRUTH_AUTHORITY,
            availability_authority_identity=_LOGICAL_AVAILABILITY_AUTHORITY,
        )
        captures = (
            ("capture-1", None, "accepted", 5),
            ("capture-2", 6, "duplicate", 6),
            ("capture-3", 7, "conflict", 7),
            ("capture-4", 8, "not_accepted", 8),
        )
        with database.sender() as sender:
            for (
                capture_id,
                provider_timestamp,
                category,
                received_timestamp,
            ) in captures:
                sender.row(
                    evidence,
                    columns={
                        "capture_id": capture_id,
                        "asset": "BTC",
                        "provider": "kalshi",
                        "source_id": "KXBTC",
                        "channel": "trade",
                        "message_type": "trade",
                        "event_subtype": None,
                        "sid": 1,
                        "seq": None,
                        "provider_timestamp": None
                        if provider_timestamp is None
                        else questdb.TimestampNanos(provider_timestamp),
                        "schema_version": "market-ingress/v1",
                        "payload": "{}",
                    },
                    at=questdb.TimestampNanos(received_timestamp),
                )
                sender.row(
                    truth,
                    columns={
                        "policy_version": "data-truth/v1",
                        "subject_capture_id": capture_id,
                        "category": category,
                        "contributing_capture_ids": f'["{capture_id}"]',
                        "reason": None,
                        "event_provider": None,
                        "event_source_id": None,
                        "event_message_type": None,
                        "event_trade_id": None,
                    },
                    at=questdb.TimestampNanos(received_timestamp + 10),
                )
            fsn = sender.flush_and_get_fsn()
            assert fsn is not None and sender.await_acked_fsn(
                fsn, timeout_millis=15_000
            )
        assert source.source_authorities().evidence
        with database.sender() as sender:
            for capture_id, _, _, received_timestamp in captures:
                sender.row(
                    availability,
                    columns={
                        "kind": "evidence",
                        "capture_id": capture_id,
                        "policy_version": None,
                        "available_at_ns": questdb.TimestampNanos(10),
                        "proof_schema_version": "replay-availability-proof/v1",
                        "source_authority_identity": _LOGICAL_EVIDENCE_AUTHORITY,
                    },
                    at=questdb.TimestampNanos(received_timestamp + 20),
                )
                sender.row(
                    availability,
                    columns={
                        "kind": "authority",
                        "capture_id": capture_id,
                        "policy_version": "data-truth/v1",
                        "available_at_ns": questdb.TimestampNanos(10),
                        "proof_schema_version": "replay-availability-proof/v1",
                        "source_authority_identity": _LOGICAL_TRUTH_AUTHORITY,
                    },
                    at=questdb.TimestampNanos(received_timestamp + 30),
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
            "capture-1",
            "capture-2",
            "capture-3",
            "capture-4",
        ]
        assert [record.truth_decision.category.value for record in view.records] == [
            "accepted",
            "duplicate",
            "conflict",
            "not_accepted",
        ]
        with pytest.raises(ReplayAsOfError) as event:
            ReplayAsOf(source, max_page_size=10).read(
                AsOfRequest(
                    20,
                    "data-truth/v1",
                    SelectionWindow(SelectionAxis.EVENT_TIME, 0, 20),
                    ReplayOrdering.ARRIVAL,
                    None,
                    None,
                    10,
                    None,
                )
            )
        assert event.value.code is ReplayErrorCode.UNSUPPORTED_EVENT_TIME
        first_page = ReplayAsOf(source, max_page_size=10).read(
            AsOfRequest(
                20,
                "data-truth/v1",
                SelectionWindow(SelectionAxis.ARRIVAL_TIME, 0, 20),
                ReplayOrdering.ARRIVAL,
                None,
                None,
                1,
                None,
            )
        )
        assert first_page.next_cursor is not None
        source.close()
        restarted = QuestDBReplaySource(
            server.connection_string,
            evidence_table=evidence,
            truth_decision_table=truth,
            availability_table=availability,
            evidence_authority_identity=_LOGICAL_EVIDENCE_AUTHORITY,
            truth_decision_authority_identity=_LOGICAL_TRUTH_AUTHORITY,
            availability_authority_identity=_LOGICAL_AVAILABILITY_AUTHORITY,
        )
        second_page = ReplayAsOf(restarted, max_page_size=10).read(
            AsOfRequest(
                20,
                "data-truth/v1",
                SelectionWindow(SelectionAxis.ARRIVAL_TIME, 0, 20),
                ReplayOrdering.ARRIVAL,
                None,
                None,
                1,
                first_page.next_cursor,
            )
        )
        assert [record.capture_fact.capture_id for record in second_page.records] == [
            "capture-2"
        ]
        restarted.close()
    _assert_lifecycle(server)


def _real_tables(database: Any, suffix: str) -> tuple[str, str, str]:
    evidence, truth, availability = (
        f"replay_evidence_{suffix}",
        f"replay_truth_{suffix}",
        f"replay_availability_{suffix}",
    )
    database.execute(
        f"CREATE TABLE {evidence} (capture_id VARCHAR, asset SYMBOL, provider SYMBOL, source_id VARCHAR, channel SYMBOL, message_type VARCHAR, event_subtype VARCHAR, sid LONG, seq LONG, provider_timestamp TIMESTAMP_NS, schema_version VARCHAR, payload VARCHAR, received_timestamp TIMESTAMP_NS) TIMESTAMP(received_timestamp) PARTITION BY DAY WAL DEDUP UPSERT KEYS(received_timestamp, capture_id)"
    )
    database.execute(
        f"CREATE TABLE {truth} (policy_version VARCHAR, subject_capture_id VARCHAR, category VARCHAR, contributing_capture_ids VARCHAR, reason VARCHAR, event_provider VARCHAR, event_source_id VARCHAR, event_message_type VARCHAR, event_trade_id VARCHAR, physical_written_at TIMESTAMP_NS) TIMESTAMP(physical_written_at) PARTITION BY DAY WAL"
    )
    database.execute(
        f"CREATE TABLE {availability} (kind VARCHAR, capture_id VARCHAR, policy_version VARCHAR, available_at_ns TIMESTAMP_NS, proof_schema_version VARCHAR, source_authority_identity VARCHAR, written_at_ns TIMESTAMP_NS) TIMESTAMP(written_at_ns) PARTITION BY DAY WAL"
    )
    return evidence, truth, availability


def _real_append_pair(
    database: Any,
    questdb_module: Any,
    tables: tuple[str, str, str],
    capture_id: str,
    *,
    received_timestamp: int,
    available_at_ns: int = 10,
    category: str = "accepted",
) -> None:
    evidence, truth, availability = tables
    with database.sender() as sender:
        sender.row(
            evidence,
            columns={
                "capture_id": capture_id,
                "asset": "BTC",
                "provider": "kalshi",
                "source_id": "KXBTC",
                "channel": "trade",
                "message_type": "trade",
                "event_subtype": None,
                "sid": 1,
                "seq": None,
                "provider_timestamp": questdb_module.TimestampNanos(received_timestamp),
                "schema_version": "market-ingress/v1",
                "payload": "{}",
            },
            at=questdb_module.TimestampNanos(received_timestamp),
        )
        sender.row(
            truth,
            columns={
                "policy_version": "data-truth/v1",
                "subject_capture_id": capture_id,
                "category": category,
                "contributing_capture_ids": f'["{capture_id}"]',
                "reason": None,
                "event_provider": None,
                "event_source_id": None,
                "event_message_type": None,
                "event_trade_id": None,
            },
            at=questdb_module.TimestampNanos(received_timestamp + 100),
        )
        fsn = sender.flush_and_get_fsn()
        assert fsn is not None and sender.await_acked_fsn(fsn, timeout_millis=15_000)
    with database.sender() as sender:
        sender.row(
            availability,
            columns={
                "kind": "evidence",
                "capture_id": capture_id,
                "policy_version": None,
                "available_at_ns": questdb_module.TimestampNanos(available_at_ns),
                "proof_schema_version": "replay-availability-proof/v1",
                "source_authority_identity": _LOGICAL_EVIDENCE_AUTHORITY,
            },
            at=questdb_module.TimestampNanos(received_timestamp + 200),
        )
        sender.row(
            availability,
            columns={
                "kind": "authority",
                "capture_id": capture_id,
                "policy_version": "data-truth/v1",
                "available_at_ns": questdb_module.TimestampNanos(available_at_ns),
                "proof_schema_version": "replay-availability-proof/v1",
                "source_authority_identity": _LOGICAL_TRUTH_AUTHORITY,
            },
            at=questdb_module.TimestampNanos(received_timestamp + 300),
        )
        fsn = sender.flush_and_get_fsn()
        assert fsn is not None and sender.await_acked_fsn(fsn, timeout_millis=15_000)
    for table in tables:
        assert (
            database.query(f"SELECT wait_wal_table('{table}')", [])
            .to_pandas()
            .to_dict(orient="records")[0]
        )


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("LIVE15_RUN_REPLAY_SOURCE_QUESTDB_INTEGRATION") != "1",
    reason="set LIVE15_RUN_REPLAY_SOURCE_QUESTDB_INTEGRATION=1 to run task-owned QuestDB",
)
def test_real_duplicate_physical_rows_fail_closed(tmp_path: Any) -> None:
    import questdb
    from test_questdb_truth_history_integration import _assert_lifecycle, _server

    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )
    from live15_quant_v2.data.replay_as_of.questdb_source import QuestDBReplaySource
    from live15_quant_v2.data.replay_as_of.service import ReplayAsOf

    with _server(tmp_path) as server:
        assert server.database is not None
        database = server.database
        tables = _real_tables(database, uuid4().hex)
        _real_append_pair(database, questdb, tables, "duplicate", received_timestamp=1)
        with database.sender() as sender:
            sender.row(
                tables[0],
                columns={
                    "capture_id": "duplicate",
                    "asset": "BTC",
                    "provider": "kalshi",
                    "source_id": "KXBTC",
                    "channel": "trade",
                    "message_type": "trade",
                    "event_subtype": None,
                    "sid": 1,
                    "seq": None,
                    "provider_timestamp": questdb.TimestampNanos(2),
                    "schema_version": "market-ingress/v1",
                    "payload": "{}",
                },
                at=questdb.TimestampNanos(2),
            )
            fsn = sender.flush_and_get_fsn()
            assert fsn is not None and sender.await_acked_fsn(
                fsn, timeout_millis=15_000
            )
        assert (
            database.query(f"SELECT wait_wal_table('{tables[0]}')", [])
            .to_pandas()
            .to_dict(orient="records")[0]
        )
        source = QuestDBReplaySource(
            server.connection_string,
            evidence_table=tables[0],
            truth_decision_table=tables[1],
            availability_table=tables[2],
            evidence_authority_identity=_LOGICAL_EVIDENCE_AUTHORITY,
            truth_decision_authority_identity=_LOGICAL_TRUTH_AUTHORITY,
            availability_authority_identity=_LOGICAL_AVAILABILITY_AUTHORITY,
        )
        with pytest.raises(ReplayAsOfError) as raised:
            ReplayAsOf(source, max_page_size=10).read(_request())
        assert raised.value.code is ReplayErrorCode.MALFORMED_EVIDENCE
        source.close()
    _assert_lifecycle(server)


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("LIVE15_RUN_REPLAY_SOURCE_QUESTDB_INTEGRATION") != "1",
    reason="set LIVE15_RUN_REPLAY_SOURCE_QUESTDB_INTEGRATION=1 to run task-owned QuestDB",
)
def test_real_duplicate_authority_and_availability_fail_closed(tmp_path: Any) -> None:
    import questdb
    from test_questdb_truth_history_integration import _assert_lifecycle, _server

    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )
    from live15_quant_v2.data.replay_as_of.questdb_source import QuestDBReplaySource
    from live15_quant_v2.data.replay_as_of.service import ReplayAsOf

    def source_for(server: Any, tables: tuple[str, str, str]) -> Any:
        return QuestDBReplaySource(
            server.connection_string,
            evidence_table=tables[0],
            truth_decision_table=tables[1],
            availability_table=tables[2],
            evidence_authority_identity=_LOGICAL_EVIDENCE_AUTHORITY,
            truth_decision_authority_identity=_LOGICAL_TRUTH_AUTHORITY,
            availability_authority_identity=_LOGICAL_AVAILABILITY_AUTHORITY,
        )

    with _server(tmp_path) as server:
        assert server.database is not None
        database = server.database
        authority_tables = _real_tables(database, uuid4().hex)
        _real_append_pair(
            database,
            questdb,
            authority_tables,
            "authority-duplicate",
            received_timestamp=1,
        )
        with database.sender() as sender:
            sender.row(
                authority_tables[1],
                columns={
                    "policy_version": "data-truth/v1",
                    "subject_capture_id": "authority-duplicate",
                    "category": "accepted",
                    "contributing_capture_ids": '["authority-duplicate"]',
                    "reason": None,
                    "event_provider": None,
                    "event_source_id": None,
                    "event_message_type": None,
                    "event_trade_id": None,
                },
                at=questdb.TimestampNanos(102),
            )
            fsn = sender.flush_and_get_fsn()
            assert fsn is not None and sender.await_acked_fsn(
                fsn, timeout_millis=15_000
            )
        assert (
            database.query(f"SELECT wait_wal_table('{authority_tables[1]}')", [])
            .to_pandas()
            .to_dict(orient="records")[0]
        )
        authority_source = source_for(server, authority_tables)
        with pytest.raises(ReplayAsOfError) as authority_error:
            ReplayAsOf(authority_source, max_page_size=10).read(_request())
        assert authority_error.value.code is ReplayErrorCode.AUTHORITY_CONFLICT
        authority_source.close()

        availability_tables = _real_tables(database, uuid4().hex)
        _real_append_pair(
            database,
            questdb,
            availability_tables,
            "availability-duplicate",
            received_timestamp=1,
        )
        with database.sender() as sender:
            sender.row(
                availability_tables[2],
                columns={
                    "kind": "evidence",
                    "capture_id": "availability-duplicate",
                    "policy_version": None,
                    "available_at_ns": questdb.TimestampNanos(10),
                    "proof_schema_version": "replay-availability-proof/v1",
                    "source_authority_identity": _LOGICAL_EVIDENCE_AUTHORITY,
                },
                at=questdb.TimestampNanos(999),
            )
            fsn = sender.flush_and_get_fsn()
            assert fsn is not None and sender.await_acked_fsn(
                fsn, timeout_millis=15_000
            )
        assert (
            database.query(f"SELECT wait_wal_table('{availability_tables[2]}')", [])
            .to_pandas()
            .to_dict(orient="records")[0]
        )
        availability_source = source_for(server, availability_tables)
        with pytest.raises(ReplayAsOfError) as availability_error:
            ReplayAsOf(availability_source, max_page_size=10).read(_request())
        assert (
            availability_error.value.code
            is ReplayErrorCode.AVAILABILITY_EVIDENCE_MISSING
        )
        availability_source.close()
    _assert_lifecycle(server)


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("LIVE15_RUN_REPLAY_SOURCE_QUESTDB_INTEGRATION") != "1",
    reason="set LIVE15_RUN_REPLAY_SOURCE_QUESTDB_INTEGRATION=1 to run task-owned QuestDB",
)
def test_real_source_reconfiguration_and_membership_drift(tmp_path: Any) -> None:
    import questdb
    from test_questdb_truth_history_integration import _assert_lifecycle, _server

    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )
    from live15_quant_v2.data.replay_as_of.questdb_source import QuestDBReplaySource
    from live15_quant_v2.data.replay_as_of.service import ReplayAsOf

    def source_for(server: Any, tables: tuple[str, str, str]) -> Any:
        return QuestDBReplaySource(
            server.connection_string,
            evidence_table=tables[0],
            truth_decision_table=tables[1],
            availability_table=tables[2],
            evidence_authority_identity=_LOGICAL_EVIDENCE_AUTHORITY,
            truth_decision_authority_identity=_LOGICAL_TRUTH_AUTHORITY,
            availability_authority_identity=_LOGICAL_AVAILABILITY_AUTHORITY,
        )

    with _server(tmp_path) as server:
        assert server.database is not None
        database = server.database
        first_tables = _real_tables(database, uuid4().hex)
        second_tables = _real_tables(database, uuid4().hex)
        for tables in (first_tables, second_tables):
            _real_append_pair(
                database, questdb, tables, "capture-a", received_timestamp=1
            )
            _real_append_pair(
                database, questdb, tables, "capture-b", received_timestamp=2
            )
        first_source = source_for(server, first_tables)
        first_page = ReplayAsOf(first_source, max_page_size=10).read(
            _request(page_size=1)
        )
        assert first_page.next_cursor is not None
        reconfigured = source_for(server, second_tables)
        with pytest.raises(ReplayAsOfError) as reconfigured_error:
            ReplayAsOf(reconfigured, max_page_size=10).read(
                _request(page_size=1, cursor=first_page.next_cursor)
            )
        assert reconfigured_error.value.code is ReplayErrorCode.SOURCE_UNAVAILABLE
        reconfigured.close()

        _real_append_pair(
            database,
            questdb,
            first_tables,
            "capture-future",
            received_timestamp=3,
            available_at_ns=21,
        )
        continued = ReplayAsOf(first_source, max_page_size=10).read(
            _request(page_size=1, cursor=first_page.next_cursor)
        )
        assert [record.capture_fact.capture_id for record in continued.records] == [
            "capture-b"
        ]
        assert continued.source_snapshot_identity == first_page.source_snapshot_identity

        _real_append_pair(
            database, questdb, first_tables, "capture-backdated", received_timestamp=4
        )
        with pytest.raises(ReplayAsOfError) as drift_error:
            ReplayAsOf(first_source, max_page_size=10).read(
                _request(page_size=1, cursor=first_page.next_cursor)
            )
        assert drift_error.value.code is ReplayErrorCode.SOURCE_UNAVAILABLE
        first_source.close()
    _assert_lifecycle(server)


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("LIVE15_RUN_REPLAY_SOURCE_QUESTDB_INTEGRATION") != "1",
    reason="set LIVE15_RUN_REPLAY_SOURCE_QUESTDB_INTEGRATION=1 to run task-owned QuestDB",
)
def test_real_malformed_truth_row_has_bounded_error(tmp_path: Any) -> None:
    import questdb
    from test_questdb_truth_history_integration import _assert_lifecycle, _server

    from live15_quant_v2.data.replay_as_of.models import (
        ReplayAsOfError,
        ReplayErrorCode,
    )
    from live15_quant_v2.data.replay_as_of.questdb_source import QuestDBReplaySource
    from live15_quant_v2.data.replay_as_of.service import ReplayAsOf

    with _server(tmp_path) as server:
        assert server.database is not None
        database = server.database
        tables = _real_tables(database, uuid4().hex)
        with database.sender() as sender:
            sender.row(
                tables[0],
                columns={
                    "capture_id": "malformed-authority",
                    "asset": "BTC",
                    "provider": "kalshi",
                    "source_id": "KXBTC",
                    "channel": "trade",
                    "message_type": "trade",
                    "event_subtype": None,
                    "sid": 1,
                    "seq": None,
                    "provider_timestamp": questdb.TimestampNanos(1),
                    "schema_version": "market-ingress/v1",
                    "payload": "{}",
                },
                at=questdb.TimestampNanos(1),
            )
            sender.row(
                tables[1],
                columns={
                    "policy_version": "data-truth/v1",
                    "subject_capture_id": "malformed-authority",
                    "category": "not-a-truth-decision-category",
                    "contributing_capture_ids": '["malformed-authority"]',
                    "reason": None,
                    "event_provider": None,
                    "event_source_id": None,
                    "event_message_type": None,
                    "event_trade_id": None,
                },
                at=questdb.TimestampNanos(2),
            )
            fsn = sender.flush_and_get_fsn()
            assert fsn is not None and sender.await_acked_fsn(
                fsn, timeout_millis=15_000
            )
        for table in tables[:2]:
            assert (
                database.query(f"SELECT wait_wal_table('{table}')", [])
                .to_pandas()
                .to_dict(orient="records")[0]
            )
        source = QuestDBReplaySource(
            server.connection_string,
            evidence_table=tables[0],
            truth_decision_table=tables[1],
            availability_table=tables[2],
            evidence_authority_identity=_LOGICAL_EVIDENCE_AUTHORITY,
            truth_decision_authority_identity=_LOGICAL_TRUTH_AUTHORITY,
            availability_authority_identity=_LOGICAL_AVAILABILITY_AUTHORITY,
        )
        with pytest.raises(ReplayAsOfError) as raised:
            ReplayAsOf(source, max_page_size=10).read(_request())
        assert raised.value.code is ReplayErrorCode.MALFORMED_AUTHORITY
        source.close()
    _assert_lifecycle(server)
