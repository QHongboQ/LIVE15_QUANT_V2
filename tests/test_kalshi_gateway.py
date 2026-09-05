import inspect
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import get_type_hints

from kalshi import KalshiClient
from kalshi.ws import KalshiWebSocket

import live15_quant_v2.data.market_ingress.kalshi_gateway as gateway_public
from live15_quant_v2.data.market_ingress import market_identity_resolver
from live15_quant_v2.data.market_ingress.ingress_boundary import (
    MarketIdentityResolver,
    MarketScopeBinding,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.candidate import (
    CandidateTickerPredictor,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.discovery import (
    OfficialMarketDiscovery,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.models import (
    DiscoveredMarket,
    OfficialStrike,
    ShadowStatus,
    VerificationStatus,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.shadow import ShadowValidator
from live15_quant_v2.data.market_ingress.ingress_boundary.verification import (
    OfficialMarketVerifier,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.window import (
    current,
    next_window,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway import KalshiGateway


class Scope:
    def __init__(self, *bindings: MarketScopeBinding) -> None:
        self.bindings = {binding.asset_id: binding for binding in bindings}

    def binding_for_asset(self, asset_id: str) -> MarketScopeBinding | None:
        return self.bindings.get(asset_id)

    def binding_for_series(self, series_ticker: str) -> MarketScopeBinding | None:
        return next(
            (
                binding
                for binding in self.bindings.values()
                if binding.series_ticker == series_ticker
            ),
            None,
        )


class Markets:
    def __init__(self, items: list[object]) -> None:
        self.items = items
        self.kwargs: dict[str, object] | None = None

    def get(self, ticker: str) -> object:
        raise AssertionError("candidate must not fetch truth")

    def list_all(self, **kwargs: object) -> list[object]:
        self.kwargs = kwargs
        return self.items


class Client:
    def __init__(self, markets: Markets) -> None:
        self.markets = markets


def binding() -> MarketScopeBinding:
    return MarketScopeBinding("asset", "KXDOGE15M")


def window():
    return current(datetime(2026, 3, 23, 20, 15, tzinfo=UTC))


def raw(w, floor=Decimal(1), cap=None):
    return SimpleNamespace(
        ticker="official-ticker",
        event_ticker="official-event",
        open_time=w.open_time,
        close_time=w.close_time,
        strike_type="greater",
        floor_strike=floor,
        cap_strike=cap,
        yes_sub_title="official",
        functional_strike="x**2",
    )


def discovered(w, series="KXDOGE15M", strike=None):
    return DiscoveredMarket(
        series,
        "official-ticker",
        "official-event",
        w.open_time,
        w.close_time,
        strike or OfficialStrike("greater", Decimal(1), None, "official", "x**2"),
    )


def test_gateway_public_surface_is_provider_only_and_ws_is_typed() -> None:
    assert gateway_public.__all__ == ["KalshiGateway"]
    assert not hasattr(gateway_public, "MarketScopeBinding")
    assert get_type_hints(KalshiGateway.subscription_access)["return"] is KalshiWebSocket


def test_candidate_is_close_time_heuristic_and_unknown_omits():
    w = window()
    predictor = CandidateTickerPredictor()
    assert predictor.predict(binding(), w).ticker == "KXDOGE15M-26MAR231630-30"
    assert predictor.predict(MarketScopeBinding("x", "OTHER"), w) is None
    assert next_window(w).open_time == w.close_time


def test_official_discovery_is_only_bounded_series_query():
    w = window()
    markets = Markets([raw(w)])
    found = OfficialMarketDiscovery(KalshiGateway(Client(markets))).discover(
        binding=binding(), window=w
    )
    assert found[0].observed_series_ticker == binding().series_ticker
    assert markets.kwargs is not None
    assert markets.kwargs["series_ticker"] == binding().series_ticker
    assert "status" not in markets.kwargs
    assert (
        markets.kwargs["min_close_ts"]
        < int(w.close_time.timestamp())
        < markets.kwargs["max_close_ts"]
    )


def test_wrong_official_series_rejected_even_with_exact_time_and_strike():
    w = window()
    result = OfficialMarketVerifier().verify(
        scope=Scope(binding()),
        binding=binding(),
        window=w,
        markets=[discovered(w, "SERIES_B")],
    )
    assert result.status is VerificationStatus.NO_MATCH


def test_functional_strike_never_authorizes_and_structured_strikes_do():
    w = window()
    verifier = OfficialMarketVerifier()
    scope = Scope(binding())
    result = verifier.verify(
        scope=scope,
        binding=binding(),
        window=w,
        markets=[discovered(w, strike=OfficialStrike("x", None, None, "yes", "x**2"))],
    )
    assert result.status is VerificationStatus.INVALID
    for strike in (
        OfficialStrike("x", Decimal(1), None, "yes"),
        OfficialStrike("x", None, Decimal(2), "yes"),
        OfficialStrike("x", Decimal(1), Decimal(2), "yes"),
    ):
        assert verifier.verify(
            scope=scope,
            binding=binding(),
            window=w,
            markets=[discovered(w, strike=strike)],
        ).verified


def test_adjacent_ambiguous_and_sibling_strike_fail_closed():
    w = window()
    verifier = OfficialMarketVerifier()
    scope = Scope(binding())
    adjacent = DiscoveredMarket(
        binding().series_ticker,
        "x",
        "e",
        w.open_time,
        w.close_time + timedelta(minutes=15),
        OfficialStrike("x", Decimal(1), None, "yes"),
    )
    assert (
        verifier.verify(
            scope=scope, binding=binding(), window=w, markets=[adjacent]
        ).status
        is VerificationStatus.NO_MATCH
    )
    assert (
        verifier.verify(
            scope=scope,
            binding=binding(),
            window=w,
            markets=[discovered(w), discovered(w)],
        ).status
        is VerificationStatus.AMBIGUOUS
    )
    assert (
        verifier.verify(
            scope=scope,
            binding=binding(),
            window=w,
            markets=[
                discovered(next_window(w)),
                discovered(w, strike=OfficialStrike("x", None, None, "yes")),
            ],
        ).status
        is VerificationStatus.INVALID
    )


def test_resolver_candidate_shadow_is_diagnostic_not_truth():
    w = window()
    scope_binding = binding()
    markets = Markets([raw(w)])
    resolver = MarketIdentityResolver(
        Scope(scope_binding),
        CandidateTickerPredictor(),
        OfficialMarketDiscovery(KalshiGateway(Client(markets))),
        OfficialMarketVerifier(),
        ShadowValidator(),
    )
    out = resolver.resolve("asset", w)
    assert out.verification.verified
    assert out.shadow.status is ShadowStatus.MISMATCH


def test_market_ingress_parent_composes_sibling_public_interfaces_offline():
    w = window()
    resolver = market_identity_resolver(
        Scope(binding()), KalshiGateway(Client(Markets([raw(w)])))
    )

    result = resolver.resolve("asset", w)

    assert result.verification.verified
    assert result.shadow.status is ShadowStatus.MISMATCH

def test_installed_sdk_has_documented_public_parameters():
    client = KalshiClient()
    params = inspect.signature(client.markets.list_all).parameters
    assert {"series_ticker", "min_close_ts", "max_close_ts"} <= set(params)
    client.close()
