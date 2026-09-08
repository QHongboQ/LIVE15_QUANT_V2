"""Shared stateless provider-observation acceptance policy."""

from live15_quant_v2.data.data_truth.models import TruthDecision, TruthDecisionCategory
from live15_quant_v2.data.storage.capture import CaptureFact

_POLICY_VERSION = "data-truth/v1"


class ObservationFacts:
    """Accept one approved provider observation without event-state semantics."""

    def decide(self, fact: CaptureFact) -> TruthDecision:
        """Return the provider-evidence acceptance for this subject capture."""
        return TruthDecision(
            subject_capture_id=fact.capture_id,
            category=TruthDecisionCategory.ACCEPTED,
            policy_version=_POLICY_VERSION,
            contributing_capture_ids=(fact.capture_id,),
            reason=None,
            event_identity=None,
        )
