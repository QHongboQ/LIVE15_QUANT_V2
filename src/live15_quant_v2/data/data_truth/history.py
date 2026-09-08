"""The intentionally narrow provider-neutral TruthDecision history seam."""

from typing import Protocol

from live15_quant_v2.data.data_truth.models import (
    EventAnchor,
    EventIdentity,
    TruthDecision,
)


class TruthDecisionHistoryError(RuntimeError):
    """Base class for bounded history failures."""


class TruthDecisionAppendRejectedError(TruthDecisionHistoryError):
    """Raised when history definitely rejected an append."""


class TruthDecisionAppendInDoubtError(TruthDecisionHistoryError):
    """Raised when an append outcome cannot be determined."""


class TruthDecisionVerificationError(TruthDecisionHistoryError):
    """Raised when history cannot verify the required authoritative decision."""


class TruthDecisionInvariantError(TruthDecisionHistoryError):
    """Raised when history returns internally inconsistent authority."""


class TruthDecisionHistory(Protocol):
    """Append-only authority access required by Slice 1 composition."""

    def find_subject_decision(
        self, policy_version: str, capture_id: str
    ) -> TruthDecision | None:
        """Find the exact prior decision for one policy-versioned subject."""

    def find_accepted_event(self, event_identity: EventIdentity) -> EventAnchor | None:
        """Find the accepted anchor for one already-validated event identity."""

    def append(self, decision: TruthDecision) -> None:
        """Append a decision or raise a bounded history exception."""
