import json
from dataclasses import FrozenInstanceError, replace
from typing import Literal

import pytest
from kalshi.ws.models.trade import TradeMessage

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.data_truth import TruthDecisionCategory
from live15_quant_v2.data.storage.capture import CaptureFact


def _trade_payload(
    *,
    trade_id: str = "trade-1",
    market_ticker: str = "KXBTC-TEST",
    ts: int = 1_789_000_123,
    ts_ms: int = 1_789_000_123_456,
    yes_price: str = "0.4200",
) -> str:
    message = TradeMessage.model_validate(
        {
            "type": "trade",
            "sid": 6,
            "seq": None,
            "msg": {
                "trade_id": trade_id,
                "market_ticker": market_ticker,
                "yes_price": yes_price,
                "no_price": "0.5800",
                "count": "2.00",
                "taker_side": "yes",
                "ts": ts,
                "taker_outcome_side": "yes",
                "taker_book_side": "bid",
                "is_block_trade": False,
                "ts_ms": ts_ms,
            },
        }
    )
    return message.model_dump_json()


def _trade_fact() -> CaptureFact:
    return CaptureFact(
        capture_id="capture-trade-1",
        asset=AssetId.BTC,
        provider="kalshi",
        source_id="KXBTC-TEST",
        channel="trade",
        message_type="trade",
        event_subtype=None,
        sid=6,
        seq=None,
        provider_timestamp=1_789_000_123_456_000_000,
        received_timestamp=1_789_000_123_457_000_000,
        schema_version="market-ingress/v1",
        payload=_trade_payload(),
    )


class FakeTruthDecisionHistory:
    """Test-only authority double implementing the exact Slice 1 history seam."""

    def __init__(
        self,
        *,
        subjects=None,
        anchors=None,
        append_outcome: Literal[
            "success", "missing", "different", "rejected", "in_doubt_committed", "in_doubt_different", "in_doubt"
        ] = "success",
    ) -> None:
        self.subjects = dict(subjects or {})
        self.anchors = dict(anchors or {})
        self.append_outcome = append_outcome
        self.append_calls = 0
        self.event_lookups = []

    def find_subject_decision(self, policy_version: str, capture_id: str):
        return self.subjects.get((policy_version, capture_id))

    def find_accepted_event(self, event_identity):
        self.event_lookups.append(event_identity)
        return self.anchors.get(event_identity)

    def append(self, decision) -> None:
        from live15_quant_v2.data.data_truth import (
            TruthDecisionAppendInDoubtError,
            TruthDecisionAppendRejectedError,
            TruthDecisionCategory,
        )

        self.append_calls += 1
        key = (decision.policy_version, decision.subject_capture_id)
        if self.append_outcome == "rejected":
            raise TruthDecisionAppendRejectedError("definite test rejection")
        if self.append_outcome == "different":
            self.subjects[key] = replace(decision, category=TruthDecisionCategory.CONFLICT)
            return
        if self.append_outcome == "in_doubt_committed":
            self.subjects[key] = decision
            raise TruthDecisionAppendInDoubtError("test ambiguity after commit")
        if self.append_outcome == "in_doubt_different":
            self.subjects[key] = replace(decision, category=TruthDecisionCategory.CONFLICT)
            raise TruthDecisionAppendInDoubtError("test ambiguity with conflict")
        if self.append_outcome == "in_doubt":
            raise TruthDecisionAppendInDoubtError("test ambiguity without commit")
        if self.append_outcome == "success":
            self.subjects[key] = decision


def _accepted_anchor(fact: CaptureFact):
    from live15_quant_v2.data.data_truth import (
        EventAnchor,
        EventIdentity,
        TruthDecision,
        TruthDecisionCategory,
    )

    identity = EventIdentity("kalshi", fact.source_id, "trade", "trade-1")
    return EventAnchor(
        event_identity=identity,
        accepted_decision=TruthDecision(
            subject_capture_id=fact.capture_id,
            category=TruthDecisionCategory.ACCEPTED,
            policy_version="data-truth/v1",
            contributing_capture_ids=(fact.capture_id,),
            reason=None,
            event_identity=identity,
        ),
        accepted_fact=fact,
    )


