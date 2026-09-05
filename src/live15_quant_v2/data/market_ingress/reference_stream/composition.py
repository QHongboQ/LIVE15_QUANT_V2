"""Public composition of approved LIVE15 reference streams."""

from collections.abc import AsyncIterator

from kalshi.ws import KalshiWebSocket
from kalshi.ws.models.cfbenchmarks import (
    CFBenchmarksIndexListMessage,
    CFBenchmarksValueMessage,
)

from live15_quant_v2.data.market_ingress.reference_stream.cfbenchmarks import (
    CFBenchmarksStream,
)
from live15_quant_v2.data.market_ingress.reference_stream.pyth_value.models import (
    PythUnderlyingListMessage,
    PythValueMessage,
)
from live15_quant_v2.data.market_ingress.reference_stream.pyth_value.stream import (
    PythValueStream,
)
from live15_quant_v2.data.market_ingress.reference_stream.scope import (
    Live15ReferenceScopeConfig,
    ReferenceSource,
)


class ReferenceStream:
    """Expose typed reference streams selected exclusively by LIVE15 scope."""

    def __init__(self, websocket: KalshiWebSocket) -> None:
        self._scope = Live15ReferenceScopeConfig()
        self._cfbenchmarks = CFBenchmarksStream(websocket)
        self._pyth_value = PythValueStream(websocket)

    async def cfbenchmarks(
        self,
    ) -> AsyncIterator[CFBenchmarksValueMessage | CFBenchmarksIndexListMessage]:
        return await self._cfbenchmarks.subscribe(
            self._scope.bindings_for_source(ReferenceSource.CF_BENCHMARKS)
        )

    async def pyth_values(
        self,
    ) -> AsyncIterator[PythValueMessage | PythUnderlyingListMessage]:
        return await self._pyth_value.subscribe(
            self._scope.bindings_for_source(ReferenceSource.PYTH_VALUE)
        )
