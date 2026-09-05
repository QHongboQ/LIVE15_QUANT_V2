"""Sole immutable LIVE15 reference-source authority."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReferenceSource(StrEnum):
    CF_BENCHMARKS = "cf_benchmarks"
    PYTH_VALUE = "pyth_value"


@dataclass(frozen=True)
class ReferenceBinding:
    asset_id: str
    source: ReferenceSource
    provider_id: str

    def __post_init__(self) -> None:
        if not self.asset_id or not self.provider_id:
            raise ValueError("reference binding values must be non-empty")


_BINDINGS = (
    ReferenceBinding("BTC", ReferenceSource.CF_BENCHMARKS, "BRTI"),
    ReferenceBinding("ETH", ReferenceSource.CF_BENCHMARKS, "ETHUSD_RTI"),
    ReferenceBinding("GOLD", ReferenceSource.PYTH_VALUE, "Metal.XAU/USD"),
    ReferenceBinding("SILVER", ReferenceSource.PYTH_VALUE, "Metal.XAG/USD"),
    ReferenceBinding("XRP", ReferenceSource.CF_BENCHMARKS, "XRPUSD_RTI"),
    ReferenceBinding("SOL", ReferenceSource.CF_BENCHMARKS, "SOLUSD_RTI"),
    ReferenceBinding("HYPE", ReferenceSource.CF_BENCHMARKS, "HYPEUSD_RTI"),
    ReferenceBinding("DOGE", ReferenceSource.CF_BENCHMARKS, "DOGEUSD_RTI"),
    ReferenceBinding("BNB", ReferenceSource.CF_BENCHMARKS, "BNBUSD_RTI"),
)

if (
    len({binding.asset_id for binding in _BINDINGS}) != 9
    or len({binding.provider_id for binding in _BINDINGS}) != 9
):
    raise RuntimeError("LIVE15 reference bindings must be bijective")


class Live15ReferenceScopeConfig:
    """Immutable exact LIVE15 asset-to-reference-source scope."""

    __slots__ = ()

    @property
    def bindings(self) -> tuple[ReferenceBinding, ...]:
        return _BINDINGS

    def binding_for_asset(self, asset_id: str) -> ReferenceBinding | None:
        return next(
            (binding for binding in _BINDINGS if binding.asset_id == asset_id), None
        )

    def bindings_for_source(
        self, source: ReferenceSource
    ) -> tuple[ReferenceBinding, ...]:
        return tuple(binding for binding in _BINDINGS if binding.source is source)
