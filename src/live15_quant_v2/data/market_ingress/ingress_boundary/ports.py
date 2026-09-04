"""Ingress Boundary scope port."""

from typing import Protocol

from live15_quant_v2.data.market_ingress.ingress_boundary.models import (
    MarketScopeBinding,
)


class MarketScopePort(Protocol):
    def binding_for_asset(self, asset_id: str) -> MarketScopeBinding | None: ...

    def binding_for_series(self, series_ticker: str) -> MarketScopeBinding | None: ...
