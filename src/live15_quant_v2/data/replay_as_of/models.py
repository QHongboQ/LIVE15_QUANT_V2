"""Provider-neutral immutable values for Replay & As-Of Slice 1."""

from dataclasses import dataclass
from enum import StrEnum

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.data_truth.models import TruthDecision
from live15_quant_v2.data.storage.capture import CaptureFact


class SelectionAxis(StrEnum):
    """The timestamp axis used to select evidence."""

    ARRIVAL_TIME = "arrival_time"
    EVENT_TIME = "event_time"


class ReplayOrdering(StrEnum):
    """The deterministic V1 Replay orderings."""

    ARRIVAL = "arrival"
    STRICT_EVENT = "strict_event"


class CompletenessState(StrEnum):
    """Replay intentionally makes no completeness claim in V1."""

    NOT_ASSERTED = "not_asserted"


class ReplayErrorCode(StrEnum):
    """The complete FINAL CLOSED Replay error vocabulary."""

    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_CURSOR = "INVALID_CURSOR"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    MALFORMED_EVIDENCE = "MALFORMED_EVIDENCE"
    MALFORMED_AUTHORITY = "MALFORMED_AUTHORITY"
    AUTHORITY_CONFLICT = "AUTHORITY_CONFLICT"
    AVAILABILITY_EVIDENCE_MISSING = "AVAILABILITY_EVIDENCE_MISSING"
    UNSUPPORTED_EVENT_TIME = "UNSUPPORTED_EVENT_TIME"
    CURSOR_MISMATCH = "CURSOR_MISMATCH"


class ReplayExclusionCode(StrEnum):
    """Bounded non-authoritative reasons for an otherwise visible candidate."""

    EVIDENCE_NOT_AVAILABLE_BY_CUTOFF = "evidence_not_available_by_cutoff"
    AUTHORITY_NOT_AVAILABLE_BY_CUTOFF = "authority_not_available_by_cutoff"


class ReplayAsOfError(Exception):
    """A bounded provider-neutral Replay failure."""

    def __init__(self, code: ReplayErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class SelectionWindow:
    """A half-open timestamp range selected on one named axis."""

    axis: SelectionAxis
    start_ns: int
    end_ns: int


@dataclass(frozen=True, slots=True)
class AsOfRequest:
    """A provider-neutral request for one bounded historical Replay view."""

    as_of_cutoff_ns: int
    authority_policy_version: str
    selection_window: SelectionWindow
    ordering: ReplayOrdering
    assets: tuple[AssetId, ...] | None
    channels: tuple[str, ...] | None
    page_size: int
    cursor: str | None

    def __post_init__(self) -> None:
        """Take immutable ownership of iterable filter inputs without validating them."""
        for name in ("assets", "channels"):
            value = getattr(self, name)
            if value is None or isinstance(value, (str, bytes)):
                continue
            try:
                object.__setattr__(self, name, tuple(value))
            except TypeError:
                continue


@dataclass(frozen=True, slots=True)
class AvailabilityReference:
    """Read-side availability evidence only; Slice 1 has no ledger mechanics."""

    available_at_ns: int | None
    reference: str | None


@dataclass(frozen=True, slots=True)
class AuthoritativeReplayRecord:
    """One immutable evidence/recorded-authority pair qualified for Replay."""

    capture_fact: CaptureFact
    truth_decision: TruthDecision
    evidence_availability_reference: str
    authority_availability_reference: str


@dataclass(frozen=True, slots=True)
class ReplayExclusion:
    """A bounded, non-completeness-claiming exclusion."""

    code: ReplayExclusionCode
    capture_id: str


@dataclass(frozen=True, slots=True)
class AsOfReplayView:
    """One immutable page with deterministic provenance and continuation."""

    records: tuple[AuthoritativeReplayRecord, ...]
    request_identity: str
    authority_policy_version: str
    as_of_cutoff_ns: int
    selection_window: SelectionWindow
    ordering: ReplayOrdering
    ordering_rule_version: str
    source_snapshot_identity: str
    completeness: CompletenessState
    exclusions: tuple[ReplayExclusion, ...]
    next_cursor: str | None
