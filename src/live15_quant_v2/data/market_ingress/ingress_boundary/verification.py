"""Fail-closed verification against official series-query provenance."""

from collections.abc import Iterable

from live15_quant_v2.data.market_ingress.ingress_boundary.models import (
    DiscoveredMarket,
    MarketScopeBinding,
    MarketWindow,
    VerificationResult,
    VerificationStatus,
    _issue_verified_market_identity,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.ports import MarketScopePort


class OfficialMarketVerifier:
    def verify(
        self,
        *,
        scope: MarketScopePort,
        binding: MarketScopeBinding,
        window: MarketWindow,
        markets: Iterable[DiscoveredMarket],
    ) -> VerificationResult:
        if (
            scope.binding_for_asset(binding.asset_id) != binding
            or scope.binding_for_series(binding.series_ticker) != binding
        ):
            return VerificationResult(VerificationStatus.INVALID, reason="unapproved binding")
        exact = [
            market
            for market in markets
            if market.observed_series_ticker == binding.series_ticker
            and market.open_time == window.open_time
            and market.close_time == window.close_time
        ]
        if not exact:
            return VerificationResult(
                VerificationStatus.NO_MATCH, reason="no exact official market"
            )
        if len(exact) != 1:
            return VerificationResult(
                VerificationStatus.AMBIGUOUS, reason="multiple exact official markets"
            )
        market = exact[0]
        if not market.ticker or not market.event_ticker:
            return VerificationResult(
                VerificationStatus.INVALID,
                reason="missing official market identity",
            )
        if not market.strike.usable:
            return VerificationResult(
                VerificationStatus.INVALID,
                reason="no usable structured official strike",
            )
        return VerificationResult(
            VerificationStatus.VERIFIED,
            _issue_verified_market_identity(
                binding,
                market.ticker,
                market.event_ticker,
                window,
                market.strike,
            ),
        )
