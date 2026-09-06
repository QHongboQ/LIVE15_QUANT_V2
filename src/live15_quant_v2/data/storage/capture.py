"""Shared immutable raw-capture contract for Storage children."""

from dataclasses import dataclass

from live15_quant_v2.data.asset import AssetId


@dataclass(frozen=True, slots=True)
class CaptureFact:
    """One immutable fact captured from an upstream market-data provider."""

    capture_id: str
    asset: AssetId
    provider: str
    source_id: str
    channel: str
    message_type: str
    event_subtype: str | None
    sid: int
    seq: int | None
    provider_timestamp: int | None
    received_timestamp: int
    schema_version: str
    payload: str
