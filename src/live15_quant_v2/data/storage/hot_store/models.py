"""Provider-neutral raw capture facts and physical retrieval filters."""

from dataclasses import dataclass
from enum import StrEnum


class TimestampOrder(StrEnum):
    """Physical ordering available for a Hot Store range read."""

    PROVIDER = "provider_timestamp"
    RECEIVED = "received_timestamp"


@dataclass(frozen=True, slots=True)
class CaptureFact:
    """One immutable fact captured from an upstream market-data provider."""

    capture_id: str
    asset: str
    channel: str
    provider: str
    sid: int
    seq: int | None
    provider_timestamp: int
    received_timestamp: int
    schema_version: str
    payload: str


@dataclass(frozen=True, slots=True)
class CaptureRange:
    """A physical received-time range, optionally narrowed by raw metadata."""

    received_start: int
    received_end: int
    asset: str | None = None
    channel: str | None = None
    order_by: TimestampOrder = TimestampOrder.RECEIVED

    def __post_init__(self) -> None:
        if self.received_start > self.received_end:
            raise ValueError("received_start must not be after received_end")
