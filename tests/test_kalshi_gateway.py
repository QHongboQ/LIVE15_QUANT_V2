from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from kalshi import KalshiClient
from kalshi.errors import KalshiNotFoundError

from live15_quant_v2.data.market_ingress.kalshi_gateway.gateway import KalshiGateway
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.candidate import (
    CandidateTickerPredictor,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.discovery import (
    OfficialMarketDiscovery,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.models import (
    CandidateTicker,
    DiscoveredMarket,
    MarketWindow,
    ShadowStatus,
    VerificationStatus,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.shadow import (
    ShadowValidator,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.verification import (
    OfficialMarketVerifier,
)


class ApprovedScope:
    def __init__(self, *series: str) -> None:
        self._series = set(series)

    def approves_series(self, series_ticker: str) -> bool:
        return series_ticker in self._series


class FakeMarkets:
    def __init__(self, fetched: object | None, discovered: list[object]) -> None:
        self.fetched = fetched
        self.discovered = discovered
        self.get_calls: list[str] = []
        self.list_calls: list[str] = []

    def get(self, ticker: str) -> object:
        self.get_calls.append(ticker)
        if self.fetched is None:
            raise KalshiNotFoundError("not found")
        return self.fetched

    def list_all(self, *, series_ticker: str) -> list[object]:
        self.list_calls.append(series_ticker)
        return self.discovered


class FakeClient:
    def __init__(self, markets: FakeMarkets) -> None:
        self.markets = markets


def window(hour: int = 12, minute: int = 0) -> MarketWindow:
    return MarketWindow.current(datetime(2024, 3, 10, hour, minute, tzinfo=UTC))


def market_for(
    series: str,
    value: MarketWindow,
    *,
    target: str | None = "100",
    ticker: str | None = None,
    event_ticker: str | None = None,
    open_time: datetime | None = None,
    close_time: datetime | None = None,
) -> DiscoveredMarket:
    event = event_ticker or f"{series}-EVENT"
    return DiscoveredMarket(
        series_ticker=series,
        ticker=ticker or f"{event}-YES",
        event_ticker=event,
        open_time=open_time or value.open_time,
        close_time=close_time or value.close_time,
        target=target,
    )


def sdk_market(value: MarketWindow, *, ticker: str = "SERIES-EVENT-YES") -> object:
    return SimpleNamespace(
        ticker=ticker,
        event_ticker="SERIES-EVENT",
        open_time=value.open_time,
        close_time=value.close_time,
        functional_strike="100",
        floor_strike=None,
        cap_strike=None,
    )


def test_window_rounding_boundary_and_contiguity() -> None:
    ordinary = MarketWindow.current(datetime(2024, 1, 1, 12, 14, 59, tzinfo=UTC))
    boundary = MarketWindow.current(datetime(2024, 1, 1, 12, 15, tzinfo=UTC))
    assert ordinary.open_time == datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    assert boundary.open_time == datetime(2024, 1, 1, 12, 15, tzinfo=UTC)
    assert ordinary.next().open_time == ordinary.close_time
    assert ordinary.close_time - ordinary.open_time == timedelta(minutes=15)


def test_window_crosses_hour_midnight_and_requires_aware_time() -> None:
    cross_hour = MarketWindow.current(datetime(2024, 1, 1, 12, 59, tzinfo=UTC))
    midnight = MarketWindow.current(datetime(2024, 1, 1, 23, 59, tzinfo=UTC))
    assert cross_hour.close_time == datetime(2024, 1, 1, 13, 0, tzinfo=UTC)
    assert midnight.close_time == datetime(2024, 1, 2, 0, 0, tzinfo=UTC)
    with pytest.raises(ValueError):
        MarketWindow.current(datetime(2024, 1, 1, 12, 0, tzinfo=UTC).replace(tzinfo=None))


def test_candidate_uses_injected_series_and_dst_safe_new_york_time() -> None:
    predictor = CandidateTickerPredictor()
    spring = MarketWindow.current(datetime(2024, 3, 10, 7, 0, tzinfo=UTC))
    fall = MarketWindow.current(datetime(2024, 11, 3, 6, 0, tzinfo=UTC))
    candidate = predictor.predict("KXBTC15M", spring)
    assert candidate.ticker == "KXBTC15M-24MAR100300"
    assert candidate.__class__.__name__ == "CandidateTicker"
    assert predictor.predict("KXBTC15M", fall).ticker == "KXBTC15M-24NOV030100"
    assert predictor.predict("OTHER", spring).ticker.startswith("OTHER-")


def test_gateway_uses_real_sdk_public_market_surface_without_network() -> None:
    real_client = KalshiClient()
    assert hasattr(real_client.markets, "get")
    assert hasattr(real_client.markets, "list_all")
    fake_markets = FakeMarkets("one", ["one", "two"])
    gateway = KalshiGateway(FakeClient(fake_markets))
    assert gateway.fetch_market("ONE") == "one"
    assert gateway.discover_markets("SERIES") == ("one", "two")
    assert fake_markets.get_calls == ["ONE"]
    assert fake_markets.list_calls == ["SERIES"]
    real_client.close()


def test_official_discovery_uses_candidate_then_exact_series_fallback() -> None:
    value = window()
    raw = sdk_market(value)
    fake_markets = FakeMarkets(raw, [raw])
    discovery = OfficialMarketDiscovery(KalshiGateway(FakeClient(fake_markets)))
    candidate = CandidateTicker("SERIES", "SERIES-EVENT-YES", value)
    discovered = discovery.discover(series_ticker="SERIES", candidate=candidate)
    assert [item.ticker for item in discovered] == ["SERIES-EVENT-YES"]
    assert fake_markets.get_calls == ["SERIES-EVENT-YES"]
    assert fake_markets.list_calls == ["SERIES"]


def test_verification_accepts_one_exact_official_market_only() -> None:
    value = window()
    result = OfficialMarketVerifier().verify(
        scope=ApprovedScope("SERIES"),
        series_ticker="SERIES",
        window=value,
        markets=[market_for("SERIES", value)],
    )
    assert result.status is VerificationStatus.VERIFIED
    assert result.identity is not None


@pytest.mark.parametrize("target", [None, "TBD", "unknown", "bad\ntarget"])
def test_verification_rejects_unpublished_or_malformed_target(target: str | None) -> None:
    value = window()
    result = OfficialMarketVerifier().verify(
        scope=ApprovedScope("SERIES"),
        series_ticker="SERIES",
        window=value,
        markets=[market_for("SERIES", value, target=target)],
    )
    assert result.status is VerificationStatus.INVALID


def test_verification_fails_closed_for_zero_ambiguous_wrong_series_and_wrong_times() -> None:
    value = window()
    verifier = OfficialMarketVerifier()
    scope = ApprovedScope("SERIES")
    assert verifier.verify(scope=scope, series_ticker="SERIES", window=value, markets=[]).status is VerificationStatus.NO_MATCH
    assert verifier.verify(
        scope=scope,
        series_ticker="SERIES",
        window=value,
        markets=[market_for("SERIES", value), market_for("SERIES", value, ticker="SERIES-EVENT-NO")],
    ).status is VerificationStatus.AMBIGUOUS
    assert verifier.verify(
        scope=scope, series_ticker="SERIES", window=value, markets=[market_for("OTHER", value)]
    ).status is VerificationStatus.NO_MATCH
    assert verifier.verify(
        scope=scope,
        series_ticker="SERIES",
        window=value,
        markets=[market_for("SERIES", value, open_time=value.open_time + timedelta(minutes=15))],
    ).status is VerificationStatus.NO_MATCH
    assert verifier.verify(
        scope=scope,
        series_ticker="SERIES",
        window=value,
        markets=[market_for("SERIES", value, close_time=value.close_time + timedelta(minutes=15))],
    ).status is VerificationStatus.NO_MATCH


def test_verification_never_borrows_a_sibling_target_or_first_open_market() -> None:
    value = window()
    sibling = market_for("SERIES", value.next(), target="100")
    targetless = market_for("SERIES", value, target=None)
    result = OfficialMarketVerifier().verify(
        scope=ApprovedScope("SERIES"),
        series_ticker="SERIES",
        window=value,
        markets=[sibling, targetless],
    )
    assert result.status is VerificationStatus.INVALID


def test_shadow_statuses_are_pure_comparisons() -> None:
    value = window()
    candidate = CandidateTicker("SERIES", "SERIES-EVENT-YES", value)
    verified = OfficialMarketVerifier().verify(
        scope=ApprovedScope("SERIES"),
        series_ticker="SERIES",
        window=value,
        markets=[market_for("SERIES", value)],
    )
    validator = ShadowValidator()
    assert validator.compare(candidate=candidate, verification=verified).status is ShadowStatus.MATCH
    other = CandidateTicker("SERIES", "SERIES-OTHER", value)
    assert validator.compare(candidate=other, verification=verified).status is ShadowStatus.MISMATCH
    missing = verifier_result(VerificationStatus.NO_MATCH)
    assert validator.compare(candidate=candidate, verification=missing).status is ShadowStatus.OFFICIAL_MISSING
    invalid = verifier_result(VerificationStatus.INVALID)
    assert validator.compare(candidate=candidate, verification=invalid).status is ShadowStatus.VERIFICATION_FAILED
    assert validator.compare(candidate=None, verification=verified).status is ShadowStatus.CANDIDATE_MISSING


def verifier_result(status: VerificationStatus):
    from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.models import (
        VerificationResult,
    )

    return VerificationResult(status)