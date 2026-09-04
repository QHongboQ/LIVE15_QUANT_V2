"""Official discovery through the Kalshi provider gateway."""

from decimal import Decimal

from kalshi.models import Market

from live15_quant_v2.data.market_ingress.ingress_boundary.models import (
    DiscoveredMarket,
    MarketScopeBinding,
    MarketWindow,
    OfficialStrike,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway import KalshiGateway


class OfficialMarketDiscovery:
    def __init__(self, gateway: KalshiGateway) -> None:
        self._gateway = gateway

    def discover(
        self, *, binding: MarketScopeBinding, window: MarketWindow
    ) -> tuple[DiscoveredMarket, ...]:
        envelope = 15 * 60
        raw = self._gateway.discover_markets(
            series_ticker=binding.series_ticker,
            min_close_ts=int(window.close_time.timestamp()) - envelope,
            max_close_ts=int(window.close_time.timestamp()) + envelope,
        )
        return tuple(self._translate(market, binding.series_ticker) for market in raw)

    @staticmethod
    def _translate(market: Market, observed_series_ticker: str) -> DiscoveredMarket:
        strike = OfficialStrike(
            market.strike_type,
            OfficialMarketDiscovery._decimal(market.floor_strike),
            OfficialMarketDiscovery._decimal(market.cap_strike),
            market.yes_sub_title,
            market.functional_strike,
        )
        return DiscoveredMarket(
            observed_series_ticker,
            market.ticker,
            market.event_ticker,
            market.open_time,
            market.close_time,
            strike,
        )

    @staticmethod
    def _decimal(value: object) -> Decimal | None:
        return value if isinstance(value, Decimal) else None
