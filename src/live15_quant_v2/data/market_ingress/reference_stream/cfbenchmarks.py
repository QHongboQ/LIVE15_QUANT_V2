"""SDK-native CF Benchmarks streaming for approved LIVE15 references."""

from collections.abc import AsyncIterator

from kalshi.ws import KalshiWebSocket
from kalshi.ws.models.cfbenchmarks import (
    CFBenchmarksIndexListMessage,
    CFBenchmarksValueMessage,
)

from live15_quant_v2.data.market_ingress.reference_stream.scope import (
    ReferenceBinding,
    ReferenceSource,
)


class CFBenchmarksStream:
    def __init__(self, websocket: KalshiWebSocket) -> None:
        self._websocket = websocket

    async def subscribe(
        self, bindings: tuple[ReferenceBinding, ...]
    ) -> AsyncIterator[CFBenchmarksValueMessage | CFBenchmarksIndexListMessage]:
        if not bindings or any(
            binding.source is not ReferenceSource.CF_BENCHMARKS for binding in bindings
        ):
            raise ValueError("CF Benchmarks requires approved CF reference bindings")
        return await self._websocket.subscribe_cfbenchmarks_value(
            index_ids=[binding.provider_id for binding in bindings]
        )
