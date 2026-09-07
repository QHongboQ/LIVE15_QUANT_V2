"""Provider-neutral Durable Persistence result and handoff contract."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from live15_quant_v2.data.storage.capture import CaptureFact


class PersistenceStatus(StrEnum):
    """The sealed Durable Persistence outcome categories."""

    LOCAL_PERSISTENCE_FAILED = "local_persistence_failed"
    PERSISTED_PENDING = "persisted_pending"
    ACKNOWLEDGED_OK = "acknowledged_ok"
    DEFINITELY_REJECTED = "definitely_rejected"
    IN_DOUBT = "in_doubt"


@dataclass(frozen=True, slots=True)
class PersistenceResult:
    """A LIVE15 persistence outcome without exposing a lease-local FSN."""

    status: PersistenceStatus


class DurablePersistence(Protocol):
    """Hand one immutable capture fact to the configured durable transport."""

    def persist(self, fact: CaptureFact) -> PersistenceResult:
        """Return the sealed ownership and acknowledgement interpretation."""


__all__ = ["DurablePersistence", "PersistenceResult", "PersistenceStatus"]
