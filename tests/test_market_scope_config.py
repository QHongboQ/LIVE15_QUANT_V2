from datetime import UTC, datetime

import pytest

from live15_quant_v2.data.market_ingress.ingress_boundary import (
    CandidateTickerPredictor,
    Live15MarketScopeConfig,
    MarketIdentityResolver,
    MarketScopePort,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.discovery import (
    OfficialMarketDiscovery,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.models import (
    VerificationStatus,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.shadow import ShadowValidator
from live15_quant_v2.data.market_ingress.ingress_boundary.verification import (
    OfficialMarketVerifier,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.window import current
from live15_quant_v2.data.market_ingress.kalshi_gateway import KalshiGateway

EXPECTED = {
    "BTC": "KXBTC15M",
    "ETH": "KXETH15M",
    "GOLD": "KXGOLD15M",
    "SILVER": "KXSILVER15M",
    "XRP": "KXXRP15M",
    "SOL": "KXSOL15M",
    "HYPE": "KXHYPE15M",
    "DOGE": "KXDOGE15M",
    "BNB": "KXBNB15M",
}


class _EmptyMarkets:
    def list_all(self, **kwargs: object) -> list[object]:
        return []

    def get(self, ticker: str) -> object:
        raise AssertionError("candidate ticker must not authorize truth")


class _EmptyClient:
    def __init__(self) -> None:
        self.markets = _EmptyMarkets()


def _accept_scope_port(scope: MarketScopePort) -> MarketScopePort:
    return scope


def test_nine_asset_bijective_scope_is_immutable_and_public() -> None:
    config = Live15MarketScopeConfig()
    assert len(config.bindings) == 9
    assert len(EXPECTED) == 9
    assert config.binding_for_asset("WTI") is None

    for asset, series in EXPECTED.items():
        binding = config.binding_for_asset(asset)
        assert binding is not None
        assert binding.series_ticker == series
        assert config.binding_for_series(series) == binding

    assert config.binding_for_asset("UNKNOWN") is None
    assert config.binding_for_series("UNKNOWN") is None
    assert _accept_scope_port(config) is config

    with pytest.raises(AttributeError):
        config.bindings = ()  # type: ignore[misc]
    with pytest.raises(TypeError):
        Live15MarketScopeConfig(bindings=())  # type: ignore[call-arg]


def test_concrete_scope_plugs_into_existing_resolver_without_framework_changes() -> None:
    config = Live15MarketScopeConfig()
    resolver = MarketIdentityResolver(
        config,
        CandidateTickerPredictor(),
        OfficialMarketDiscovery(KalshiGateway(_EmptyClient())),
        OfficialMarketVerifier(),
        ShadowValidator(),
    )
    window = current(datetime(2026, 9, 4, 22, 15, tzinfo=UTC))

    resolution = resolver.resolve("BTC", window)

    assert resolution.candidate is not None
    assert resolution.verification.status is VerificationStatus.NO_MATCH
