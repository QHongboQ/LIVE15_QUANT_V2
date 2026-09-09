"""Upper Data System composition for proven capture and authority recording."""

from __future__ import annotations

from dataclasses import dataclass

from live15_quant_v2.data.data_truth.composition import DataTruth
from live15_quant_v2.data.data_truth.models import TruthDecision
from live15_quant_v2.data.market_ingress.ingress_boundary import VerifiedMarketIdentity
from live15_quant_v2.data.replay_as_of.availability import (
    AvailabilityKind,
    AvailabilityRecord,
    AvailabilitySupportError,
    AvailabilitySupportErrorCode,
    AvailabilityWriter,
)
from live15_quant_v2.data.storage.capture import CaptureFact
from live15_quant_v2.data.storage.capture_boundary.boundary import CaptureBoundary
from live15_quant_v2.data.storage.durable_persistence import (
    DurablePersistence,
    PersistenceResult,
    PersistenceStatus,
)
from live15_quant_v2.data.storage.hot_store.port import HotStore


class RecorderCompositionInvariantError(RuntimeError):
    """Raised when a lower public seam contradicts immutable capture evidence."""


@dataclass(frozen=True, slots=True)
class RecorderCompositionResult:
    """Observable result of one bounded Recorder composition invocation."""

    capture_fact: CaptureFact
    persistence_result: PersistenceResult | None
    evidence_proven: bool
    evidence_availability: AvailabilityRecord | None
    evidence_availability_error: AvailabilitySupportErrorCode | None
    truth_decision: TruthDecision | None
    authority_availability: AvailabilityRecord | None
    authority_availability_error: AvailabilitySupportErrorCode | None


class RecorderComposition:
    """Sequence sealed public Data System responsibilities without replacing them."""

    def __init__(
        self,
        *,
        capture_boundary: CaptureBoundary,
        durable_persistence: DurablePersistence,
        hot_store: HotStore,
        availability_writer: AvailabilityWriter,
        data_truth: DataTruth,
        evidence_authority_identity: str,
        truth_decision_authority_identity: str,
    ) -> None:
        self._capture_boundary = capture_boundary
        self._durable_persistence = durable_persistence
        self._hot_store = hot_store
        self._availability_writer = availability_writer
        self._data_truth = data_truth
        self._evidence_authority_identity = _identity(evidence_authority_identity)
        self._truth_decision_authority_identity = _identity(
            truth_decision_authority_identity
        )

    def record_market(
        self, identity: VerifiedMarketIdentity, message: object
    ) -> RecorderCompositionResult:
        """Capture one typed market message, then progress only from public proof."""

        fact = self._capture_boundary.capture_market(identity, message)
        return self._persist_and_prove(fact)

    def record_reference(self, message: object) -> RecorderCompositionResult:
        """Capture one typed reference message, then progress only from public proof."""

        fact = self._capture_boundary.capture_reference(message)
        return self._persist_and_prove(fact)

    def recover_fact(self, fact: CaptureFact) -> RecorderCompositionResult:
        """Explicitly re-prove one immutable fact without repersisting it."""

        return self._prove_and_record(fact, None)

    def _persist_and_prove(self, fact: CaptureFact) -> RecorderCompositionResult:
        persistence_result = self._durable_persistence.persist(fact)
        if persistence_result.status in (
            PersistenceStatus.LOCAL_PERSISTENCE_FAILED,
            PersistenceStatus.DEFINITELY_REJECTED,
        ):
            return _result(fact, persistence_result)
        return self._prove_and_record(fact, persistence_result)

    def _prove_and_record(
        self, fact: CaptureFact, persistence_result: PersistenceResult | None
    ) -> RecorderCompositionResult:
        stored_fact = self._hot_store.read_capture(fact.capture_id)
        if stored_fact is None:
            return _result(fact, persistence_result)
        if stored_fact != fact:
            raise RecorderCompositionInvariantError(
                "Hot Store read-back did not return the exact immutable CaptureFact"
            )

        evidence, evidence_error = self._record_availability(
            AvailabilityKind.EVIDENCE,
            fact.capture_id,
            None,
            self._evidence_authority_identity,
        )
        decision = self._data_truth.decide(fact)
        authority, authority_error = self._record_availability(
            AvailabilityKind.AUTHORITY,
            decision.subject_capture_id,
            decision.policy_version,
            self._truth_decision_authority_identity,
        )
        return RecorderCompositionResult(
            fact,
            persistence_result,
            True,
            evidence,
            evidence_error,
            decision,
            authority,
            authority_error,
        )

    def _record_availability(
        self,
        kind: AvailabilityKind,
        capture_id: str,
        policy_version: str | None,
        source_authority_identity: str,
    ) -> tuple[AvailabilityRecord | None, AvailabilitySupportErrorCode | None]:
        try:
            return (
                self._availability_writer.record_proven(
                    kind=kind,
                    capture_id=capture_id,
                    policy_version=policy_version,
                    source_authority_identity=source_authority_identity,
                ),
                None,
            )
        except AvailabilitySupportError as error:
            return None, error.code


def _identity(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("authority identity must be non-empty text")
    return value


def _result(
    fact: CaptureFact, persistence_result: PersistenceResult | None
) -> RecorderCompositionResult:
    return RecorderCompositionResult(
        fact,
        persistence_result,
        False,
        None,
        None,
        None,
        None,
        None,
    )
