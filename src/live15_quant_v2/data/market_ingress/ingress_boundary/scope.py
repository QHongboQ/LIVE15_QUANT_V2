"""Sole concrete LIVE15 nine-asset market-scope authority."""

from __future__ import annotations

from typing import TYPE_CHECKING

from live15_quant_v2.data.market_ingress.ingress_boundary.models import (
    MarketScopeBinding,
)

if TYPE_CHECKING:
    from live15_quant_v2.data.market_ingress.ingress_boundary.ports import (
        MarketScopePort,
    )

_BINDINGS = (
    MarketScopeBinding("BTC", "KXBTC15M"),
    MarketScopeBinding("ETH", "KXETH15M"),
    MarketScopeBinding("GOLD", "KXGOLD15M"),
    MarketScopeBinding("SILVER", "KXSILVER15M"),
    MarketScopeBinding("XRP", "KXXRP15M"),
    MarketScopeBinding("SOL", "KXSOL15M"),
    MarketScopeBinding("HYPE", "KXHYPE15M"),
    MarketScopeBinding("DOGE", "KXDOGE15M"),
    MarketScopeBinding("BNB", "KXBNB15M"),
)

if len({binding.asset_id for binding in _BINDINGS}) != 9 or len(
    {binding.series_ticker for binding in _BINDINGS}
) != 9:
    raise RuntimeError("LIVE15 market-scope bindings must be bijective")


class Live15MarketScopeConfig:
    """Immutable exact LIVE15 asset-to-Kalshi-series scope."""

    __slots__ = ()

    @property
    def bindings(self) -> tuple[MarketScopeBinding, ...]:
        return _BINDINGS

    def binding_for_asset(self, asset_id: str) -> MarketScopeBinding | None:
        return next((binding for binding in _BINDINGS if binding.asset_id == asset_id), None)

    def binding_for_series(self, series_ticker: str) -> MarketScopeBinding | None:
        return next(
            (binding for binding in _BINDINGS if binding.series_ticker == series_ticker),
            None,
        )


if TYPE_CHECKING:
    _market_scope_port_check: MarketScopePort = Live15MarketScopeConfig()
