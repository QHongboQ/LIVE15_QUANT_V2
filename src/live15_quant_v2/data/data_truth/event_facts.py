"""Trade-only Event Facts semantic adjudication."""

from kalshi.ws.models.trade import TradeMessage
from pydantic import ValidationError

from live15_quant_v2.data.data_truth.history import TruthDecisionInvariantError
from live15_quant_v2.data.data_truth.models import (
    EventAnchor,
    EventIdentity,
    TradeNotAcceptedReason,
    TruthDecision,
    TruthDecisionCategory,
)
from live15_quant_v2.data.storage.capture import CaptureFact

_POLICY_VERSION = "data-truth/v1"
_TRADE_SCHEMA_VERSION = "market-ingress/v1"
_TRADE_PROVIDER = "kalshi"
_TRADE_MESSAGE_TYPE = "trade"
type _TradeProjection = dict[str, object]


class EventFacts:
    """Classify one valid Trade against an optional accepted EventAnchor."""

    def event_identity_or_not_accepted(
        self, fact: CaptureFact
    ) -> EventIdentity | TruthDecision:
        """Return only an approved identity or a bounded rejected decision."""
        evidence = self._trade_evidence_or_not_accepted(fact)
        if isinstance(evidence, TruthDecision):
            return evidence
        return evidence[0]

    def decide(self, fact: CaptureFact, anchor: EventAnchor | None) -> TruthDecision:
        """Return the deterministic semantic decision for one Trade evidence fact."""
        evidence = self._trade_evidence_or_not_accepted(fact)
        if isinstance(evidence, TruthDecision):
            return evidence
        event_identity, projection = evidence
        if anchor is None:
            return self._decision(
                fact,
                TruthDecisionCategory.ACCEPTED,
                event_identity=event_identity,
            )

        accepted_projection = self._validated_anchor_projection(anchor, event_identity)
        category = (
            TruthDecisionCategory.DUPLICATE
            if accepted_projection == projection
            else TruthDecisionCategory.CONFLICT
        )
        return self._decision(
            fact,
            category,
            event_identity=event_identity,
            contributing_capture_ids=(anchor.accepted_fact.capture_id, fact.capture_id),
        )

    def _validated_anchor_projection(
        self, anchor: EventAnchor, event_identity: EventIdentity
    ) -> _TradeProjection:
        if anchor.event_identity != event_identity:
            raise TruthDecisionInvariantError("accepted event anchor identity differs")
        if anchor.accepted_decision.policy_version != _POLICY_VERSION:
            raise TruthDecisionInvariantError("event anchor decision policy differs")
        if (
            anchor.accepted_decision.category is not TruthDecisionCategory.ACCEPTED
            or anchor.accepted_decision.event_identity != event_identity
        ):
            raise TruthDecisionInvariantError("event anchor does not contain accepted authority")
        if anchor.accepted_decision.subject_capture_id != anchor.accepted_fact.capture_id:
            raise TruthDecisionInvariantError("event anchor decision subject differs from accepted evidence")
        if anchor.accepted_fact.capture_id not in anchor.accepted_decision.contributing_capture_ids:
            raise TruthDecisionInvariantError("event anchor decision does not reference accepted evidence")
        accepted_evidence = self._trade_evidence_or_not_accepted(anchor.accepted_fact)
        if isinstance(accepted_evidence, TruthDecision):
            raise TruthDecisionInvariantError("event anchor contains invalid accepted evidence")
        accepted_identity, accepted_projection = accepted_evidence
        if accepted_identity != event_identity:
            raise TruthDecisionInvariantError("accepted evidence identity differs")
        return accepted_projection

    def _trade_evidence_or_not_accepted(
        self, fact: CaptureFact
    ) -> tuple[EventIdentity, _TradeProjection] | TruthDecision:
        if fact.schema_version != _TRADE_SCHEMA_VERSION:
            return self._not_accepted(fact, TradeNotAcceptedReason.UNSUPPORTED_TRADE_SCHEMA)
        if fact.provider != _TRADE_PROVIDER or fact.message_type != _TRADE_MESSAGE_TYPE:
            return self._not_accepted(fact, TradeNotAcceptedReason.INVALID_TRADE_EVIDENCE)
        try:
            message = TradeMessage.model_validate_json(fact.payload)
        except (TypeError, ValidationError, ValueError):
            return self._not_accepted(fact, TradeNotAcceptedReason.INVALID_TRADE_EVIDENCE)
        if type(message) is not TradeMessage or message.type != _TRADE_MESSAGE_TYPE:
            return self._not_accepted(fact, TradeNotAcceptedReason.INVALID_TRADE_EVIDENCE)
        trade_id = message.msg.trade_id
        if not isinstance(trade_id, str) or not trade_id:
            return self._not_accepted(fact, TradeNotAcceptedReason.INVALID_TRADE_EVIDENCE)
        if message.msg.market_ticker != fact.source_id:
            return self._not_accepted(fact, TradeNotAcceptedReason.TRADE_IDENTITY_MISMATCH)
        projection = message.msg.model_dump(mode="json")
        projection.pop("trade_id")
        projection.pop("market_ticker")
        return (
            EventIdentity(
                provider=fact.provider,
                source_id=fact.source_id,
                message_type=fact.message_type,
                trade_id=trade_id,
            ),
            projection,
        )

    @staticmethod
    def _decision(
        fact: CaptureFact,
        category: TruthDecisionCategory,
        *,
        event_identity: EventIdentity,
        contributing_capture_ids: tuple[str, ...] | None = None,
    ) -> TruthDecision:
        return TruthDecision(
            subject_capture_id=fact.capture_id,
            category=category,
            policy_version=_POLICY_VERSION,
            contributing_capture_ids=contributing_capture_ids or (fact.capture_id,),
            reason=None,
            event_identity=event_identity,
        )

    @staticmethod
    def _not_accepted(
        fact: CaptureFact, reason: TradeNotAcceptedReason
    ) -> TruthDecision:
        return TruthDecision(
            subject_capture_id=fact.capture_id,
            category=TruthDecisionCategory.NOT_ACCEPTED,
            policy_version=_POLICY_VERSION,
            contributing_capture_ids=(fact.capture_id,),
            reason=reason,
            event_identity=None,
        )