def test_first_valid_trade_is_accepted_after_same_authority_verification() -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionCategory

    decision = DataTruth(FakeTruthDecisionHistory()).decide(_trade_fact())

    assert decision.category is TruthDecisionCategory.ACCEPTED
    assert decision.subject_capture_id == "capture-trade-1"
    assert decision.event_identity is not None
    assert decision.event_identity.trade_id == "trade-1"
    assert decision.contributing_capture_ids == ("capture-trade-1",)


def test_equal_distinct_trade_evidence_is_a_semantic_duplicate() -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionCategory

    accepted = _trade_fact()
    subject = replace(accepted, capture_id="capture-trade-2")
    history = FakeTruthDecisionHistory(anchors={_accepted_anchor(accepted).event_identity: _accepted_anchor(accepted)})

    decision = DataTruth(history).decide(subject)

    assert decision.category is TruthDecisionCategory.DUPLICATE
    assert decision.contributing_capture_ids == ("capture-trade-1", "capture-trade-2")


def test_changed_provider_semantic_trade_field_is_a_conflict() -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionCategory

    accepted = _trade_fact()
    subject = replace(
        accepted,
        capture_id="capture-trade-2",
        payload=_trade_payload(yes_price="0.4300"),
    )
    anchor = _accepted_anchor(accepted)

    decision = DataTruth(FakeTruthDecisionHistory(anchors={anchor.event_identity: anchor})).decide(subject)

    assert decision.category is TruthDecisionCategory.CONFLICT


def test_internally_inconsistent_event_anchor_fails_closed() -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionInvariantError

    accepted = _trade_fact()
    subject = replace(accepted, capture_id="capture-trade-2")
    anchor = _accepted_anchor(accepted)
    invalid_anchor = replace(anchor, accepted_decision=replace(anchor.accepted_decision, event_identity=None))

    with pytest.raises(TruthDecisionInvariantError):
        DataTruth(
            FakeTruthDecisionHistory(anchors={anchor.event_identity: invalid_anchor})
        ).decide(subject)


@pytest.mark.parametrize(
    "corrupt_anchor",
    [
        lambda anchor: replace(
            anchor,
            event_identity=replace(anchor.event_identity, trade_id="other-trade"),
        ),
        lambda anchor: replace(
            anchor,
            accepted_decision=replace(
                anchor.accepted_decision,
                category=TruthDecisionCategory.CONFLICT,
            ),
        ),
        lambda anchor: replace(
            anchor,
            accepted_decision=replace(anchor.accepted_decision, event_identity=None),
        ),
        lambda anchor: replace(
            anchor,
            accepted_fact=replace(
                anchor.accepted_fact,
                source_id="OTHER-MARKET",
                payload=_trade_payload(market_ticker="OTHER-MARKET"),
            ),
        ),
        lambda anchor: replace(anchor, accepted_fact=replace(anchor.accepted_fact, payload="not JSON")),
        lambda anchor: replace(
            anchor,
            accepted_decision=replace(anchor.accepted_decision, subject_capture_id="other-capture"),
        ),
        lambda anchor: replace(
            anchor,
            accepted_decision=replace(
                anchor.accepted_decision,
                contributing_capture_ids=("other-capture",),
            ),
        ),
    ],
    ids=[
        "anchor-event-identity",
        "decision-category",
        "decision-event-identity",
        "accepted-fact-identity",
        "accepted-fact-invalid-evidence",
        "decision-subject-capture-id",
        "decision-contributing-capture-ids",
    ],
)
def test_every_representable_corrupt_event_anchor_fails_before_append(corrupt_anchor) -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionInvariantError

    accepted = _trade_fact()
    subject = replace(accepted, capture_id="capture-trade-2")
    anchor = _accepted_anchor(accepted)
    history = FakeTruthDecisionHistory(anchors={anchor.event_identity: corrupt_anchor(anchor)})

    with pytest.raises(TruthDecisionInvariantError):
        DataTruth(history).decide(subject)

    assert history.append_calls == 0


def test_wrong_policy_event_anchor_fails_closed_before_append() -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionInvariantError

    accepted = _trade_fact()
    subject = replace(accepted, capture_id="capture-trade-2")
    anchor = _accepted_anchor(accepted)
    wrong_policy_anchor = replace(
        anchor,
        accepted_decision=replace(anchor.accepted_decision, policy_version="data-truth/v0"),
    )
    history = FakeTruthDecisionHistory(anchors={anchor.event_identity: wrong_policy_anchor})

    with pytest.raises(TruthDecisionInvariantError):
        DataTruth(history).decide(subject)

    assert history.append_calls == 0


