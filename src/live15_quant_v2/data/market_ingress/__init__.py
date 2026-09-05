"""Market Ingress parent composition."""

from live15_quant_v2.data.market_ingress.ingress_boundary import (
    MarketIdentityResolver,
    MarketScopePort,
    build_market_identity_resolver,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway import KalshiGateway


def market_identity_resolver(
    scope: MarketScopePort, gateway: KalshiGateway
) -> MarketIdentityResolver:
    """Compose provider discovery with LIVE15 market-identity semantics."""
    return build_market_identity_resolver(scope, gateway)


__all__ = ["KalshiGateway", "market_identity_resolver"]