import inspect
from datetime import UTC, datetime, timedelta
from decimal import Decimal
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
    MarketScopeBinding,
    OfficialStrike,
    ShadowStatus,
    VerificationStatus,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.resolver import (
    MarketIdentityResolver,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.shadow import (
    ShadowValidator,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.verification import (
    OfficialMarketVerifier,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.window import (
    current,
    next_window,
)


class Scope:
    def __init__(self,*bindings:MarketScopeBinding)->None:self.bindings={b.asset_id:b for b in bindings}
    def binding_for_asset(self,asset_id:str)->MarketScopeBinding|None:return self.bindings.get(asset_id)
    def binding_for_series(self,series_ticker:str)->MarketScopeBinding|None:return next((b for b in self.bindings.values() if b.series_ticker==series_ticker),None)
class FakeMarkets:
    def __init__(self,fetched:object|None,listed:list[object])->None:self.fetched,self.listed,self.calls=fetched,listed,[]
    def get(self,ticker:str)->object:
        self.calls.append(("get",ticker))
        if self.fetched is None: raise KalshiNotFoundError("missing")
        return self.fetched
    def list_all(self,**kwargs:object)->list[object]:self.calls.append(("list",kwargs));return self.listed
class FakeClient:
    def __init__(self,markets:FakeMarkets)->None:self.markets=markets

def window(hour:int=20,minute:int=15):return current(datetime(2026,3,23,hour,minute,tzinfo=UTC))
def binding()->MarketScopeBinding:return MarketScopeBinding("asset-under-test","KXDOGE15M")
def raw(value,*,ticker="KXDOGE15M-26MAR231630-30",floor=Decimal(1),cap=None,functional="x**2"):
    return SimpleNamespace(ticker=ticker,event_ticker="KXDOGE15M-26MAR231630",open_time=value.open_time,close_time=value.close_time,strike_type="greater",floor_strike=floor,cap_strike=cap,yes_sub_title="official",functional_strike=functional)
def market(value,*,strike=None,close_time=None,b=None):
    b=b or binding();strike=strike or OfficialStrike("greater",Decimal(1),None,"official")
    return DiscoveredMarket(b,"KXDOGE15M-26MAR231630-30","KXDOGE15M-26MAR231630",value.open_time,close_time or value.close_time,strike)

def test_windows_are_quarter_hour_aware_and_contiguous()->None:
    value=current(datetime(2026,3,23,20,29,59,tzinfo=UTC));assert value.open_time.minute==15;assert next_window(value).open_time==value.close_time
    with pytest.raises(ValueError): current(datetime(2026,1,1,tzinfo=UTC).replace(tzinfo=None))
def test_candidate_uses_close_time_format_and_is_heuristic()->None:
    predictor=CandidateTickerPredictor();value=window();candidate=predictor.predict(binding(),value)
    assert candidate.ticker=="KXDOGE15M-26MAR231630-30";assert candidate.window.close_time==datetime(2026,3,23,20,30,tzinfo=UTC)
def test_candidate_cross_midnight_and_dst_are_et_safe()->None:
    p=CandidateTickerPredictor();b=MarketScopeBinding("x","KXBTC15M")
    midnight=current(datetime(2026,4,1,0,45,tzinfo=UTC));assert p.predict(b,midnight).ticker=="KXBTC15M-26MAR312100-00"
    spring=current(datetime(2026,3,8,6,45,tzinfo=UTC));fall=current(datetime(2026,11,1,5,45,tzinfo=UTC))
    assert "-" in p.predict(b,spring).ticker and "-" in p.predict(b,fall).ticker
def test_discovery_candidate_miss_uses_bounded_documented_series_filters()->None:
    value=window();fake=FakeMarkets(None,[raw(value)]);found=OfficialMarketDiscovery(KalshiGateway(FakeClient(fake))).discover(binding=binding(),window=value,candidate=CandidateTicker(binding(),"missing",value))
    kwargs=fake.calls[-1][1];assert len(found)==1;assert kwargs["series_ticker"]=="KXDOGE15M";assert "status" not in kwargs
    assert kwargs["min_close_ts"]<int(value.close_time.timestamp())<kwargs["max_close_ts"]
def test_functional_strike_is_metadata_not_target_truth()->None:
    value=window();found=OfficialMarketDiscovery(KalshiGateway(FakeClient(FakeMarkets(raw(value,floor=None,cap=None,functional="x**2"),[])))).discover(binding=binding(),window=value,candidate=CandidateTicker(binding(),"candidate",value))
    result=OfficialMarketVerifier().verify(scope=Scope(binding()),binding=binding(),window=value,markets=found);assert result.status is VerificationStatus.INVALID;assert found[0].strike.functional_strike=="x**2"
def test_structured_floor_cap_and_range_are_retained()->None:
    value=window();scope=Scope(binding());verifier=OfficialMarketVerifier()
    for strike in (OfficialStrike("greater",Decimal(1),None,"x"),OfficialStrike("less",None,Decimal(2),"x"),OfficialStrike("between",Decimal(1),Decimal(2),"x")):
        assert verifier.verify(scope=scope,binding=binding(),window=value,markets=[market(value,strike=strike)]).verified
def test_verification_rejects_sibling_ambiguous_adjacent_and_unknown_scope()->None:
    value=window();verifier=OfficialMarketVerifier();scope=Scope(binding())
    sibling=market(next_window(value));missing=market(value,strike=OfficialStrike("x",None,None,"x"))
    assert verifier.verify(scope=scope,binding=binding(),window=value,markets=[sibling,missing]).status is VerificationStatus.INVALID
    assert verifier.verify(scope=scope,binding=binding(),window=value,markets=[market(value),market(value)]).status is VerificationStatus.AMBIGUOUS
    assert verifier.verify(scope=scope,binding=binding(),window=value,markets=[market(value,close_time=value.close_time+timedelta(minutes=15))]).status is VerificationStatus.NO_MATCH
    assert verifier.verify(scope=Scope(),binding=binding(),window=value,markets=[market(value)]).status is VerificationStatus.INVALID
def test_resolver_composes_leaves_and_shadow_mismatch_preserves_truth()->None:
    value=window();b=binding();scope=Scope(b);fake=FakeMarkets(raw(value,ticker="KXDOGE15M-26MAR231630-99"),[])
    resolver=MarketIdentityResolver(scope,CandidateTickerPredictor(),OfficialMarketDiscovery(KalshiGateway(FakeClient(fake))),OfficialMarketVerifier(),ShadowValidator())
    resolution=resolver.resolve(b.asset_id,value);assert resolution.verification.verified;assert resolution.shadow.status is ShadowStatus.MISMATCH
    unknown=resolver.resolve("unknown",value);assert unknown.verification.status is VerificationStatus.INVALID and fake.calls
def test_shadow_never_authorizes_candidate()->None:
    value=window();candidate=CandidateTicker(binding(),"hint",value);result=ShadowValidator().compare(candidate=candidate,verification=OfficialMarketVerifier().verify(scope=Scope(binding()),binding=binding(),window=value,markets=[]));assert result.status is ShadowStatus.OFFICIAL_MISSING
def test_gateway_uses_installed_public_sdk_market_signatures() -> None:
    client = KalshiClient()
    parameters = inspect.signature(client.markets.list_all).parameters
    assert {"series_ticker", "min_close_ts", "max_close_ts"} <= set(parameters)
    assert "status" in parameters
    assert hasattr(client.markets, "get")
    client.close()