@pytest.mark.parametrize(
    ("fact", "reason"),
    [
        (replace(_trade_fact(), payload="not JSON"), "INVALID_TRADE_EVIDENCE"),
        (replace(_trade_fact(), schema_version="market-ingress/v2"), "UNSUPPORTED_TRADE_SCHEMA"),
        (replace(_trade_fact(), payload=_trade_payload(market_ticker="OTHER")), "TRADE_IDENTITY_MISMATCH"),
        (replace(_trade_fact(), provider="other"), "INVALID_TRADE_EVIDENCE"),
        (replace(_trade_fact(), payload=_trade_payload(trade_id="")), "INVALID_TRADE_EVIDENCE"),
    ],
)
def test_invalid_trade_evidence_is_bounded_not_accepted(fact, reason: str) -> None:
    from live15_quant_v2.data.data_truth import (
        DataTruth,
        TradeNotAcceptedReason,
        TruthDecisionCategory,
    )

    history = FakeTruthDecisionHistory()
    decision = DataTruth(history).decide(fact)

    assert decision.category is TruthDecisionCategory.NOT_ACCEPTED
    assert decision.reason is TradeNotAcceptedReason[reason]
    assert decision.event_identity is None
    assert history.event_lookups == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sid", 99),
        ("seq", 100),
        ("received_timestamp", 1),
        ("provider_timestamp", 2),
    ],
)
def test_transport_only_trade_fields_do_not_create_semantic_conflicts(field, value) -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionCategory

    accepted = _trade_fact()
    subject = replace(accepted, capture_id=f"capture-{field}", **{field: value})
    anchor = _accepted_anchor(accepted)

    decision = DataTruth(FakeTruthDecisionHistory(anchors={anchor.event_identity: anchor})).decide(subject)

    assert decision.category is TruthDecisionCategory.DUPLICATE


def test_equivalent_trade_json_with_different_formatting_is_a_duplicate() -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionCategory

    accepted = _trade_fact()
    decoded = json.loads(accepted.payload)
    differently_formatted = json.dumps(
        {"msg": decoded["msg"], "seq": None, "sid": 6, "type": "trade"},
        indent=2,
    )
    subject = replace(accepted, capture_id="capture-trade-2", payload=differently_formatted)
    anchor = _accepted_anchor(accepted)

    assert (
        DataTruth(FakeTruthDecisionHistory(anchors={anchor.event_identity: anchor})).decide(
            subject
        ).category
        is TruthDecisionCategory.DUPLICATE
    )


@pytest.mark.parametrize("payload", [_trade_payload(ts=1), _trade_payload(ts_ms=1)])
def test_provider_semantic_trade_timestamps_remain_conflict_evidence(payload: str) -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionCategory

    accepted = _trade_fact()
    subject = replace(accepted, capture_id="capture-trade-2", payload=payload)
    anchor = _accepted_anchor(accepted)

    assert (
        DataTruth(FakeTruthDecisionHistory(anchors={anchor.event_identity: anchor})).decide(
            subject
        ).category
        is TruthDecisionCategory.CONFLICT
    )


@pytest.mark.parametrize(
    "message_type",
    [
        "orderbook_snapshot",
        "orderbook_delta",
        "ticker",
        "market_lifecycle_v2",
        "event_fee_update",
        "cfbenchmarks_value",
        "pyth_value",
    ],
)
def test_each_approved_observation_is_independently_accepted(message_type: str) -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionCategory

    fact = replace(_trade_fact(), capture_id=f"capture-{message_type}", message_type=message_type)
    history = FakeTruthDecisionHistory()
    decision = DataTruth(history).decide(fact)

    assert decision.category is TruthDecisionCategory.ACCEPTED
    assert decision.event_identity is None
    assert history.event_lookups == []


def test_equal_observations_remain_independent_subject_decisions() -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionCategory

    first = replace(_trade_fact(), capture_id="observation-1", message_type="ticker")
    second = replace(first, capture_id="observation-2")
    history = FakeTruthDecisionHistory()
    truth = DataTruth(history)

    assert truth.decide(first).category is TruthDecisionCategory.ACCEPTED
    assert truth.decide(second).category is TruthDecisionCategory.ACCEPTED
    assert history.append_calls == 2


