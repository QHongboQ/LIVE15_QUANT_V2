"""SDK-native orderbook streaming for a verified market."""

from collections.abc import AsyncIterator

from kalshi.ws.models.orderbook_delta import (
    OrderbookDeltaMessage,
    OrderbookSnapshotMessage,
)

from live15_quant_v2.data.market_ingress.ingress_boundary import (
    VerifiedMarketIdentity,
)
from live15_quant_v2.data.market_ingress.market_stream.ports import (
    MarketStreamSocket,
)


class OrderbookStream:
    def __init__(self, websocket: MarketStreamSocket) -> None:
        self._websocket = websocket

    async def subscribe(
        self, identity: VerifiedMarketIdentity
    ) -> AsyncIterator[OrderbookSnapshotMessage | OrderbookDeltaMessage]:
        return await self._websocket.subscribe_orderbook_delta(tickers=[identity.ticker])
