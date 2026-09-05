"""Typed Pyth streaming through the SDK's public generic subscription."""

from collections.abc import AsyncIterator
from typing import cast

from kalshi.ws import KalshiWebSocket
from kalshi.ws.backpressure import OverflowStrategy

from live15_quant_v2.data.market_ingress.reference_stream.pyth_value.models import (
    PythUnderlyingListMessage,
    PythValueMessage,
)
from live15_quant_v2.data.market_ingress.reference_stream.pyth_value.sdk_compat import (
    install_pyth_sdk_compat,
)
from live15_quant_v2.data.market_ingress.reference_stream.scope import (
    ReferenceBinding,
    ReferenceSource,
)


class PythValueStream:
    def __init__(self, websocket: KalshiWebSocket) -> None:
        self._websocket = websocket

    async def subscribe(
        self, bindings: tuple[ReferenceBinding, ...]
    ) -> AsyncIterator[PythValueMessage | PythUnderlyingListMessage]:
        if not bindings or any(
            binding.source is not ReferenceSource.PYTH_VALUE for binding in bindings
        ):
            raise ValueError("Pyth Value requires approved Pyth reference bindings")
        install_pyth_sdk_compat()
        stream = await self._websocket.subscribe(
            "pyth_value",
            params={
                "underlying_tickers": [binding.provider_id for binding in bindings]
            },
            overflow=OverflowStrategy.ERROR,
        )
        return cast(AsyncIterator[PythValueMessage | PythUnderlyingListMessage], stream)
