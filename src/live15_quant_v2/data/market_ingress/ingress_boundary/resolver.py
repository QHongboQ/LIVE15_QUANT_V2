"""Ingress Boundary composition point for market identity."""

from dataclasses import dataclass

from live15_quant_v2.data.market_ingress.ingress_boundary.candidate import (
    CandidateTickerPredictor,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.discovery import (
    OfficialMarketDiscovery,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.models import (
    CandidateTicker,
    MarketWindow,
    ShadowResult,
    VerificationResult,
    VerificationStatus,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.ports import MarketScopePort
from live15_quant_v2.data.market_ingress.ingress_boundary.shadow import ShadowValidator
from live15_quant_v2.data.market_ingress.ingress_boundary.verification import (
    OfficialMarketVerifier,
)


@dataclass(frozen=True)
class MarketIdentityResolution:
    candidate: CandidateTicker | None
    verification: VerificationResult
    shadow: ShadowResult


class MarketIdentityResolver:
    def __init__(
        self,
        scope: MarketScopePort,
        predictor: CandidateTickerPredictor,
        discovery: OfficialMarketDiscovery,
        verifier: OfficialMarketVerifier,
        shadow: ShadowValidator,
    ) -> None:
        self._scope = scope
        self._predictor = predictor
        self._discovery = discovery
        self._verifier = verifier
        self._shadow = shadow

    def resolve(self, asset_id: str, window: MarketWindow) -> MarketIdentityResolution:
        binding = self._scope.binding_for_asset(asset_id)
        if binding is None:
            verification = VerificationResult(
                VerificationStatus.INVALID, reason="unknown asset"
            )
            return MarketIdentityResolution(
                None,
                verification,
                self._shadow.compare(candidate=None, verification=verification),
            )
        candidate = self._predictor.predict(binding, window)
        markets = self._discovery.discover(binding=binding, window=window)
        verification = self._verifier.verify(
            scope=self._scope,
            binding=binding,
            window=window,
            markets=markets,
        )
        return MarketIdentityResolution(
            candidate,
            verification,
            self._shadow.compare(candidate=candidate, verification=verification),
        )
