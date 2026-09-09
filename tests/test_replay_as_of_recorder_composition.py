from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import cast

import pytest

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.data_truth import (
    TruthDecisionAppendInDoubtError,
    TruthDecisionAppendRejectedError,
    TruthDecisionInvariantError,
    TruthDecisionVerificationError,
    UnsupportedDataTruthInputError,
)
from live15_quant_v2.data.data_truth.composition import DataTruth
from live15_quant_v2.data.data_truth.models import (
    TruthDecision,
    TruthDecisionCategory,
)
from live15_quant_v2.data.market_ingress.ingress_boundary import VerifiedMarketIdentity
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
    AvailabilityKey,
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


class _ControlledAvailabilityStore:
    """External availability boundary controlled only at its public store seam."""

    def __init__(
        self,
        calls: list[str],
        *,
        append_errors: dict[AvailabilityKind, AvailabilitySupportError] | None = None,
    ) -> None:
        self._calls = calls
        self._append_errors = append_errors or {}
        self.visible: dict[AvailabilityKey, AvailabilityRecord] = {}
        self.attempted: dict[AvailabilityKey, AvailabilityRecord] = {}
        self.append_count: dict[AvailabilityKey, int] = {}

    def find(self, key: AvailabilityKey) -> AvailabilityRecord | None:
        self._calls.append(f"find:{key.kind.value}")
        return self.visible.get(key)

    def read_committed_floor(self) -> int | None:
        self._calls.append("read_floor")
        return None

    def append(self, record: AvailabilityRecord) -> AvailabilityRecord:
        self._calls.append(f"append:{record.kind.value}")
        self.attempted[record.key] = record
        self.append_count[record.key] = self.append_count.get(record.key, 0) + 1
        error = self._append_errors.get(record.kind)
        if error is not None:
            raise error
        self.visible[record.key] = record
        return record

    def set_append_error(
        self, kind: AvailabilityKind, error: AvailabilitySupportError | None
    ) -> None:
        if error is None:
            self._append_errors.pop(kind, None)
        else:
            self._append_errors[kind] = error


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


def _real_writer_composition(
    calls: list[str],
    *,
    store: _ControlledAvailabilityStore,
    fact: CaptureFact | None = None,
    truth_error: Exception | None = None,
) -> RecorderComposition:
    actual_fact = fact or _fact()
    return RecorderComposition(
        capture_boundary=cast(CaptureBoundary, _Boundary(actual_fact, calls)),
        durable_persistence=_Persistence(calls, PersistenceStatus.ACKNOWLEDGED_OK),
        hot_store=cast(HotStore, _HotStore(actual_fact, calls)),
        availability_writer=AvailabilityWriter(
            store,
            wall_time_ns=lambda: 1_000,
            monotonic_ns=iter(range(100)).__next__,
        ),
        data_truth=cast(DataTruth, _DataTruth(calls, actual_fact, error=truth_error)),
        evidence_authority_identity="test-evidence-authority/v1",
        truth_decision_authority_identity="test-truth-authority/v1",
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


def test_same_id_readback_with_different_immutable_payload_is_rejected() -> None:
    from live15_quant_v2.data.recorder_composition import (
        RecorderCompositionInvariantError,
    )

    calls: list[str] = []
    composition, _ = _composition(calls, read_back=replace(_fact(), payload="changed"))

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


def test_real_writer_evidence_in_doubt_never_blindly_reappends_and_reconciles() -> None:
    calls: list[str] = []
    in_doubt = AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "controlled")
    store = _ControlledAvailabilityStore(
        calls,
        append_errors={AvailabilityKind.EVIDENCE: in_doubt},
    )
    composition = _real_writer_composition(calls, store=store)
    calls.clear()

    first = composition.record_market(cast(VerifiedMarketIdentity, object()), object())
    evidence_key = AvailabilityKey(AvailabilityKind.EVIDENCE, "capture-1", None)
    evidence_candidate = store.attempted[evidence_key]
    before_recovery = store.append_count[evidence_key]
    assert first.evidence_availability_error is AvailabilitySupportErrorCode.IN_DOUBT
    calls.clear()

    unresolved = composition.recover_fact(_fact())

    assert calls[:2] == ["read_back:capture-1", "find:evidence"]
    assert unresolved.evidence_proven is True
    assert unresolved.evidence_availability_error is AvailabilitySupportErrorCode.IN_DOUBT
    assert store.append_count[evidence_key] == before_recovery

    store.visible[evidence_key] = evidence_candidate
    calls.clear()
    reconciled = composition.recover_fact(_fact())

    assert calls[:2] == ["read_back:capture-1", "find:evidence"]
    assert reconciled.evidence_availability == evidence_candidate
    assert store.append_count[evidence_key] == before_recovery


