"""The provider-neutral seam for raw Hot Store storage."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from live15_quant_v2.data.storage.capture import CaptureFact
from live15_quant_v2.data.storage.hot_store.models import CaptureRange


@dataclass(frozen=True, slots=True)
class AppendReceipt:
    """An explicit successful acknowledgement for a raw capture batch."""

    appended_count: int


class HotStoreError(RuntimeError):
    """Base error for a failed Hot Store operation."""


class BatchTooLargeError(HotStoreError):
    """Raised when a caller exceeds the declared write-batch interface."""


class HotStoreUnavailableError(HotStoreError):
    """Raised when the configured Hot Store cannot be reached."""


class HotStoreWriteRejectedError(HotStoreError):
    """Raised when a write is not acknowledged by the configured Hot Store."""


class HotStore(Protocol):
    """Store and physically retrieve raw captures without interpreting them."""

    max_batch_rows: int

    def append_batch(self, facts: Sequence[CaptureFact]) -> AppendReceipt:
        """Persist one explicitly bounded batch or raise without a success receipt."""

    def read_capture(self, capture_id: str) -> CaptureFact | None:
        """Return the raw capture with this identity, if it is stored."""

    def read_range(self, capture_range: CaptureRange) -> list[CaptureFact]:
        """Return raw facts matching a physical received-time retrieval range."""
