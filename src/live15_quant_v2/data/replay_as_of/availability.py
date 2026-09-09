"""Replay-internal, provider-neutral availability recording support."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

SUPPORTED_PROOF_SCHEMA_VERSION = "replay-availability-proof/v1"


class AvailabilityKind(StrEnum):
    EVIDENCE = "evidence"
    AUTHORITY = "authority"


@dataclass(frozen=True, slots=True)
class AvailabilityKey:
    kind: AvailabilityKind
    capture_id: str
    policy_version: str | None

    def __post_init__(self) -> None:
        _validate_key(self.kind, self.capture_id, self.policy_version)


@dataclass(frozen=True, slots=True)
class AvailabilityRecord:
    kind: AvailabilityKind
    capture_id: str
    policy_version: str | None
    available_at_ns: int
    proof_schema_version: str
    source_authority_identity: str

    def __post_init__(self) -> None:
        _validate_key(self.kind, self.capture_id, self.policy_version)
        if not isinstance(self.available_at_ns, int) or isinstance(self.available_at_ns, bool):
            raise TypeError("available_at_ns must be an int")
        if self.available_at_ns < 0:
            raise ValueError("available_at_ns must be non-negative")
        if self.proof_schema_version != SUPPORTED_PROOF_SCHEMA_VERSION:
            raise ValueError("unsupported proof schema")
        if not isinstance(self.source_authority_identity, str) or not self.source_authority_identity:
            raise ValueError("source_authority_identity must be non-empty text")

    @property
    def key(self) -> AvailabilityKey:
        return AvailabilityKey(self.kind, self.capture_id, self.policy_version)


class AvailabilityStore(Protocol):
    def find(self, key: AvailabilityKey) -> AvailabilityRecord | None: ...

    def read_committed_floor(self) -> int | None: ...

    def append(self, record: AvailabilityRecord) -> AvailabilityRecord: ...


class AvailabilitySupportErrorCode(StrEnum):
    DEFINITE_PREPUBLICATION_FAILURE = "definite_prepublication_failure"
    IN_DOUBT = "in_doubt"
    INVARIANT_CONFLICT = "invariant_conflict"
    SOURCE_UNAVAILABLE = "source_unavailable"


class AvailabilitySupportError(Exception):
    def __init__(self, code: AvailabilitySupportErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class AvailabilityWriter:
    """One ordered writer; callers enter only after their proof trigger."""

    def __init__(
        self,
        store: AvailabilityStore,
        *,
        wall_time_ns: Callable[[], int] = time.time_ns,
        monotonic_ns: Callable[[], int] = time.monotonic_ns,
    ) -> None:
        self._store = store
        self._wall_time_ns = wall_time_ns
        self._monotonic_ns = monotonic_ns
        self._anchor_wall_ns = wall_time_ns()
        self._anchor_monotonic_ns = monotonic_ns()
        self._observed_monotonic_ns = self._anchor_monotonic_ns
        floor = store.read_committed_floor()
        if floor is not None and (not isinstance(floor, int) or isinstance(floor, bool) or floor < 0):
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.SOURCE_UNAVAILABLE, "invalid committed floor")
        self._committed_floor = floor
        self._last_issued: int | None = None
        self._in_doubt: set[AvailabilityKey] = set()

    def record_proven(
        self,
        *,
        kind: AvailabilityKind,
        capture_id: str,
        policy_version: str | None,
        source_authority_identity: str,
    ) -> AvailabilityRecord:
        key = AvailabilityKey(kind, capture_id, policy_version)
        existing = self._store.find(key)
        if existing is not None:
            self._require_compatible(existing, key, source_authority_identity)
            self._in_doubt.discard(key)
            return existing
        if key in self._in_doubt:
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "append remains unresolved")
        record = AvailabilityRecord(
            kind, capture_id, policy_version, self._next_proof_time(),
            SUPPORTED_PROOF_SCHEMA_VERSION, source_authority_identity,
        )
        try:
            result = self._store.append(record)
        except AvailabilitySupportError as error:
            if error.code is AvailabilitySupportErrorCode.IN_DOUBT:
                self._in_doubt.add(key)
            raise
        self._require_compatible(result, key, source_authority_identity)
        if result != record:
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.INVARIANT_CONFLICT, "append changed immutable record")
        return result

    def _next_proof_time(self) -> int:
        monotonic_now = self._monotonic_ns()
        if monotonic_now < self._observed_monotonic_ns:
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.SOURCE_UNAVAILABLE, "monotonic clock regressed")
        self._observed_monotonic_ns = monotonic_now
        candidate = self._anchor_wall_ns + (monotonic_now - self._anchor_monotonic_ns)
        floor = max(value for value in (self._committed_floor, self._last_issued) if value is not None) if any(value is not None for value in (self._committed_floor, self._last_issued)) else None
        if floor is not None and candidate <= floor:
            candidate = floor + 1
        self._last_issued = candidate
        return candidate

    @staticmethod
    def _require_compatible(record: AvailabilityRecord, key: AvailabilityKey, source: str) -> None:
        if record.key != key or record.proof_schema_version != SUPPORTED_PROOF_SCHEMA_VERSION or record.source_authority_identity != source:
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.INVARIANT_CONFLICT, "immutable availability conflict")


def _validate_key(kind: AvailabilityKind, capture_id: str, policy_version: str | None) -> None:
    if not isinstance(kind, AvailabilityKind):
        raise TypeError("kind must be AvailabilityKind")
    if not isinstance(capture_id, str) or not capture_id:
        raise ValueError("capture_id must be non-empty text")
    if kind is AvailabilityKind.EVIDENCE and policy_version is not None:
        raise ValueError("evidence policy_version must be None")
    if kind is AvailabilityKind.AUTHORITY and (
        not isinstance(policy_version, str) or not policy_version
    ):
        raise ValueError("authority policy_version must be non-empty text")
