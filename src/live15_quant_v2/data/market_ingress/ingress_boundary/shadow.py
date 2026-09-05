"""Pure candidate-versus-verified-official comparison."""

from __future__ import annotations

from live15_quant_v2.data.market_ingress.ingress_boundary.models import (
    CandidateTicker,
    ShadowResult,
    ShadowStatus,
    VerificationResult,
    VerificationStatus,
)


class ShadowValidator:
    """Observe disagreement without authorizing, scheduling, or repairing anything."""

    def compare(
        self,
        *,
        candidate: CandidateTicker | None,
        verification: VerificationResult,
    ) -> ShadowResult:
        official_ticker = verification.identity.ticker if verification.identity else None
        if candidate is None:
            return ShadowResult(ShadowStatus.CANDIDATE_MISSING, None, official_ticker)
        if verification.status is VerificationStatus.NO_MATCH:
            return ShadowResult(ShadowStatus.OFFICIAL_MISSING, candidate.ticker, None)
        if not verification.verified:
            return ShadowResult(
                ShadowStatus.VERIFICATION_FAILED, candidate.ticker, official_ticker
            )
        if candidate.ticker == official_ticker:
            return ShadowResult(ShadowStatus.MATCH, candidate.ticker, official_ticker)
        return ShadowResult(ShadowStatus.MISMATCH, candidate.ticker, official_ticker)
