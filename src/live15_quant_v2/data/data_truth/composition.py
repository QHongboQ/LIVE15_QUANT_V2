"""Provider-neutral parent composition for Slice 1 Data Truth decisions."""

from live15_quant_v2.data.data_truth.event_facts import EventFacts
from live15_quant_v2.data.data_truth.history import (
    TruthDecisionAppendInDoubtError,
    TruthDecisionHistory,
    TruthDecisionInvariantError,
    TruthDecisionVerificationError,
)
from live15_quant_v2.data.data_truth.models import TruthDecision
from live15_quant_v2.data.data_truth.observation_facts import ObservationFacts
from live15_quant_v2.data.storage.capture import CaptureFact

_POLICY_VERSION = "data-truth/v1"
_OBSERVATION_MESSAGE_TYPES = frozenset(
    {
        "orderbook_snapshot",
        "orderbook_delta",
        "ticker",
        "market_lifecycle_v2",
        "event_fee_update",
        "cfbenchmarks_value",
        "pyth_value",
    }
)


class UnsupportedDataTruthInputError(ValueError):
    """Raised when V1 has no approved semantic owner for a capture family."""


class DataTruth:
    """Route immutable CaptureFact evidence into verified append-only decisions."""

    def __init__(self, history: TruthDecisionHistory) -> None:
        self._history = history
        self._event_facts = EventFacts()
        self._observation_facts = ObservationFacts()

    def decide(self, fact: CaptureFact) -> TruthDecision:
        """Return only a history-verified authority decision for one evidence fact."""
        existing = self._history.find_subject_decision(_POLICY_VERSION, fact.capture_id)
        if existing is not None:
            return self._require_subject(existing, fact.capture_id)

        candidate = self._candidate(fact)
        return self._append_and_verify(candidate)

    def _candidate(self, fact: CaptureFact) -> TruthDecision:
        if fact.message_type == "trade":
            event_identity = self._event_facts.event_identity_or_not_accepted(fact)
            if isinstance(event_identity, TruthDecision):
                return event_identity
            anchor = self._history.find_accepted_event(event_identity)
            if anchor is not None and anchor.accepted_fact.capture_id == fact.capture_id:
                raise TruthDecisionInvariantError(
                    "accepted event anchor contradicts missing subject authority"
                )
            return self._event_facts.decide(fact, anchor)
        if fact.message_type in _OBSERVATION_MESSAGE_TYPES:
            return self._observation_facts.decide(fact)
        raise UnsupportedDataTruthInputError("unsupported Data Truth capture message type")

    def _append_and_verify(self, candidate: TruthDecision) -> TruthDecision:
        try:
            self._history.append(candidate)
        except TruthDecisionAppendInDoubtError as error:
            persisted = self._history.find_subject_decision(
                candidate.policy_version, candidate.subject_capture_id
            )
            if persisted is None:
                raise TruthDecisionAppendInDoubtError(
                    "TruthDecision append remains in doubt after reconciliation"
                ) from error
            return self._require_exact(candidate, persisted)

        persisted = self._history.find_subject_decision(
            candidate.policy_version, candidate.subject_capture_id
        )
        if persisted is None:
            raise TruthDecisionVerificationError(
                "TruthDecision append was not visible through same-authority verification"
            )
        return self._require_exact(candidate, persisted)

    @staticmethod
    def _require_subject(decision: TruthDecision, capture_id: str) -> TruthDecision:
        if (
            decision.policy_version != _POLICY_VERSION
            or decision.subject_capture_id != capture_id
        ):
            raise TruthDecisionInvariantError("history returned a mismatched subject decision")
        return decision

    @staticmethod
    def _require_exact(candidate: TruthDecision, persisted: TruthDecision) -> TruthDecision:
        if persisted != candidate:
            raise TruthDecisionVerificationError(
                "TruthDecision history did not return the exact persisted authority"
            )
        return persisted
