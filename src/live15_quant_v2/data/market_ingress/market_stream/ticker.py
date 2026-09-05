"""SDK-native ticker streaming for a verified market."""

from collections.abc import AsyncIterator

from kalshi.ws.models.ticker import TickerMessage

from live15_quant_v2.data.market_ingress.ingress_boundary import (
    VerifiedMarketIdentity,
)
from live15_quant_v2.data.market_ingress.market_stream.ports import (
    MarketStreamSocket,
)


class TickerStream:
    def __init__(self, websocket: MarketStreamSocket) -> None:
        self._websocket = websocket

    async def subscribe(
        self, identity: VerifiedMarketIdentity
    ) -> AsyncIterator[TickerMessage]:
        return await self._websocket.subscribe_ticker(tickers=[identity.ticker])
