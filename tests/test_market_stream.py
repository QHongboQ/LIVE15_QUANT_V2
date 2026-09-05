import asyncio
import inspect
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import get_args, get_origin, get_type_hints

import pytest
from kalshi.ws import KalshiWebSocket
from kalshi.ws.models.event_fee import EventFeeUpdateMessage
from kalshi.ws.models.market_lifecycle import MarketLifecycleMessage
from kalshi.ws.models.orderbook_delta import (
    OrderbookDeltaMessage,
    OrderbookSnapshotMessage,
)
from kalshi.ws.models.ticker import TickerMessage
from kalshi.ws.models.trade import TradeMessage

from live15_quant_v2.data.market_ingress.ingress_boundary import (
    MarketScopeBinding,
    MarketWindow,
    VerifiedMarketIdentity,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.models import (
    DiscoveredMarket,
    OfficialStrike,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.verification import (
    OfficialMarketVerifier,
)
from live15_quant_v2.data.market_ingress.market_stream import MarketStream


class FakeSocket:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str] | None]] = []
        self.orderbook_result = object()
        self.ticker_result = object()
        self.trade_result = object()
        self.lifecycle_result = object()

    async def subscribe_orderbook_delta(
        self, *, tickers: list[str] | None = None, maxsize: int = 1000
    ) -> object:
        self.calls.append(("orderbook", tickers))
        return self.orderbook_result

    async def subscribe_ticker(
        self, *, tickers: list[str] | None = None, maxsize: int = 1000
    ) -> object:
        self.calls.append(("ticker", tickers))
        return self.ticker_result

    async def subscribe_trade(
        self, *, tickers: list[str] | None = None, maxsize: int = 1000
    ) -> object:
        self.calls.append(("trade", tickers))
        return self.trade_result

    async def subscribe_market_lifecycle(
        self, *, tickers: list[str] | None = None, maxsize: int = 1000
    ) -> object:
        self.calls.append(("lifecycle", tickers))
        return self.lifecycle_result


class HandoffScope:
    def __init__(self, binding: MarketScopeBinding) -> None:
        self._binding = binding

    def binding_for_asset(self, asset_id: str) -> MarketScopeBinding | None:
        return self._binding if asset_id == self._binding.asset_id else None

    def binding_for_series(self, series_ticker: str) -> MarketScopeBinding | None:
        return self._binding if series_ticker == self._binding.series_ticker else None

def verified_identity() -> VerifiedMarketIdentity:
    window = MarketWindow(
        datetime(2026, 9, 4, 22, 15, tzinfo=UTC),
        datetime(2026, 9, 4, 22, 30, tzinfo=UTC),
    )
    return VerifiedMarketIdentity(
        MarketScopeBinding("BTC", "KXBTC15M"),
        "KXBTC15M-26SEP042215-99",
        "KXBTC15M-26SEP042215",
        window,
        OfficialStrike("greater", Decimal(99), None, "BTC above"),
    )


def test_orderbook_delegates_verified_ticker_and_preserves_sdk_result() -> None:
    socket = FakeSocket()
    result = asyncio.run(MarketStream(socket).orderbook(verified_identity()))

    assert result is socket.orderbook_result
    assert socket.calls == [("orderbook", [verified_identity().ticker])]


def test_ticker_delegates_verified_ticker_and_preserves_sdk_result() -> None:
    socket = FakeSocket()
    result = asyncio.run(MarketStream(socket).ticker(verified_identity()))

    assert result is socket.ticker_result
    assert socket.calls == [("ticker", [verified_identity().ticker])]


def test_trade_delegates_verified_ticker_and_preserves_sdk_result() -> None:
    socket = FakeSocket()
    result = asyncio.run(MarketStream(socket).trades(verified_identity()))

    assert result is socket.trade_result
    assert socket.calls == [("trade", [verified_identity().ticker])]


def test_lifecycle_delegates_verified_ticker_and_preserves_sdk_result() -> None:
    socket = FakeSocket()
    result = asyncio.run(MarketStream(socket).lifecycle(verified_identity()))

    assert result is socket.lifecycle_result
    assert socket.calls == [("lifecycle", [verified_identity().ticker])]


def test_candidate_or_asset_input_fails_closed_without_subscription() -> None:
    socket = FakeSocket()
    stream = MarketStream(socket)

    with pytest.raises(TypeError, match="VerifiedMarketIdentity"):
        asyncio.run(stream.ticker("KXBTC15M-candidate"))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="VerifiedMarketIdentity"):
        asyncio.run(stream.trades("BTC"))  # type: ignore[arg-type]

    assert socket.calls == []


def test_verified_identity_handoff_delegates_official_ticker_to_market_stream() -> None:
    binding = MarketScopeBinding("BTC", "KXBTC15M")
    window = MarketWindow(
        datetime(2026, 9, 4, 22, 15, tzinfo=UTC),
        datetime(2026, 9, 4, 22, 30, tzinfo=UTC),
    )
    verification = OfficialMarketVerifier().verify(
        scope=HandoffScope(binding),
        binding=binding,
        window=window,
        markets=[
            DiscoveredMarket(
                binding.series_ticker,
                "KXBTC15M-26SEP042215-99",
                "KXBTC15M-26SEP042215",
                window.open_time,
                window.close_time,
                OfficialStrike("greater", Decimal(99), None, "BTC above"),
            )
        ],
    )
    assert verification.verified
    assert verification.identity is not None

    socket = FakeSocket()
    result = asyncio.run(MarketStream(socket).ticker(verification.identity))

    assert result is socket.ticker_result
    assert socket.calls == [("ticker", [verification.identity.ticker])]
def test_pinned_sdk_subscription_contract_is_typed_and_async() -> None:
    expected = {
        "subscribe_orderbook_delta": {
            OrderbookSnapshotMessage,
            OrderbookDeltaMessage,
        },
        "subscribe_ticker": {TickerMessage},
        "subscribe_trade": {TradeMessage},
        "subscribe_market_lifecycle": {
            MarketLifecycleMessage,
            EventFeeUpdateMessage,
        },
    }

    for helper, message_types in expected.items():
        method = getattr(KalshiWebSocket, helper)
        signature = inspect.signature(method)
        annotation = get_type_hints(method)["return"]

        assert inspect.iscoroutinefunction(method)
        assert list(signature.parameters) == ["self", "tickers", "maxsize"]
        assert signature.parameters["tickers"].kind is inspect.Parameter.KEYWORD_ONLY
        assert signature.parameters["maxsize"].kind is inspect.Parameter.KEYWORD_ONLY
        assert signature.parameters["maxsize"].default == 1000
        assert get_origin(annotation) is AsyncIterator
        payload = get_args(annotation)[0]
        actual_message_types = set(get_args(payload)) or {payload}
        assert actual_message_types == message_types