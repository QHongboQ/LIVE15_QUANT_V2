"""Authoritative Kalshi discovery; no title matching or fallback selection."""

from __future__ import annotations

from collections.abc import Iterable

from kalshi.errors import KalshiNotFoundError
from kalshi.models import Market

from live15_quant_v2.data.market_ingress.kalshi_gateway.gateway import KalshiGateway
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.models import (
    CandidateTicker,
    DiscoveredMarket,
)


class OfficialMarketDiscovery:
    """Translate only official SDK market facts needed for later verification."""

    def __init__(self, gateway: KalshiGateway) -> None:
        self._gateway = gateway

    def discover(
        self, *, series_ticker: str, candidate: CandidateTicker | None = None
    ) -> tuple[DiscoveredMarket, ...]:
        """Look up a hint, then use exact SDK series discovery as authority."""
        raw_markets: list[Market] = []
        if candidate is not None:
            try:
                raw_markets.append(self._gateway.fetch_market(candidate.ticker))
            except KalshiNotFoundError:
                pass
        raw_markets.extend(self._gateway.discover_markets(series_ticker))
        translated = [self._translate(market, series_ticker) for market in raw_markets]
        return tuple(self._deduplicate(translated))

    @staticmethod
    def _translate(market: Market, series_ticker: str) -> DiscoveredMarket:
        target = OfficialMarketDiscovery._extract_target(market)
        return DiscoveredMarket(
            series_ticker=series_ticker,
            ticker=market.ticker,
            event_ticker=market.event_ticker,
            open_time=market.open_time,
            close_time=market.close_time,
            target=target,
        )

    @staticmethod
    def _extract_target(market: Market) -> str | None:
        """Use only target/strike fields from this same official market object."""
        functional = market.functional_strike
        if isinstance(functional, str) and functional.strip():
            return functional.strip()
        floor = market.floor_strike
        cap = market.cap_strike
        if floor is not None and cap is not None:
            return f"[{floor},{cap}]"
        if floor is not None:
            return f">={floor}"
        if cap is not None:
            return f"<={cap}"
        return None

    @staticmethod
    def _deduplicate(markets: Iterable[DiscoveredMarket]) -> list[DiscoveredMarket]:
        unique: dict[str, DiscoveredMarket] = {}
        for market in markets:
            unique[market.ticker] = market
        return list(unique.values())