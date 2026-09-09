"""The narrow provider-neutral Replay source seam and in-memory test source."""

from dataclasses import dataclass
from typing import Protocol

from live15_quant_v2.data.data_truth.models import TruthDecision
from live15_quant_v2.data.replay_as_of.models import AvailabilityReference
from live15_quant_v2.data.storage.capture import CaptureFact

AvailabilityEvidence = AvailabilityReference


@dataclass(frozen=True, slots=True)
class SourceAuthorityIdentities:
    """Configured logical authorities used to bind a Replay snapshot."""

    evidence: str
    truth_decision: str
    availability: str


@dataclass(frozen=True, slots=True)
class ReplaySourceRecord:
    """One provider-neutral paired candidate supplied to the Replay core."""

    capture_fact: CaptureFact
    truth_decision: TruthDecision
    evidence_availability: AvailabilityReference
    authority_availability: AvailabilityReference


class ReplaySource(Protocol):
    """Read-only seam needed by the pure Replay core."""

    def candidate_records(self) -> tuple[ReplaySourceRecord, ...]:
        """Return bounded candidate records without assigning their order."""

    def source_authorities(self) -> SourceAuthorityIdentities:
        """Return stable configured logical authority identities."""


class InMemoryReplaySource:
    """Immutable, provider-neutral Slice 1 source used through ReplaySource."""

    def __init__(
        self,
        records: tuple[ReplaySourceRecord, ...] | list[ReplaySourceRecord],
        authorities: SourceAuthorityIdentities,
    ) -> None:
        self._records = tuple(records)
        self._authorities = authorities

    def candidate_records(self) -> tuple[ReplaySourceRecord, ...]:
        """Return the source-owned immutable candidate tuple."""
        return self._records

    def source_authorities(self) -> SourceAuthorityIdentities:
        """Return the configured logical identities."""
        return self._authorities
