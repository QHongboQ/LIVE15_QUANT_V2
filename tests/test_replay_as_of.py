"""Public behavior tests for the provider-neutral Replay & As-Of pure core."""

import base64
import json

import pytest

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.data_truth.models import TruthDecision, TruthDecisionCategory
from live15_quant_v2.data.replay_as_of import (
    AsOfRequest,
    ReplayAsOf,
    ReplayAsOfError,
    ReplayErrorCode,
    ReplayOrdering,
    SelectionAxis,
    SelectionWindow,
)
from live15_quant_v2.data.replay_as_of.source import (
    AvailabilityEvidence,
    InMemoryReplaySource,
    ReplaySourceRecord,
    SourceAuthorityIdentities,
)
from live15_quant_v2.data.storage.capture import CaptureFact


def _fact(capture_id: str = "capture-1") -> CaptureFact:
    return CaptureFact(
        capture_id,
        AssetId.BTC,
        "provider",
        "source",
        "trade",
        "trade",
        None,
        1,
        1,
        10,
        20,
        "market-ingress/v1",
        "{}",
    )


def _decision(fact: CaptureFact) -> TruthDecision:
    return TruthDecision(
        fact.capture_id,
        TruthDecisionCategory.ACCEPTED,
        "data-truth/v1",
        (fact.capture_id,),
        None,
        None,
    )


def _source(*records: ReplaySourceRecord) -> InMemoryReplaySource:
    return InMemoryReplaySource(
        list(records),
        SourceAuthorityIdentities("evidence/v1", "truth/v1", "availability/v1"),
    )


def _record(
    capture_id: str = "capture-1",
    *,
    provider_timestamp: int | None = 10,
    received_timestamp: int = 20,
    evidence: AvailabilityEvidence | None = None,
    authority: AvailabilityEvidence | None = None,
    category: TruthDecisionCategory = TruthDecisionCategory.ACCEPTED,
) -> ReplaySourceRecord:
    fact = CaptureFact(
        capture_id,
        AssetId.BTC,
        "provider",
        "source",
        "trade",
        "trade",
        None,
        1,
        1,
        provider_timestamp,
        received_timestamp,
        "market-ingress/v1",
        "{}",
    )
    return ReplaySourceRecord(
        fact,
        TruthDecision(
            fact.capture_id,
            category,
            "data-truth/v1",
            (fact.capture_id,),
            None,
            None,
        ),
        evidence or AvailabilityEvidence(30, f"evidence-{capture_id}"),
        authority or AvailabilityEvidence(40, f"authority-{capture_id}"),
    )


def _request(
    *,
    cutoff: object = 50,
    axis: object = SelectionAxis.ARRIVAL_TIME,
    start: object = 0,
    end: object = 100,
    policy: object = "data-truth/v1",
    ordering: object = ReplayOrdering.ARRIVAL,
    assets: object = (AssetId.BTC,),
    channels: object = ("trade",),
    page_size: object = 10,
    cursor: object = None,
) -> AsOfRequest:
    return AsOfRequest(
        cutoff,
        policy,
        SelectionWindow(axis, start, end),
        ordering,
        assets,
        channels,
        page_size,
        cursor,
    )


def _read(request: AsOfRequest, *records: ReplaySourceRecord) -> object:
    return ReplayAsOf(_source(*records), max_page_size=20).read(request)


