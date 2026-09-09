"""Behavioral tests for Replay-internal availability support."""

from dataclasses import FrozenInstanceError

import pytest

from live15_quant_v2.data.replay_as_of.availability import (
    SUPPORTED_PROOF_SCHEMA_VERSION,
    AvailabilityKey,
    AvailabilityKind,
    AvailabilityRecord,
    AvailabilitySupportError,
    AvailabilitySupportErrorCode,
    AvailabilityWriter,
)


class _Store:
    def __init__(self, floor: int | None = None) -> None:
        self.records: dict[AvailabilityKey, AvailabilityRecord] = {}
        self.floor = floor

    def find(self, key: AvailabilityKey) -> AvailabilityRecord | None:
        return self.records.get(key)

    def read_committed_floor(self) -> int | None:
        return self.floor

    def append(self, record: AvailabilityRecord) -> AvailabilityRecord:
        self.records[record.key] = record
        return record


def test_evidence_record_has_an_immutable_policy_free_semantic_key() -> None:
    record = AvailabilityRecord(
        AvailabilityKind.EVIDENCE,
        "capture-1",
        None,
        101,
        SUPPORTED_PROOF_SCHEMA_VERSION,
        "hot-store/v1",
    )

    assert record.key == AvailabilityKey(AvailabilityKind.EVIDENCE, "capture-1", None)
    with pytest.raises(FrozenInstanceError):
        record.capture_id = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    "kind,capture_id,policy,available_at,source",
    [
        (AvailabilityKind.EVIDENCE, "capture", "data-truth/v1", 1, "source"),
        (AvailabilityKind.AUTHORITY, "capture", None, 1, "source"),
        (AvailabilityKind.EVIDENCE, "", None, 1, "source"),
        (AvailabilityKind.EVIDENCE, "capture", None, True, "source"),
        (AvailabilityKind.EVIDENCE, "capture", None, -1, "source"),
        (AvailabilityKind.EVIDENCE, "capture", None, 1, ""),
    ],
)
def test_invalid_availability_semantics_fail_closed(
    kind: AvailabilityKind,
    capture_id: str,
    policy: str | None,
    available_at: object,
    source: str,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        AvailabilityRecord(kind, capture_id, policy, available_at, SUPPORTED_PROOF_SCHEMA_VERSION, source)


def test_writer_samples_after_entry_clamps_to_floor_and_reconciles_existing() -> None:
    store = _Store(floor=100)
    writer = AvailabilityWriter(store, wall_time_ns=lambda: 90, monotonic_ns=lambda: 7)

    first = writer.record_proven(
        kind=AvailabilityKind.EVIDENCE,
        capture_id="capture-1",
        policy_version=None,
        source_authority_identity="hot-store/v1",
    )
    repeated = writer.record_proven(
        kind=AvailabilityKind.EVIDENCE,
        capture_id="capture-1",
        policy_version=None,
        source_authority_identity="hot-store/v1",
    )

    assert first.available_at_ns == 101
    assert repeated is first


def test_in_doubt_reconciles_only_the_exact_attempted_immutable_record() -> None:
    class InDoubtStore(_Store):
        def append(self, record: AvailabilityRecord) -> AvailabilityRecord:
            self.attempted = record
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "ambiguous")

    store = InDoubtStore()
    writer = AvailabilityWriter(store, wall_time_ns=lambda: 10, monotonic_ns=lambda: 1)
    arguments = {"kind": AvailabilityKind.EVIDENCE, "capture_id": "capture-2", "policy_version": None, "source_authority_identity": "source/v1"}
    with pytest.raises(AvailabilitySupportError) as first:
        writer.record_proven(**arguments)
    assert first.value.code is AvailabilitySupportErrorCode.IN_DOUBT
    store.records[store.attempted.key] = store.attempted
    assert writer.record_proven(**arguments) == store.attempted


def test_in_doubt_different_visible_record_fails_closed_without_reappend() -> None:
    class InDoubtStore(_Store):
        def append(self, record: AvailabilityRecord) -> AvailabilityRecord:
            self.attempts = getattr(self, "attempts", 0) + 1
            self.record = record
            raise AvailabilitySupportError(AvailabilitySupportErrorCode.IN_DOUBT, "ambiguous")

    store = InDoubtStore()
    writer = AvailabilityWriter(store, wall_time_ns=lambda: 10, monotonic_ns=lambda: 1)
    arguments = {"kind": AvailabilityKind.EVIDENCE, "capture_id": "capture-3", "policy_version": None, "source_authority_identity": "source/v1"}
    with pytest.raises(AvailabilitySupportError): writer.record_proven(**arguments)
    store.records[store.record.key] = AvailabilityRecord(AvailabilityKind.EVIDENCE, "capture-3", None, 99, SUPPORTED_PROOF_SCHEMA_VERSION, "source/v1")
    with pytest.raises(AvailabilitySupportError) as error: writer.record_proven(**arguments)
    assert error.value.code is AvailabilitySupportErrorCode.INVARIANT_CONFLICT
    assert store.attempts == 1
