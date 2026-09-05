"""SDK-native market-lifecycle streaming for a verified market."""

from collections.abc import AsyncIterator

from kalshi.ws.models.event_fee import EventFeeUpdateMessage
from kalshi.ws.models.market_lifecycle import MarketLifecycleMessage

from live15_quant_v2.data.market_ingress.ingress_boundary import (
    VerifiedMarketIdentity,
)
from live15_quant_v2.data.market_ingress.market_stream.ports import (
    MarketStreamSocket,
)


class LifecycleStream:
    def __init__(self, websocket: MarketStreamSocket) -> None:
        self._websocket = websocket

    async def subscribe(
        self, identity: VerifiedMarketIdentity
    ) -> AsyncIterator[MarketLifecycleMessage | EventFeeUpdateMessage]:
        return await self._websocket.subscribe_market_lifecycle(
            tickers=[identity.ticker]
        )
