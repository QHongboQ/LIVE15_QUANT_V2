from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import cast

import pytest

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.data_truth import TruthDecisionAppendInDoubtError
from live15_quant_v2.data.data_truth.composition import DataTruth
from live15_quant_v2.data.data_truth.models import (
    TruthDecision,
    TruthDecisionCategory,
)
from live15_quant_v2.data.recorder_composition import RecorderComposition
from live15_quant_v2.data.replay_as_of import (
    AsOfRequest,
    ReplayAsOf,
    ReplayOrdering,
    SelectionAxis,
    SelectionWindow,
)
from live15_quant_v2.data.replay_as_of.availability import (
    SUPPORTED_PROOF_SCHEMA_VERSION,
    AvailabilityKind,
    AvailabilityRecord,
    AvailabilitySupportError,
    AvailabilitySupportErrorCode,
    AvailabilityWriter,
)
from live15_quant_v2.data.replay_as_of.models import AvailabilityReference
from live15_quant_v2.data.replay_as_of.source import (
    InMemoryReplaySource,
    ReplaySourceRecord,
    SourceAuthorityIdentities,
)
from live15_quant_v2.data.storage.capture import CaptureFact
from live15_quant_v2.data.storage.capture_boundary import CaptureBoundary
from live15_quant_v2.data.storage.durable_persistence import (
    PersistenceResult,
    PersistenceStatus,
)
from live15_quant_v2.data.storage.hot_store.port import HotStore


