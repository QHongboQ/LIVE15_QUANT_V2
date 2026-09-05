"""Market Ingress parent composition."""

from live15_quant_v2.data.market_ingress.ingress_boundary import (
    MarketIdentityResolver,
    build_market_identity_resolver,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway import KalshiGateway


def market_identity_resolver(gateway: KalshiGateway) -> MarketIdentityResolver:
    """Compose provider discovery with the sole LIVE15 market scope."""
    return build_market_identity_resolver(gateway)


__all__ = ["KalshiGateway", "market_identity_resolver"]