def _encode_cursor(payload: dict[str, object]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(body).decode("ascii").rstrip("=")


def test_read_returns_one_paired_arrival_record() -> None:
    fact = _fact()
    source = InMemoryReplaySource(
        [
            ReplaySourceRecord(
                fact,
                _decision(fact),
                AvailabilityEvidence(30, "evidence-1"),
                AvailabilityEvidence(40, "authority-1"),
            )
        ],
        SourceAuthorityIdentities("evidence/v1", "truth/v1", "availability/v1"),
    )
    request = AsOfRequest(
        50,
        "data-truth/v1",
        SelectionWindow(SelectionAxis.ARRIVAL_TIME, 0, 30),
        ReplayOrdering.ARRIVAL,
        (AssetId.BTC,),
        ("trade",),
        10,
        None,
    )

    view = ReplayAsOf(source, max_page_size=20).read(request)

    assert [record.capture_fact.capture_id for record in view.records] == ["capture-1"]
    assert view.next_cursor is None


@pytest.mark.parametrize(
    "as_of_request",
    [
        _request(cutoff="50"),
        _request(cutoff=True),
        _request(start=True),
        _request(start=10, end=10),
        _request(start=11, end=10),
        _request(policy="data-truth/v2"),
        _request(axis="arrival_time"),
        _request(ordering="arrival"),
        _request(assets=("BTC",)),
        _request(channels=("",)),
        _request(page_size=0),
        _request(page_size=-1),
        _request(page_size=21),
    ],
)
def test_invalid_semantic_request_is_rejected(as_of_request: AsOfRequest) -> None:
    with pytest.raises(ReplayAsOfError) as error:
        _read(as_of_request, _record())

    assert error.value.code is ReplayErrorCode.INVALID_REQUEST


def test_request_identity_is_deterministic_and_filter_order_independent() -> None:
    first = _read(
        _request(assets=(AssetId.ETH, AssetId.BTC), channels=("book", "trade")),
        _record(),
    )
    second = _read(
        _request(assets=(AssetId.BTC, AssetId.ETH), channels=("trade", "book")),
        _record(),
    )

    assert first.request_identity == second.request_identity


@pytest.mark.parametrize(
    "changed_request",
    [
        _request(cutoff=51),
        _request(axis=SelectionAxis.EVENT_TIME),
        _request(ordering=ReplayOrdering.STRICT_EVENT),
        _request(assets=None),
        _request(channels=None),
    ],
)
def test_semantic_request_change_changes_request_identity(changed_request: AsOfRequest) -> None:
    baseline = _read(_request(), _record())
    changed = _read(changed_request, _record())

    assert baseline.request_identity != changed.request_identity


def test_page_size_does_not_change_request_or_snapshot_identity() -> None:
    records = (_record("capture-1"), _record("capture-2", received_timestamp=21))

    small = _read(_request(page_size=1), *records)
    large = _read(_request(page_size=2), *records)

    assert small.request_identity == large.request_identity
    assert small.source_snapshot_identity == large.source_snapshot_identity


@pytest.mark.parametrize(
    ("evidence", "authority", "exclusion"),
    [
        (
            AvailabilityEvidence(51, "evidence-1"),
            AvailabilityEvidence(40, "authority-1"),
            "evidence_not_available_by_cutoff",
        ),
        (
            AvailabilityEvidence(30, "evidence-1"),
            AvailabilityEvidence(51, "authority-1"),
            "authority_not_available_by_cutoff",
        ),
        (AvailabilityEvidence(None, None), AvailabilityEvidence(40, "authority-1"), "evidence_not_available_by_cutoff"),
        (AvailabilityEvidence(30, "evidence-1"), AvailabilityEvidence(None, None), "authority_not_available_by_cutoff"),
    ],
)
def test_unavailable_evidence_or_authority_is_a_bounded_exclusion(
    evidence: AvailabilityEvidence,
    authority: AvailabilityEvidence,
    exclusion: str,
) -> None:
    view = _read(_request(), _record(evidence=evidence, authority=authority))

    assert view.records == ()
    assert [item.code.value for item in view.exclusions] == [exclusion]


@pytest.mark.parametrize(
    "evidence,authority",
    [
        (AvailabilityEvidence(30, None), AvailabilityEvidence(40, "authority-1")),
        (AvailabilityEvidence(None, "evidence-1"), AvailabilityEvidence(40, "authority-1")),
        (AvailabilityEvidence(30, "evidence-1"), AvailabilityEvidence(40, None)),
    ],
)
def test_partial_availability_fails_closed(
    evidence: AvailabilityEvidence,
    authority: AvailabilityEvidence,
) -> None:
    with pytest.raises(ReplayAsOfError) as error:
        _read(_request(), _record(evidence=evidence, authority=authority))

    assert error.value.code is ReplayErrorCode.AVAILABILITY_EVIDENCE_MISSING


def test_event_selection_fails_for_qualified_null_provider_time_before_window() -> None:
    with pytest.raises(ReplayAsOfError) as error:
        _read(
            _request(axis=SelectionAxis.EVENT_TIME, start=100, end=200),
            _record(provider_timestamp=None),
        )

    assert error.value.code is ReplayErrorCode.UNSUPPORTED_EVENT_TIME


def test_arrival_selection_accepts_null_provider_time_but_strict_event_order_does_not() -> None:
    record = _record(provider_timestamp=None)

    arrival = _read(_request(), record)

    assert [item.capture_fact.capture_id for item in arrival.records] == ["capture-1"]
    with pytest.raises(ReplayAsOfError) as error:
        _read(_request(ordering=ReplayOrdering.STRICT_EVENT), record)
    assert error.value.code is ReplayErrorCode.UNSUPPORTED_EVENT_TIME


def test_arrival_and_event_selection_are_half_open_and_independent_of_ordering() -> None:
    record = _record(provider_timestamp=10, received_timestamp=20)

    arrival = _read(
        _request(start=20, end=21, ordering=ReplayOrdering.STRICT_EVENT), record
    )
    event = _read(
        _request(axis=SelectionAxis.EVENT_TIME, start=10, end=11), record
    )
    excluded_arrival = _read(_request(start=21, end=22), record)

    assert [item.capture_fact.capture_id for item in arrival.records] == ["capture-1"]
    assert [item.capture_fact.capture_id for item in event.records] == ["capture-1"]
    assert excluded_arrival.records == ()


@pytest.mark.parametrize("category", list(TruthDecisionCategory))
def test_every_valid_truth_decision_category_is_replayable(
    category: TruthDecisionCategory,
) -> None:
    view = _read(_request(), _record(category=category))

    assert view.records[0].truth_decision.category is category


def test_ordering_uses_capture_id_ties_and_never_source_input_order() -> None:
    later = _record("capture-b", provider_timestamp=10, received_timestamp=20)
    earlier = _record("capture-a", provider_timestamp=10, received_timestamp=20)

    arrival = _read(_request(), later, earlier)
    strict_event = _read(_request(ordering=ReplayOrdering.STRICT_EVENT), later, earlier)

    assert [item.capture_fact.capture_id for item in arrival.records] == ["capture-a", "capture-b"]
    assert [item.capture_fact.capture_id for item in strict_event.records] == ["capture-a", "capture-b"]


def test_mismatched_fact_and_decision_subject_fails_closed() -> None:
    record = _record()
    mismatched = TruthDecision(
        "other-capture",
        TruthDecisionCategory.ACCEPTED,
        "data-truth/v1",
        ("other-capture",),
        None,
        None,
    )

    with pytest.raises(ReplayAsOfError) as error:
        _read(
            _request(),
            ReplaySourceRecord(
                record.capture_fact,
                mismatched,
                record.evidence_availability,
                record.authority_availability,
            ),
        )

    assert error.value.code is ReplayErrorCode.MALFORMED_AUTHORITY


def test_snapshot_identity_is_stable_across_input_order_and_changes_with_source_identity() -> None:
    records = (_record("capture-b"), _record("capture-a"))
    first = _read(_request(), *records)
    reordered = _read(_request(), *reversed(records))
    changed_source = ReplayAsOf(
        InMemoryReplaySource(
            list(records),
            SourceAuthorityIdentities("evidence/v2", "truth/v1", "availability/v1"),
        ),
        max_page_size=20,
    ).read(_request())

    assert first.source_snapshot_identity == reordered.source_snapshot_identity
    assert first.source_snapshot_identity != changed_source.source_snapshot_identity


def test_membership_change_changes_snapshot_identity() -> None:
    baseline = _read(_request(), _record("capture-a"))
    expanded = _read(_request(), _record("capture-a"), _record("capture-b"))

    assert baseline.source_snapshot_identity != expanded.source_snapshot_identity


def test_cursor_continues_by_keyset_with_changed_page_size_without_loss_or_duplication() -> None:
    records = (
        _record("capture-a", received_timestamp=20),
        _record("capture-b", received_timestamp=20),
        _record("capture-c", received_timestamp=21),
    )
    first = _read(_request(page_size=1), *records)
    second = _read(_request(page_size=2, cursor=first.next_cursor), *records)

    assert [item.capture_fact.capture_id for item in first.records] == ["capture-a"]
    assert [item.capture_fact.capture_id for item in second.records] == ["capture-b", "capture-c"]
    assert first.request_identity == second.request_identity
    assert first.source_snapshot_identity == second.source_snapshot_identity
    assert second.next_cursor is None


@pytest.mark.parametrize("cursor", ["not base64", _encode_cursor({"version": "wrong"})])
def test_malformed_or_wrong_version_cursor_is_invalid(cursor: str) -> None:
    with pytest.raises(ReplayAsOfError) as error:
        _read(_request(cursor=cursor), _record())

    assert error.value.code is ReplayErrorCode.INVALID_CURSOR


def test_cursor_for_different_semantic_request_is_rejected_as_mismatch() -> None:
    records = (_record("capture-a"), _record("capture-b", received_timestamp=21))
    first = _read(_request(page_size=1), *records)

    with pytest.raises(ReplayAsOfError) as error:
        _read(_request(cutoff=51, page_size=1, cursor=first.next_cursor), *records)

    assert error.value.code is ReplayErrorCode.CURSOR_MISMATCH


@pytest.mark.parametrize(
    "authorities,records",
    [
        (
            SourceAuthorityIdentities("evidence/v2", "truth/v1", "availability/v1"),
            (_record("capture-a"), _record("capture-b", received_timestamp=21)),
        ),
        (
            SourceAuthorityIdentities("evidence/v1", "truth/v1", "availability/v1"),
            (
                _record("capture-a"),
                _record("capture-b", received_timestamp=21),
                _record("capture-c", received_timestamp=22),
            ),
        ),
    ],
)
def test_source_authority_or_membership_drift_fails_closed(
    authorities: SourceAuthorityIdentities,
    records: tuple[ReplaySourceRecord, ...],
) -> None:
    original = (_record("capture-a"), _record("capture-b", received_timestamp=21))
    first = _read(_request(page_size=1), *original)
    drifted = ReplayAsOf(InMemoryReplaySource(list(records), authorities), max_page_size=20)

    with pytest.raises(ReplayAsOfError) as error:
        drifted.read(_request(page_size=1, cursor=first.next_cursor))

    assert error.value.code is ReplayErrorCode.SOURCE_UNAVAILABLE


def test_cursor_with_wrong_ordering_or_unknown_last_key_is_invalid() -> None:
    record = _record("capture-a")
    baseline = _read(_request(), record)
    wrong_ordering = _encode_cursor(
        {
            "version": "replay-as-of-cursor/v1",
            "request_identity": baseline.request_identity,
            "source_snapshot_identity": baseline.source_snapshot_identity,
            "ordering": "strict_event",
            "last_key": [20, "capture-a"],
        }
    )
    unknown_key = _encode_cursor(
        {
            "version": "replay-as-of-cursor/v1",
            "request_identity": baseline.request_identity,
            "source_snapshot_identity": baseline.source_snapshot_identity,
            "ordering": "arrival",
            "last_key": [20, "missing"],
        }
    )

    for cursor in (wrong_ordering, unknown_key):
        with pytest.raises(ReplayAsOfError) as error:
            _read(_request(cursor=cursor), record)
        assert error.value.code is ReplayErrorCode.INVALID_CURSOR


def test_cursor_with_wrong_key_component_type_is_invalid() -> None:
    record = _record("capture-a")
    baseline = _read(_request(), record)
    cursor = _encode_cursor(
        {
            "version": "replay-as-of-cursor/v1",
            "request_identity": baseline.request_identity,
            "source_snapshot_identity": baseline.source_snapshot_identity,
            "ordering": "arrival",
            "last_key": ["not-an-int", "capture-a"],
        }
    )

    with pytest.raises(ReplayAsOfError) as error:
        _read(_request(cursor=cursor), record)

    assert error.value.code is ReplayErrorCode.INVALID_CURSOR
