"""Public assembly for LIVE15 Ingress Boundary semantics."""
from live15_quant_v2.data.market_ingress.ingress_boundary.candidate import (
 CandidateTickerPredictor,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.discovery import (
 OfficialMarketDiscovery,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.ports import (
 MarketDiscoveryPort,
 MarketScopePort,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.resolver import (
 MarketIdentityResolver,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.shadow import ShadowValidator
from live15_quant_v2.data.market_ingress.ingress_boundary.verification import (
 OfficialMarketVerifier,
)


def build_market_identity_resolver(scope:MarketScopePort, discovery_port:MarketDiscoveryPort)->MarketIdentityResolver:
 return MarketIdentityResolver(scope,CandidateTickerPredictor(),OfficialMarketDiscovery(discovery_port),OfficialMarketVerifier(),ShadowValidator())