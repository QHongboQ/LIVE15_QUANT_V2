import inspect
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from kalshi import KalshiClient

from live15_quant_v2.data.market_ingress.kalshi_gateway import (
 KalshiGateway,
 MarketIdentityResolver,
 MarketScopeBinding,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.candidate import (
 CandidateTickerPredictor,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.discovery import (
 OfficialMarketDiscovery,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.models import (
 DiscoveredMarket,
 OfficialStrike,
 ShadowStatus,
 VerificationStatus,
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
 def __init__(self,*bs):self.bs={b.asset_id:b for b in bs}
 def binding_for_asset(self,a):return self.bs.get(a)
 def binding_for_series(self,s):return next((b for b in self.bs.values() if b.series_ticker==s),None)
class Markets:
 def __init__(self,items):self.items=items;self.kwargs=None
 def get(self,t):raise AssertionError('candidate must not fetch truth')
 def list_all(self,**kwargs):self.kwargs=kwargs;return self.items
class Client:
 def __init__(self,m):self.markets=m
def binding():return MarketScopeBinding('asset','KXDOGE15M')
def window():return current(datetime(2026,3,23,20,15,tzinfo=UTC))
def raw(w,floor=Decimal(1),cap=None):return SimpleNamespace(ticker='official-ticker',event_ticker='official-event',open_time=w.open_time,close_time=w.close_time,strike_type='greater',floor_strike=floor,cap_strike=cap,yes_sub_title='official',functional_strike='x**2')
def discovered(w,series='KXDOGE15M',strike=None):return DiscoveredMarket(series,'official-ticker','official-event',w.open_time,w.close_time,strike or OfficialStrike('greater',Decimal(1),None,'official','x**2'))
def test_candidate_is_close_time_heuristic_and_unknown_omits():
 w=window();p=CandidateTickerPredictor();assert p.predict(binding(),w).ticker=='KXDOGE15M-26MAR231630-30';assert p.predict(MarketScopeBinding('x','OTHER'),w) is None
 assert next_window(w).open_time==w.close_time
def test_official_discovery_is_only_bounded_series_query():
 w=window();m=Markets([raw(w)]);found=OfficialMarketDiscovery(KalshiGateway(Client(m))).discover(binding=binding(),window=w)
 assert found[0].observed_series_ticker==binding().series_ticker;assert m.kwargs['series_ticker']==binding().series_ticker;assert 'status' not in m.kwargs;assert m.kwargs['min_close_ts']<int(w.close_time.timestamp())<m.kwargs['max_close_ts']
def test_wrong_official_series_rejected_even_with_exact_time_and_strike():
 w=window();r=OfficialMarketVerifier().verify(scope=Scope(binding()),binding=binding(),window=w,markets=[discovered(w,'SERIES_B')]);assert r.status is VerificationStatus.NO_MATCH
def test_functional_strike_never_authorizes_and_structured_strikes_do():
 w=window();v=OfficialMarketVerifier();s=Scope(binding());assert v.verify(scope=s,binding=binding(),window=w,markets=[discovered(w,strike=OfficialStrike('x',None,None,'yes','x**2'))]).status is VerificationStatus.INVALID
 for strike in (OfficialStrike('x',Decimal(1),None,'yes'),OfficialStrike('x',None,Decimal(2),'yes'),OfficialStrike('x',Decimal(1),Decimal(2),'yes')):assert v.verify(scope=s,binding=binding(),window=w,markets=[discovered(w,strike=strike)]).verified
def test_adjacent_ambiguous_and_sibling_strike_fail_closed():
 w=window();v=OfficialMarketVerifier();s=Scope(binding());adj=DiscoveredMarket(binding().series_ticker,'x','e',w.open_time,w.close_time+timedelta(minutes=15),OfficialStrike('x',Decimal(1),None,'yes'))
 assert v.verify(scope=s,binding=binding(),window=w,markets=[adj]).status is VerificationStatus.NO_MATCH
 assert v.verify(scope=s,binding=binding(),window=w,markets=[discovered(w),discovered(w)]).status is VerificationStatus.AMBIGUOUS
 assert v.verify(scope=s,binding=binding(),window=w,markets=[discovered(next_window(w)),discovered(w,strike=OfficialStrike('x',None,None,'yes'))]).status is VerificationStatus.INVALID
def test_resolver_candidate_shadow_is_diagnostic_not_truth():
 w=window();b=binding();m=Markets([raw(w)]);resolver=MarketIdentityResolver(Scope(b),CandidateTickerPredictor(),OfficialMarketDiscovery(KalshiGateway(Client(m))),OfficialMarketVerifier(),ShadowValidator());out=resolver.resolve('asset',w);assert out.verification.verified;assert out.shadow.status is ShadowStatus.MISMATCH
def test_installed_sdk_has_documented_public_parameters():
 c=KalshiClient();params=inspect.signature(c.markets.list_all).parameters;assert {'series_ticker','min_close_ts','max_close_ts'}<=set(params);c.close()