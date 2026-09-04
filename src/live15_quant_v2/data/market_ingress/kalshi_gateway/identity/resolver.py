"""One composition point for the Market Identity leaves."""
from dataclasses import dataclass

from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.candidate import (
    CandidateTickerPredictor,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.discovery import (
    OfficialMarketDiscovery,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.models import (
    CandidateTicker,
    MarketWindow,
    ShadowResult,
    VerificationResult,
    VerificationStatus,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.ports import (
    MarketScopePort,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.shadow import (
    ShadowValidator,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.verification import (
    OfficialMarketVerifier,
)


@dataclass(frozen=True)
class MarketIdentityResolution:
    candidate:CandidateTicker|None
    verification:VerificationResult
    shadow:ShadowResult
class MarketIdentityResolver:
    def __init__(self,scope:MarketScopePort,predictor:CandidateTickerPredictor,discovery:OfficialMarketDiscovery,verifier:OfficialMarketVerifier,shadow:ShadowValidator)->None: self._scope,self._predictor,self._discovery,self._verifier,self._shadow=scope,predictor,discovery,verifier,shadow
    def resolve(self,asset_id:str,window:MarketWindow)->MarketIdentityResolution:
        binding=self._scope.binding_for_asset(asset_id)
        if binding is None:
            verification=VerificationResult(VerificationStatus.INVALID,reason="unknown asset")
            return MarketIdentityResolution(None,verification,self._shadow.compare(candidate=None,verification=verification))
        candidate=self._predictor.predict(binding,window)
        markets=self._discovery.discover(binding=binding,window=window,candidate=candidate)
        verification=self._verifier.verify(scope=self._scope,binding=binding,window=window,markets=markets)
        return MarketIdentityResolution(candidate,verification,self._shadow.compare(candidate=candidate,verification=verification))