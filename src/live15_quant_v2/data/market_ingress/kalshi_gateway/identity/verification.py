"""Fail-closed verification against official series-query provenance."""
from collections.abc import Iterable

from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.models import (
    DiscoveredMarket,
    MarketScopeBinding,
    MarketWindow,
    VerificationResult,
    VerificationStatus,
    VerifiedMarketIdentity,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.ports import (
    MarketScopePort,
)


class OfficialMarketVerifier:
    def verify(self, *, scope: MarketScopePort, binding: MarketScopeBinding, window: MarketWindow, markets: Iterable[DiscoveredMarket]) -> VerificationResult:
        if scope.binding_for_asset(binding.asset_id) != binding or scope.binding_for_series(binding.series_ticker) != binding: return VerificationResult(VerificationStatus.INVALID, reason="unapproved binding")
        exact = [m for m in markets if m.observed_series_ticker == binding.series_ticker and m.open_time == window.open_time and m.close_time == window.close_time]
        if not exact: return VerificationResult(VerificationStatus.NO_MATCH, reason="no exact official market")
        if len(exact) != 1: return VerificationResult(VerificationStatus.AMBIGUOUS, reason="multiple exact official markets")
        market = exact[0]
        if not market.strike.usable: return VerificationResult(VerificationStatus.INVALID, reason="no usable structured official strike")
        return VerificationResult(VerificationStatus.VERIFIED, VerifiedMarketIdentity(binding, market.ticker, market.event_ticker or "", window, market.strike))