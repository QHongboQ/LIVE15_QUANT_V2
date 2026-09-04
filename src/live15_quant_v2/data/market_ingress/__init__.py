"""Market Ingress parent composition for provider access and LIVE15 semantics."""
from live15_quant_v2.data.market_ingress.ingress_boundary import (
 MarketIdentityResolver,
 MarketScopePort,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.candidate import (
 CandidateTickerPredictor,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.discovery import (
 OfficialMarketDiscovery,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.shadow import ShadowValidator
from live15_quant_v2.data.market_ingress.ingress_boundary.verification import (
 OfficialMarketVerifier,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway import KalshiGateway


def market_identity_resolver(scope: MarketScopePort, gateway: KalshiGateway) -> MarketIdentityResolver:
 return MarketIdentityResolver(scope, CandidateTickerPredictor(), OfficialMarketDiscovery(gateway), OfficialMarketVerifier(), ShadowValidator())
__all__=["KalshiGateway","market_identity_resolver"]