"""Hot Store physical retrieval models."""

from dataclasses import dataclass
from enum import StrEnum

from live15_quant_v2.data.asset import AssetId


class TimestampOrder(StrEnum):
    """Physical ordering available for a Hot Store range read."""

    PROVIDER = "provider_timestamp"
    RECEIVED = "received_timestamp"


@dataclass(frozen=True, slots=True)
class CaptureRange:
    """A physical received-time range, optionally narrowed by raw metadata."""

    received_start: int
    received_end: int
    asset: AssetId | None = None
    channel: str | None = None
    order_by: TimestampOrder = TimestampOrder.RECEIVED

    def __post_init__(self) -> None:
        if self.received_start > self.received_end:
            raise ValueError("received_start must not be after received_end")
