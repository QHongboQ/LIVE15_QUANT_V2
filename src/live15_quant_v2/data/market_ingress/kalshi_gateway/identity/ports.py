"""LIVE15-owned ports; concrete market scope configuration is intentionally deferred."""

from __future__ import annotations

from typing import Protocol


class MarketScopePort(Protocol):
    """Answer whether a supplied Kalshi series is approved for LIVE15."""

    def approves_series(self, series_ticker: str) -> bool:
        """Return approval for exactly one externally supplied series ticker."""