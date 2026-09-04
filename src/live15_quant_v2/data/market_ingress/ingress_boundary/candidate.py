"""Non-authoritative ticker heuristic derived from observed Kalshi behavior."""

from zoneinfo import ZoneInfo

from live15_quant_v2.data.market_ingress.ingress_boundary.models import (
    CandidateTicker,
    MarketScopeBinding,
    MarketWindow,
)

NEW_YORK = ZoneInfo("America/New_York")


class CandidateTickerPredictor:
    """Return a hint only for the observed KX*15M shape; otherwise omit it."""

    def predict(
        self, binding: MarketScopeBinding, window: MarketWindow
    ) -> CandidateTicker | None:
        series = binding.series_ticker
        if not series.startswith("KX") or not series.endswith("15M"):
            return None
        close = window.close_time.astimezone(NEW_YORK)
        stamp = close.strftime("%y%b%d%H%M").upper()
        return CandidateTicker(binding, f"{series}-{stamp}-{close.minute:02d}", window)
