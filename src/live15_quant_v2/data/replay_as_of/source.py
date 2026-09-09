"""The narrow provider-neutral Replay source seam and in-memory test source."""

from dataclasses import dataclass
from typing import Protocol

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.data_truth.models import TruthDecision
from live15_quant_v2.data.replay_as_of.models import (
    AvailabilityReference,
    ReplayOrdering,
    SelectionAxis,
)
from live15_quant_v2.data.storage.capture import CaptureFact

AvailabilityEvidence = AvailabilityReference


@dataclass(frozen=True, slots=True)
class SourceAuthorityIdentities:
    """Configured logical authorities used to bind a Replay snapshot."""

    evidence: str
    truth_decision: str
    availability: str


@dataclass(frozen=True, slots=True)
class ReplayCandidateScope:
    """Validated semantic bounds a source may safely use for discovery."""

    authority_policy_version: str
    as_of_cutoff_ns: int
    selection_axis: SelectionAxis
    selection_start_ns: int
    selection_end_ns: int
    assets: tuple[AssetId, ...] | None
    channels: tuple[str, ...] | None
    ordering: ReplayOrdering


@dataclass(frozen=True, slots=True)
class ReplaySourceRecord:
    """One provider-neutral paired candidate supplied to the Replay core."""

    capture_fact: CaptureFact
    truth_decision: TruthDecision
    evidence_availability: AvailabilityReference
    authority_availability: AvailabilityReference


class ReplaySource(Protocol):
    """Read-only seam needed by the pure Replay core."""

    def candidate_records(self, scope: ReplayCandidateScope) -> tuple[ReplaySourceRecord, ...]:
        """Return a semantics-preserving candidate superset for one scope.

        A future physical source may push down safe bounds but must not omit a
        qualified null provider-time candidate for an EVENT_TIME request.
        ReplayAsOf independently enforces every semantic qualification rule.
        """

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

    def candidate_records(self, scope: ReplayCandidateScope) -> tuple[ReplaySourceRecord, ...]:
        """Return the source-owned immutable candidate tuple."""
        del scope
        return self._records

    def source_authorities(self) -> SourceAuthorityIdentities:
        """Return the configured logical identities."""
        return self._authorities