def test_real_writer_authority_in_doubt_never_blindly_reappends_and_reconciles() -> None:
    calls: list[str] = []
    in_doubt = AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "controlled")
    store = _ControlledAvailabilityStore(
        calls,
        append_errors={AvailabilityKind.AUTHORITY: in_doubt},
    )
    composition = _real_writer_composition(calls, store=store)
    calls.clear()

    first = composition.record_market(cast(VerifiedMarketIdentity, object()), object())
    authority_key = AvailabilityKey(
        AvailabilityKind.AUTHORITY, "capture-1", "data-truth/v1"
    )
    authority_candidate = store.attempted[authority_key]
    before_recovery = store.append_count[authority_key]
    assert first.authority_availability_error is AvailabilitySupportErrorCode.IN_DOUBT
    calls.clear()

    unresolved = composition.recover_fact(_fact())

    assert calls[:2] == ["read_back:capture-1", "find:evidence"]
    assert unresolved.authority_availability_error is AvailabilitySupportErrorCode.IN_DOUBT
    assert store.append_count[authority_key] == before_recovery

    store.visible[authority_key] = authority_candidate
    calls.clear()
    reconciled = composition.recover_fact(_fact())

    assert calls[:2] == ["read_back:capture-1", "find:evidence"]
    assert reconciled.authority_availability == authority_candidate
    assert store.append_count[authority_key] == before_recovery


def test_real_writer_definite_evidence_failure_allows_one_explicit_recovery_attempt() -> None:
    calls: list[str] = []
    store = _ControlledAvailabilityStore(
        calls,
        append_errors={
            AvailabilityKind.EVIDENCE: AvailabilitySupportError(
                AvailabilitySupportErrorCode.DEFINITE_PREPUBLICATION_FAILURE,
                "controlled",
            )
        },
    )
    composition = _real_writer_composition(calls, store=store)
    calls.clear()

    first = composition.record_market(cast(VerifiedMarketIdentity, object()), object())
    evidence_key = AvailabilityKey(AvailabilityKind.EVIDENCE, "capture-1", None)
    assert first.evidence_availability_error is (
        AvailabilitySupportErrorCode.DEFINITE_PREPUBLICATION_FAILURE
    )
    assert store.append_count[evidence_key] == 1
    store.set_append_error(AvailabilityKind.EVIDENCE, None)
    calls.clear()

    recovered = composition.recover_fact(_fact())

    assert calls[:3] == [
        "read_back:capture-1",
        "find:evidence",
        "append:evidence",
    ]
    assert recovered.evidence_availability is not None
    assert store.append_count[evidence_key] == 2


def test_cross_restart_marker_ambiguity_is_not_automatically_retried() -> None:
    """A restarted writer is inert until an upper caller supplies new proof."""

    calls: list[str] = []
    store = _ControlledAvailabilityStore(calls)
    _real_writer_composition(calls, store=store)

    assert store.append_count == {}


@pytest.mark.parametrize(
    "error",
    [
        TruthDecisionAppendRejectedError("rejected"),
        TruthDecisionAppendInDoubtError("in doubt"),
        TruthDecisionVerificationError("verification"),
        TruthDecisionInvariantError("invariant"),
        UnsupportedDataTruthInputError("unsupported"),
    ],
)
def test_data_truth_error_propagates_and_prevents_authority_marker(
    error: Exception,
) -> None:
    calls: list[str] = []
    composition, _ = _composition(calls, truth_error=error)

    with pytest.raises(type(error)) as raised:
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


@pytest.mark.parametrize(
    "missing_kind",
    [AvailabilityKind.EVIDENCE, AvailabilityKind.AUTHORITY],
)
def test_replay_excludes_marker_failure_from_actual_composition_result(
    missing_kind: AvailabilityKind,
) -> None:
    calls: list[str] = []
    store = _ControlledAvailabilityStore(
        calls,
        append_errors={
            missing_kind: AvailabilitySupportError(
                AvailabilitySupportErrorCode.DEFINITE_REJECTION,
                "controlled",
            )
        },
    )
    composition = _real_writer_composition(calls, store=store)
    result = composition.record_market(cast(VerifiedMarketIdentity, object()), object())
    assert result.truth_decision is not None

    def reference(record: AvailabilityRecord | None) -> AvailabilityReference:
        if record is None:
            return AvailabilityReference(None, None)
        return AvailabilityReference(record.available_at_ns, record.kind.value)

    source = InMemoryReplaySource(
        [
            ReplaySourceRecord(
                result.capture_fact,
                result.truth_decision,
                reference(result.evidence_availability),
                reference(result.authority_availability),
            )
        ],
        SourceAuthorityIdentities("evidence/v1", "truth/v1", "availability/v1"),
    )
    request = AsOfRequest(
        2_000,
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
