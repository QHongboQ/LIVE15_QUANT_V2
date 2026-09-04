"""Fail-closed verification of an official Kalshi market identity."""

from __future__ import annotations

from collections.abc import Iterable

from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.models import (
    DiscoveredMarket,
    MarketWindow,
    VerificationResult,
    VerificationStatus,
    VerifiedMarketIdentity,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.ports import (
    MarketScopePort,
)


class OfficialMarketVerifier:
    """Verify exactly one official market; never infer truth from a candidate."""

    def verify(
        self,
        *,
        scope: MarketScopePort,
        series_ticker: str,
        window: MarketWindow,
        markets: Iterable[DiscoveredMarket],
    ) -> VerificationResult:
        if not scope.approves_series(series_ticker):
            return VerificationResult(VerificationStatus.INVALID, reason="series is not approved")
        exact = [
            market
            for market in markets
            if market.series_ticker == series_ticker
            and market.open_time == window.open_time
            and market.close_time == window.close_time
        ]
        if not exact:
            return VerificationResult(VerificationStatus.NO_MATCH, reason="no exact official market")
        if len(exact) != 1:
            return VerificationResult(VerificationStatus.AMBIGUOUS, reason="multiple exact official markets")
        market = exact[0]
        if not self._coherent_event_identity(market):
            return VerificationResult(VerificationStatus.INVALID, reason="incoherent ticker/event identity")
        if not market.has_published_target or not self._valid_target(market.target):
            return VerificationResult(VerificationStatus.INVALID, reason="target is unpublished or malformed")
        return VerificationResult(
            VerificationStatus.VERIFIED,
            identity=VerifiedMarketIdentity(
                series_ticker=market.series_ticker,
                ticker=market.ticker,
                event_ticker=market.event_ticker or "",
                window=window,
                target=market.target or "",
            ),
        )

    @staticmethod
    def _coherent_event_identity(market: DiscoveredMarket) -> bool:
        return bool(
            market.ticker
            and market.event_ticker
            and market.ticker.startswith(market.event_ticker)
        )

    @staticmethod
    def _valid_target(target: str | None) -> bool:
        return bool(target and target.isprintable() and target.strip())