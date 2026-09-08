"""Provider-neutral immutable Data Truth semantic models."""

from dataclasses import dataclass
from enum import StrEnum

from live15_quant_v2.data.storage.capture import CaptureFact


class TruthDecisionCategory(StrEnum):
    """The complete V1 Data Truth decision vocabulary."""

    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"
    CONFLICT = "conflict"
    NOT_ACCEPTED = "not_accepted"


class TradeNotAcceptedReason(StrEnum):
    """The bounded V1 reasons for a Trade that cannot be accepted."""

    INVALID_TRADE_EVIDENCE = "invalid_trade_evidence"
    TRADE_IDENTITY_MISMATCH = "trade_identity_mismatch"
    UNSUPPORTED_TRADE_SCHEMA = "unsupported_trade_schema"


@dataclass(frozen=True, slots=True)
class EventIdentity:
    """Provider-owned logical identity for the currently supported Trade event."""

    provider: str
    source_id: str
    message_type: str
    trade_id: str


@dataclass(frozen=True, slots=True)
class SubjectDecisionKey:
    """Stable idempotency and reconciliation key for one subject decision."""

    policy_version: str
    subject_capture_id: str


@dataclass(frozen=True, slots=True)
class TruthDecision:
    """An immutable, auditable adjudication of one captured evidence record."""

    subject_capture_id: str
    category: TruthDecisionCategory
    policy_version: str
    contributing_capture_ids: tuple[str, ...]
    reason: TradeNotAcceptedReason | None
    event_identity: EventIdentity | None


@dataclass(frozen=True, slots=True)
class EventAnchor:
    """Resolved accepted evidence passed by composition into Event Facts."""

    event_identity: EventIdentity
    accepted_decision: TruthDecision
    accepted_fact: CaptureFact