def test_unsupported_message_family_fails_closed() -> None:
    from live15_quant_v2.data.data_truth import (
        DataTruth,
        UnsupportedDataTruthInputError,
    )

    with pytest.raises(UnsupportedDataTruthInputError):
        DataTruth(FakeTruthDecisionHistory()).decide(
            replace(_trade_fact(), message_type="unknown")
        )


def test_existing_subject_decision_returns_without_new_append() -> None:
    from live15_quant_v2.data.data_truth import DataTruth

    existing_history = FakeTruthDecisionHistory()
    existing = DataTruth(existing_history).decide(_trade_fact())
    history = FakeTruthDecisionHistory(
        subjects={(existing.policy_version, existing.subject_capture_id): existing}
    )

    assert DataTruth(history).decide(_trade_fact()) == existing
    assert history.append_calls == 0


@pytest.mark.parametrize("append_outcome", ["missing", "different"])
def test_successful_append_without_exact_same_authority_verification_fails_closed(
    append_outcome: str,
) -> None:
    from live15_quant_v2.data.data_truth import (
        DataTruth,
        TruthDecisionVerificationError,
    )

    with pytest.raises(TruthDecisionVerificationError):
        DataTruth(FakeTruthDecisionHistory(append_outcome=append_outcome)).decide(
            _trade_fact()
        )


def test_definite_append_failure_is_raised_without_retry() -> None:
    from live15_quant_v2.data.data_truth import (
        DataTruth,
        TruthDecisionAppendRejectedError,
    )

    history = FakeTruthDecisionHistory(append_outcome="rejected")
    with pytest.raises(TruthDecisionAppendRejectedError):
        DataTruth(history).decide(_trade_fact())

    assert history.append_calls == 1


def test_in_doubt_after_commit_reconciles_exact_subject_without_reappend() -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionCategory

    history = FakeTruthDecisionHistory(append_outcome="in_doubt_committed")
    decision = DataTruth(history).decide(_trade_fact())

    assert decision.category is TruthDecisionCategory.ACCEPTED
    assert history.append_calls == 1


def test_in_doubt_without_proven_subject_remains_in_doubt_without_reappend() -> None:
    from live15_quant_v2.data.data_truth import (
        DataTruth,
        TruthDecisionAppendInDoubtError,
    )

    history = FakeTruthDecisionHistory(append_outcome="in_doubt")
    with pytest.raises(TruthDecisionAppendInDoubtError):
        DataTruth(history).decide(_trade_fact())

    assert history.append_calls == 1


def test_in_doubt_with_conflicting_subject_fails_closed_without_reappend() -> None:
    from live15_quant_v2.data.data_truth import (
        DataTruth,
        TruthDecisionVerificationError,
    )

    history = FakeTruthDecisionHistory(append_outcome="in_doubt_different")
    with pytest.raises(TruthDecisionVerificationError):
        DataTruth(history).decide(_trade_fact())

    assert history.append_calls == 1


def test_missing_trade_identity_has_no_capture_or_timestamp_or_payload_fallback() -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionCategory

    fact = replace(
        _trade_fact(),
        capture_id="different-capture",
        sid=99,
        seq=100,
        provider_timestamp=1,
        received_timestamp=2,
        payload=_trade_payload(trade_id=""),
    )

    decision = DataTruth(FakeTruthDecisionHistory()).decide(fact)

    assert decision.category is TruthDecisionCategory.NOT_ACCEPTED
    assert decision.event_identity is None


def test_equally_invalid_trade_payloads_are_not_a_semantic_duplicate() -> None:
    from live15_quant_v2.data.data_truth import DataTruth, TruthDecisionCategory

    first = replace(_trade_fact(), capture_id="invalid-trade-1", payload=_trade_payload(trade_id=""))
    second = replace(first, capture_id="invalid-trade-2")
    history = FakeTruthDecisionHistory()
    truth = DataTruth(history)

    assert truth.decide(first).category is TruthDecisionCategory.NOT_ACCEPTED
    assert truth.decide(second).category is TruthDecisionCategory.NOT_ACCEPTED
    assert history.event_lookups == []


