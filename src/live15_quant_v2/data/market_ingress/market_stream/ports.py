"""Private typed seam for the SDK WebSocket capability."""

from collections.abc import AsyncIterator
from typing import Protocol

from kalshi.ws.models.event_fee import EventFeeUpdateMessage
from kalshi.ws.models.market_lifecycle import MarketLifecycleMessage
from kalshi.ws.models.orderbook_delta import (
    OrderbookDeltaMessage,
    OrderbookSnapshotMessage,
)
from kalshi.ws.models.ticker import TickerMessage
from kalshi.ws.models.trade import TradeMessage


class MarketStreamSocket(Protocol):
    """The pinned SDK subscription capability needed by Market Stream."""

    async def subscribe_orderbook_delta(
        self, *, tickers: list[str] | None = None, maxsize: int = 1000
    ) -> AsyncIterator[OrderbookSnapshotMessage | OrderbookDeltaMessage]: ...

    async def subscribe_ticker(
        self, *, tickers: list[str] | None = None, maxsize: int = 1000
    ) -> AsyncIterator[TickerMessage]: ...

    async def subscribe_trade(
        self, *, tickers: list[str] | None = None, maxsize: int = 1000
    ) -> AsyncIterator[TradeMessage]: ...

    async def subscribe_market_lifecycle(
        self, *, tickers: list[str] | None = None, maxsize: int = 1000
    ) -> AsyncIterator[MarketLifecycleMessage | EventFeeUpdateMessage]: ...
