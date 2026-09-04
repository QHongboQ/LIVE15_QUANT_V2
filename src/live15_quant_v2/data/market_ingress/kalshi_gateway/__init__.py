"""Thin Kalshi SDK adapter and Market Identity composition exports."""

from live15_quant_v2.data.market_ingress.kalshi_gateway.gateway import KalshiGateway
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.candidate import (
    CandidateTickerPredictor,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.discovery import (
    OfficialMarketDiscovery,
)
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.verification import (
    OfficialMarketVerifier,
)

__all__ = [
    "CandidateTickerPredictor",
    "KalshiGateway",
    "OfficialMarketDiscovery",
    "OfficialMarketVerifier",
]