def test_truth_decisions_are_immutable_and_deterministically_equal() -> None:
    from live15_quant_v2.data.data_truth import DataTruth

    first = DataTruth(FakeTruthDecisionHistory()).decide(_trade_fact())
    second = DataTruth(FakeTruthDecisionHistory()).decide(_trade_fact())

    assert first == second
    with pytest.raises(AttributeError):
        first.category = first.category


def test_public_authority_models_are_deeply_immutable() -> None:
    from live15_quant_v2.data.data_truth import (
        EventAnchor,
        EventIdentity,
        TruthDecision,
        TruthDecisionCategory,
    )

    fact = _trade_fact()
    identity = EventIdentity("kalshi", fact.source_id, "trade", "trade-1")
    caller_references = [fact.capture_id]
    decision = TruthDecision(
        subject_capture_id=fact.capture_id,
        category=TruthDecisionCategory.ACCEPTED,
        policy_version="data-truth/v1",
        contributing_capture_ids=caller_references,
        reason=None,
        event_identity=identity,
    )
    anchor = EventAnchor(identity, decision, fact)

    caller_references.append("later-capture")

    assert type(decision.contributing_capture_ids) is tuple
    assert decision.contributing_capture_ids == (fact.capture_id,)
    with pytest.raises(FrozenInstanceError):
        decision.contributing_capture_ids = ()
    with pytest.raises(FrozenInstanceError):
        identity.trade_id = "other-trade"
    with pytest.raises(FrozenInstanceError):
        anchor.accepted_fact = fact


def test_truth_decision_accepts_tuple_references() -> None:
    from live15_quant_v2.data.data_truth import (
        EventIdentity,
        TruthDecision,
        TruthDecisionCategory,
    )

    fact = _trade_fact()
    decision = TruthDecision(
        subject_capture_id=fact.capture_id,
        category=TruthDecisionCategory.ACCEPTED,
        policy_version="data-truth/v1",
        contributing_capture_ids=(fact.capture_id,),
        reason=None,
        event_identity=EventIdentity("kalshi", fact.source_id, "trade", "trade-1"),
    )

    assert decision.contributing_capture_ids == (fact.capture_id,)


def test_truth_decision_validates_and_stores_one_stateful_list_snapshot() -> None:
    from live15_quant_v2.data.data_truth import EventIdentity, TruthDecision

    class ChangingReferenceList(list[str]):
        def __init__(self, valid_capture_id: str) -> None:
            super().__init__([valid_capture_id])
            self.iteration_count = 0

        def __iter__(self):
            self.iteration_count += 1
            if self.iteration_count == 1:
                return iter([self[0]])
            return iter([1])

    fact = _trade_fact()
    references = ChangingReferenceList(fact.capture_id)
    decision = TruthDecision(
        subject_capture_id=fact.capture_id,
        category=TruthDecisionCategory.ACCEPTED,
        policy_version="data-truth/v1",
        contributing_capture_ids=references,
        reason=None,
        event_identity=EventIdentity("kalshi", fact.source_id, "trade", "trade-1"),
    )

    assert references.iteration_count == 1
    assert decision.contributing_capture_ids == (fact.capture_id,)
    assert all(type(capture_id) is str for capture_id in decision.contributing_capture_ids)


@pytest.mark.parametrize(
    "references",
    [
        "capture-trade-1",
        b"capture-trade-1",
        bytearray(b"capture-trade-1"),
        {"capture-trade-1"},
        frozenset({"capture-trade-1"}),
        {"capture-trade-1": True},
        (capture_id for capture_id in ("capture-trade-1",)),
        1,
        object(),
        ["capture-trade-1", 2],
        ("capture-trade-1", object()),
    ],
    ids=[
        "str",
        "bytes",
        "bytearray",
        "set",
        "frozenset",
        "dict",
        "generator",
        "integer",
        "object",
        "list-non-string-element",
        "tuple-non-string-element",
    ],
)
def test_truth_decision_rejects_unsafe_reference_input(references: object) -> None:
    from live15_quant_v2.data.data_truth import (
        EventIdentity,
        TruthDecision,
        TruthDecisionCategory,
    )

    fact = _trade_fact()
    with pytest.raises(TypeError):
        TruthDecision(
            subject_capture_id=fact.capture_id,
            category=TruthDecisionCategory.ACCEPTED,
            policy_version="data-truth/v1",
            contributing_capture_ids=references,
            reason=None,
            event_identity=EventIdentity("kalshi", fact.source_id, "trade", "trade-1"),
        )