def _fact(capture_id: str = "capture-1") -> CaptureFact:
    return CaptureFact(
        capture_id,
        AssetId.BTC,
        "kalshi",
        "KXBTC",
        "trade",
        "trade",
        None,
        1,
        None,
        1,
        2,
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


class _Boundary:
    def __init__(
        self,
        fact: CaptureFact,
        calls: list[str],
        *,
        market_error: Exception | None = None,
    ) -> None:
        self._fact = fact
        self._calls = calls
        self._market_error = market_error

    def capture_market(self, identity: object, message: object) -> CaptureFact:
        del identity, message
        self._calls.append("capture_market")
        if self._market_error is not None:
            raise self._market_error
        return self._fact

    def capture_reference(self, message: object) -> CaptureFact:
        del message
        self._calls.append("capture_reference")
        return self._fact


class _Persistence:
    def __init__(self, calls: list[str], status: PersistenceStatus) -> None:
        self._calls = calls
        self._status = status

    def persist(self, fact: CaptureFact) -> PersistenceResult:
        self._calls.append("persist")
        return PersistenceResult(self._status)


class _HotStore:
    def __init__(
        self,
        result: CaptureFact | None,
        calls: list[str],
        *,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._calls = calls
        self._error = error

    def read_capture(self, capture_id: str) -> CaptureFact | None:
        self._calls.append(f"read_back:{capture_id}")
        if self._error is not None:
            raise self._error
        return self._result


class _AvailabilityWriter:
    def __init__(
        self,
        calls: list[str],
        *,
        errors: dict[AvailabilityKind, Exception] | None = None,
    ) -> None:
        self._calls = calls
        self._errors = errors or {}
        self.requests: list[tuple[AvailabilityKind, str, str | None, str]] = []

    def record_proven(
        self,
        *,
        kind: AvailabilityKind,
        capture_id: str,
        policy_version: str | None,
        source_authority_identity: str,
    ) -> AvailabilityRecord:
        self._calls.append(f"{kind.value}_marker")
        self.requests.append(
            (kind, capture_id, policy_version, source_authority_identity)
        )
        if kind in self._errors:
            raise self._errors[kind]
        return AvailabilityRecord(
            kind,
            capture_id,
            policy_version,
            10 if kind is AvailabilityKind.EVIDENCE else 11,
            SUPPORTED_PROOF_SCHEMA_VERSION,
            source_authority_identity,
        )


class _DataTruth:
    def __init__(
        self,
        calls: list[str],
        fact: CaptureFact,
        *,
        error: Exception | None = None,
    ) -> None:
        self._calls = calls
        self._fact = fact
        self._error = error

    def decide(self, fact: CaptureFact) -> TruthDecision:
        assert fact == self._fact
        self._calls.append("data_truth")
        if self._error is not None:
            raise self._error
        return _decision(fact)


def _composition(
    calls: list[str],
    *,
    fact: CaptureFact | None = None,
    status: PersistenceStatus = PersistenceStatus.ACKNOWLEDGED_OK,
    read_back: CaptureFact | None | object = ...,
    capture_error: Exception | None = None,
    hot_store_error: Exception | None = None,
    writer_errors: dict[AvailabilityKind, Exception] | None = None,
    truth_error: Exception | None = None,
) -> tuple[RecorderComposition, _AvailabilityWriter]:

    actual_fact = fact or _fact()
    stored = actual_fact if read_back is ... else cast(CaptureFact | None, read_back)
    writer = _AvailabilityWriter(calls, errors=writer_errors)
    return (
        RecorderComposition(
            capture_boundary=cast(
                CaptureBoundary,
                _Boundary(actual_fact, calls, market_error=capture_error),
            ),
            durable_persistence=_Persistence(calls, status),
            hot_store=cast(HotStore, _HotStore(stored, calls, error=hot_store_error)),
            availability_writer=cast(AvailabilityWriter, writer),
            data_truth=cast(DataTruth, _DataTruth(calls, actual_fact, error=truth_error)),
            evidence_authority_identity="test-evidence-authority/v1",
            truth_decision_authority_identity="test-truth-authority/v1",
        ),
        writer,
    )


def test_market_capture_persists_proves_and_records_authority_in_order() -> None:
    calls: list[str] = []
    composition, writer = _composition(calls)

    result = composition.record_market(object(), object())

    assert calls == [
        "capture_market",
        "persist",
        "read_back:capture-1",
        "evidence_marker",
        "data_truth",
        "authority_marker",
    ]
    assert writer.requests == [
        (AvailabilityKind.EVIDENCE, "capture-1", None, "test-evidence-authority/v1"),
        (
            AvailabilityKind.AUTHORITY,
            "capture-1",
            "data-truth/v1",
            "test-truth-authority/v1",
        ),
    ]
    assert result.capture_fact == _fact()
    assert result.persistence_result == PersistenceResult(PersistenceStatus.ACKNOWLEDGED_OK)
    assert result.evidence_proven is True
    assert result.truth_decision == _decision(_fact())
    assert result.evidence_availability is not None
    assert result.authority_availability is not None
    with pytest.raises(FrozenInstanceError):
        result.evidence_proven = False  # type: ignore[misc]


@pytest.mark.parametrize(
    "status",
    [
        PersistenceStatus.LOCAL_PERSISTENCE_FAILED,
        PersistenceStatus.DEFINITELY_REJECTED,
    ],
)
def test_terminal_persistence_status_stops_before_readback(status: PersistenceStatus) -> None:
    calls: list[str] = []
    composition, _ = _composition(calls, status=status)

    result = composition.record_market(object(), object())

    assert calls == ["capture_market", "persist"]
    assert result.persistence_result == PersistenceResult(status)
    assert result.evidence_proven is False
    assert result.truth_decision is None


def test_capture_boundary_error_propagates_unchanged_without_persistence() -> None:
    calls: list[str] = []
    error = RuntimeError("capture authority failed")
    composition, _ = _composition(calls, capture_error=error)

    with pytest.raises(RuntimeError, match="capture authority failed") as raised:
        composition.record_market(object(), object())

    assert raised.value is error
    assert calls == ["capture_market"]


@pytest.mark.parametrize(
    "status",
    [
        PersistenceStatus.PERSISTED_PENDING,
        PersistenceStatus.ACKNOWLEDGED_OK,
        PersistenceStatus.IN_DOUBT,
    ],
)
def test_nonterminal_persistence_without_exact_readback_stops_normally(
    status: PersistenceStatus,
) -> None:
    calls: list[str] = []
    composition, _ = _composition(calls, status=status, read_back=None)

    result = composition.record_market(object(), object())

    assert calls == ["capture_market", "persist", "read_back:capture-1"]
    assert result.persistence_result == PersistenceResult(status)
    assert result.evidence_proven is False
    assert result.evidence_availability is None
    assert result.truth_decision is None


def test_mismatched_readback_raises_before_availability_or_truth() -> None:
    from live15_quant_v2.data.recorder_composition import (
        RecorderCompositionInvariantError,
    )

    calls: list[str] = []
    composition, _ = _composition(calls, read_back=_fact("other-capture"))

    with pytest.raises(RecorderCompositionInvariantError):
        composition.record_market(object(), object())

    assert calls == ["capture_market", "persist", "read_back:capture-1"]


def test_hot_store_error_propagates_unchanged_without_lower_calls() -> None:
    calls: list[str] = []
    error = RuntimeError("hot-store unavailable")
    composition, _ = _composition(calls, hot_store_error=error)

    with pytest.raises(RuntimeError, match="hot-store unavailable") as raised:
        composition.record_market(object(), object())

    assert raised.value is error
    assert calls == ["capture_market", "persist", "read_back:capture-1"]


@pytest.mark.parametrize("code", list(AvailabilitySupportErrorCode))
def test_evidence_marker_failure_is_reported_and_truth_still_progresses(
    code: AvailabilitySupportErrorCode,
) -> None:
    calls: list[str] = []
    composition, _ = _composition(
        calls,
        writer_errors={
            AvailabilityKind.EVIDENCE: AvailabilitySupportError(code, "controlled")
        },
    )

    result = composition.record_market(object(), object())

    assert calls == [
        "capture_market",
        "persist",
        "read_back:capture-1",
        "evidence_marker",
        "data_truth",
        "authority_marker",
    ]
    assert result.evidence_proven is True
    assert result.evidence_availability is None
    assert result.evidence_availability_error is code
    assert result.truth_decision == _decision(_fact())
    assert result.authority_availability is not None


@pytest.mark.parametrize("code", list(AvailabilitySupportErrorCode))
def test_authority_marker_failure_is_reported_without_rollback(
    code: AvailabilitySupportErrorCode,
) -> None:
    calls: list[str] = []
    composition, _ = _composition(
        calls,
        writer_errors={
            AvailabilityKind.AUTHORITY: AvailabilitySupportError(code, "controlled")
        },
    )

    result = composition.record_market(object(), object())

    assert calls[-3:] == ["evidence_marker", "data_truth", "authority_marker"]
    assert result.evidence_availability is not None
    assert result.truth_decision == _decision(_fact())
    assert result.authority_availability is None
    assert result.authority_availability_error is code


def test_unrelated_availability_error_propagates_without_data_truth() -> None:
    calls: list[str] = []
    error = RuntimeError("availability implementation failed")
    composition, _ = _composition(
        calls,
        writer_errors={AvailabilityKind.EVIDENCE: error},
    )

    with pytest.raises(RuntimeError, match="availability implementation failed") as raised:
        composition.record_market(object(), object())

    assert raised.value is error
    assert calls == [
        "capture_market",
        "persist",
        "read_back:capture-1",
        "evidence_marker",
    ]


def test_data_truth_error_propagates_and_prevents_authority_marker() -> None:
    calls: list[str] = []
    error = TruthDecisionAppendInDoubtError("controlled truth ambiguity")
    composition, _ = _composition(calls, truth_error=error)

    with pytest.raises(TruthDecisionAppendInDoubtError) as raised:
        composition.record_market(object(), object())

    assert raised.value is error
    assert calls == [
        "capture_market",
        "persist",
        "read_back:capture-1",
        "evidence_marker",
        "data_truth",
    ]


def test_reference_entry_and_explicit_recovery_use_only_the_authorized_sequence() -> None:
    calls: list[str] = []
    composition, _ = _composition(calls)

    reference = composition.record_reference(object())
    recovered = composition.recover_fact(_fact())

    assert reference.persistence_result == PersistenceResult(PersistenceStatus.ACKNOWLEDGED_OK)
    assert recovered.persistence_result is None
    assert calls == [
        "capture_reference",
        "persist",
        "read_back:capture-1",
        "evidence_marker",
        "data_truth",
        "authority_marker",
        "read_back:capture-1",
        "evidence_marker",
        "data_truth",
        "authority_marker",
    ]


@pytest.mark.parametrize("identity", ["", 1, None])
def test_authority_identities_must_be_nonempty_text(identity: object) -> None:
    calls: list[str] = []
    with pytest.raises(ValueError):
        RecorderComposition(
            capture_boundary=cast(CaptureBoundary, _Boundary(_fact(), calls)),
            durable_persistence=_Persistence(calls, PersistenceStatus.ACKNOWLEDGED_OK),
            hot_store=cast(HotStore, _HotStore(_fact(), calls)),
            availability_writer=cast(AvailabilityWriter, _AvailabilityWriter(calls)),
            data_truth=cast(DataTruth, _DataTruth(calls, _fact())),
            evidence_authority_identity=cast(str, identity),
            truth_decision_authority_identity="truth/v1",
        )


def test_missing_evidence_marker_is_excluded_by_existing_replay_semantics() -> None:
    fact = _fact()
    record = ReplaySourceRecord(
        fact,
        _decision(fact),
        AvailabilityReference(None, None),
        AvailabilityReference(11, "authority-marker"),
    )
    source = InMemoryReplaySource(
        [record],
        SourceAuthorityIdentities("evidence/v1", "truth/v1", "availability/v1"),
    )
    request = AsOfRequest(
        20,
        "data-truth/v1",
        SelectionWindow(SelectionAxis.ARRIVAL_TIME, 0, 10),
        ReplayOrdering.ARRIVAL,
        (AssetId.BTC,),
        ("trade",),
        10,
        None,
    )

    view = ReplayAsOf(source, max_page_size=10).read(request)

    assert view.records == ()
    assert [exclusion.capture_id for exclusion in view.exclusions] == ["capture-1"]


def test_composition_has_no_provider_or_lower_level_implementation_dependency() -> None:
    source = Path("src/live15_quant_v2/data/recorder_composition.py").read_text(
        encoding="utf-8"
    )

    for prohibited in (
        "questdb",
        "QuestDB",
        "questdb_source",
        "recorder_composition import",
        "sql",
        "DDL",
        "sender",
        "time.sleep",
        "while True",
        "retry",
        "write_capture",
        "replay_as_of.service",
    ):
        assert prohibited not in source
