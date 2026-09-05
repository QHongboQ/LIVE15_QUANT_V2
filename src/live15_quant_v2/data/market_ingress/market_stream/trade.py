"""SDK-native trade streaming for a verified market."""

from collections.abc import AsyncIterator

from kalshi.ws.models.trade import TradeMessage

from live15_quant_v2.data.market_ingress.ingress_boundary import (
    VerifiedMarketIdentity,
)
from live15_quant_v2.data.market_ingress.market_stream.ports import (
    MarketStreamSocket,
)


class TradeStream:
    def __init__(self, websocket: MarketStreamSocket) -> None:
        self._websocket = websocket

    async def subscribe(
        self, identity: VerifiedMarketIdentity
    ) -> AsyncIterator[TradeMessage]:
        return await self._websocket.subscribe_trade(tickers=[identity.ticker])
