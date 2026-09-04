"""Deterministic candidate ticker hints; candidates are never market truth."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.models import (
    CandidateTicker,
    MarketWindow,
)

NEW_YORK = ZoneInfo("America/New_York")


class CandidateTickerPredictor:
    """Predict a series/window ticker hint using New York calendar mechanics."""

    def predict(self, series_ticker: str, window: MarketWindow) -> CandidateTicker:
        if not series_ticker or series_ticker != series_ticker.strip():
            raise ValueError("series_ticker must be a non-empty exact value")
        local_open = window.open_time.astimezone(NEW_YORK)
        suffix = local_open.strftime("%y%b%d%H%M").upper()
        return CandidateTicker(
            series_ticker=series_ticker,
            ticker=f"{series_ticker}-{suffix}",
            window=window,
        )