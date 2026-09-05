"""Public composition for typed streams of verified LIVE15 markets."""

from collections.abc import AsyncIterator

from kalshi.ws.models.event_fee import EventFeeUpdateMessage
from kalshi.ws.models.market_lifecycle import MarketLifecycleMessage
from kalshi.ws.models.orderbook_delta import (
    OrderbookDeltaMessage,
    OrderbookSnapshotMessage,
)
from kalshi.ws.models.ticker import TickerMessage
from kalshi.ws.models.trade import TradeMessage

from live15_quant_v2.data.market_ingress.ingress_boundary import (
    VerifiedMarketIdentity,
)
from live15_quant_v2.data.market_ingress.market_stream.lifecycle import (
    LifecycleStream,
)
from live15_quant_v2.data.market_ingress.market_stream.orderbook import (
    OrderbookStream,
)
from live15_quant_v2.data.market_ingress.market_stream.ports import (
    MarketStreamSocket,
)
from live15_quant_v2.data.market_ingress.market_stream.ticker import TickerStream
from live15_quant_v2.data.market_ingress.market_stream.trade import TradeStream


class MarketStream:
    """Expose SDK-native typed streams selected only by verified identities."""

    def __init__(self, websocket: MarketStreamSocket) -> None:
        self._orderbook = OrderbookStream(websocket)
        self._ticker = TickerStream(websocket)
        self._trade = TradeStream(websocket)
        self._lifecycle = LifecycleStream(websocket)

    async def orderbook(
        self, identity: VerifiedMarketIdentity
    ) -> AsyncIterator[OrderbookSnapshotMessage | OrderbookDeltaMessage]:
        return await self._orderbook.subscribe(self._require_verified(identity))

    async def ticker(
        self, identity: VerifiedMarketIdentity
    ) -> AsyncIterator[TickerMessage]:
        return await self._ticker.subscribe(self._require_verified(identity))

    async def trades(
        self, identity: VerifiedMarketIdentity
    ) -> AsyncIterator[TradeMessage]:
        return await self._trade.subscribe(self._require_verified(identity))

    async def lifecycle(
        self, identity: VerifiedMarketIdentity
    ) -> AsyncIterator[MarketLifecycleMessage | EventFeeUpdateMessage]:
        return await self._lifecycle.subscribe(self._require_verified(identity))

    @staticmethod
    def _require_verified(identity: VerifiedMarketIdentity) -> VerifiedMarketIdentity:
        if not isinstance(identity, VerifiedMarketIdentity):
            raise TypeError("Market Stream requires a VerifiedMarketIdentity")
        if not identity.has_verified_provenance:
            raise ValueError("Market Stream requires verifier-issued market identity")
        return identity
