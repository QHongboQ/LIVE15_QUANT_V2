"""Contract tests for the synchronous Storage Capture Boundary."""

import json
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pytest
from kalshi.ws.models.cfbenchmarks import (
    CFBenchmarksIndexListMessage,
    CFBenchmarksValueMessage,
)
from kalshi.ws.models.event_fee import EventFeeUpdateMessage
from kalshi.ws.models.market_lifecycle import MarketLifecycleMessage
from kalshi.ws.models.orderbook_delta import (
    OrderbookDeltaMessage,
    OrderbookSnapshotMessage,
)
from kalshi.ws.models.ticker import TickerMessage
from kalshi.ws.models.trade import TradeMessage

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.market_ingress.ingress_boundary import (
    MarketScopeBinding,
    MarketWindow,
    VerifiedMarketIdentity,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.models import (
    DiscoveredMarket,
    OfficialStrike,
)
from live15_quant_v2.data.market_ingress.ingress_boundary.verification import (
    OfficialMarketVerifier,
)
from live15_quant_v2.data.market_ingress.reference_stream import (
    PythValueMessage,
)
from live15_quant_v2.data.market_ingress.reference_stream.pyth_value.models import (
    PythUnderlyingListMessage,
)
from live15_quant_v2.data.storage.capture_boundary import (
    CaptureAuthorityError,
    CaptureBoundary,
    IncompatibleCaptureInputError,
    UnsupportedCaptureMessageError,
)

_TICKER = "KXBTC15M-26SEP042215-99"
_EVENT_TICKER = "KXBTC15M-26SEP042215"
_TS_MS = 1_789_000_123_456
MarketMessage = (
    OrderbookSnapshotMessage
    | OrderbookDeltaMessage
    | TickerMessage
    | TradeMessage
    | MarketLifecycleMessage
    | EventFeeUpdateMessage
)


class _Scope:
    def __init__(self, binding: MarketScopeBinding) -> None:
        self._binding = binding

    def binding_for_asset(self, asset_id: str) -> MarketScopeBinding | None:
        return self._binding if asset_id == self._binding.asset_id else None

    def binding_for_series(self, series_ticker: str) -> MarketScopeBinding | None:
        return self._binding if series_ticker == self._binding.series_ticker else None


def _verified_identity() -> VerifiedMarketIdentity:
    binding = MarketScopeBinding("BTC", "KXBTC15M")
    window = MarketWindow(
        datetime(2026, 9, 4, 22, 15, tzinfo=UTC),
        datetime(2026, 9, 4, 22, 30, tzinfo=UTC),
    )
    strike = OfficialStrike("greater", Decimal(99), None, "BTC above")
    verification = OfficialMarketVerifier().verify(
        scope=_Scope(binding),
        binding=binding,
        window=window,
        markets=[
            DiscoveredMarket(
                binding.series_ticker,
                _TICKER,
                _EVENT_TICKER,
                window.open_time,
                window.close_time,
                strike,
            )
        ],
    )
    assert verification.identity is not None
    return verification.identity


def _boundary() -> CaptureBoundary:
    return CaptureBoundary(clock_ns=lambda: 987_654_321, capture_id_factory=lambda: "cap-1")


def _snapshot(ticker: str = _TICKER) -> OrderbookSnapshotMessage:
    return OrderbookSnapshotMessage.model_validate(
        {
            "type": "orderbook_snapshot",
            "sid": 1,
            "seq": 2,
            "msg": {
                "market_ticker": ticker,
                "market_id": "market-1",
                "yes": [["0.4200", "12.00"]],
                "no": [["0.5800", "8.00"]],
                "unicode_note": "café 金",
            },
        }
    )


def _delta(
    *, ts_ms: int | None = _TS_MS, ts: str | None = "2026-01-02T03:04:05.123456Z"
) -> OrderbookDeltaMessage:
    return OrderbookDeltaMessage.model_validate(
        {
            "type": "orderbook_delta",
            "sid": 3,
            "seq": 4,
            "msg": {
                "market_ticker": _TICKER,
                "market_id": "market-1",
                "price": "0.4200",
                "delta": "3.00",
                "side": "yes",
                "ts": ts,
                "ts_ms": ts_ms,
            },
        }
    )


def _ticker() -> TickerMessage:
    return TickerMessage.model_validate(
        {
            "type": "ticker",
            "sid": 5,
            "seq": None,
            "msg": {
                "market_ticker": _TICKER,
                "market_id": "market-1",
                "yes_bid": "0.4200",
                "yes_ask": "0.4300",
                "no_bid": "0.5700",
                "no_ask": "0.5800",
                "volume": "12.00",
                "open_interest": "8.00",
                "dollar_volume": "120.00",
                "dollar_open_interest": "80.00",
                "yes_bid_size": "2.00",
                "yes_ask_size": "3.00",
                "last_trade_size": "1.00",
                "ts": 1_789_000_123,
                "price": "0.4200",
                "ts_ms": _TS_MS,
            },
        }
    )


def _trade() -> TradeMessage:
    return TradeMessage.model_validate(
        {
            "type": "trade",
            "sid": 6,
            "seq": None,
            "msg": {
                "trade_id": "trade-1",
                "market_ticker": _TICKER,
                "yes_price": "0.4200",
                "no_price": "0.5800",
                "count": "2.00",
                "taker_side": "yes",
                "ts": 1_789_000_123,
                "taker_outcome_side": "yes",
                "taker_book_side": "bid",
                "is_block_trade": False,
                "ts_ms": _TS_MS,
            },
        }
    )


def _lifecycle() -> MarketLifecycleMessage:
    return MarketLifecycleMessage.model_validate(
        {
            "type": "market_lifecycle_v2",
            "sid": 7,
            "seq": None,
            "msg": {"event_type": "created", "market_ticker": _TICKER},
        }
    )


def _fee(event_ticker: str = _EVENT_TICKER) -> EventFeeUpdateMessage:
    return EventFeeUpdateMessage.model_validate(
        {
            "type": "event_fee_update",
            "sid": 8,
            "seq": None,
            "msg": {
                "event_ticker": event_ticker,
                "fee_type_override": None,
                "fee_multiplier_override": None,
            },
        }
    )


def _cf(index_id: str = "BRTI") -> CFBenchmarksValueMessage:
    return CFBenchmarksValueMessage.model_validate(
        {
            "type": "cfbenchmarks_value",
            "sid": 9,
            "seq": None,
            "msg": {
                "index_id": index_id,
                "received_at": 111,
                "data": '{"rate":"100.00000000"}',
                "avg_60s_data": {
                    "value": "100.00000000",
                    "window_size": 1,
                    "window_start_ts_ms": 1,
                    "window_end_ts_exclusive": 2,
                },
            },
        }
    )


def _pyth(ticker: str = "Metal.XAU/USD") -> PythValueMessage:
    return PythValueMessage.model_validate(
        {
            "type": "pyth_value",
            "sid": 10,
            "seq": 11,
            "msg": {
                "underlying_ticker": ticker,
                "value_usd": "2345.6700",
                "source_ts_ms": _TS_MS,
                "received_at": 222,
            },
        }
    )


@pytest.mark.parametrize(
    ("message", "channel", "message_type", "event_subtype", "provider_timestamp"),
    [
        (_snapshot(), "orderbook_delta", "orderbook_snapshot", None, None),
        (_delta(), "orderbook_delta", "orderbook_delta", None, _TS_MS * 1_000_000),
        (_ticker(), "ticker", "ticker", None, _TS_MS * 1_000_000),
        (_trade(), "trade", "trade", None, _TS_MS * 1_000_000),
        (_lifecycle(), "market_lifecycle_v2", "market_lifecycle_v2", "created", None),
        (_fee(), "market_lifecycle_v2", "event_fee_update", None, None),
    ],
)
def test_market_data_messages_have_exact_capture_metadata(
    message: MarketMessage,
    channel: str,
    message_type: str,
    event_subtype: str | None,
    provider_timestamp: int | None,
) -> None:
    fact = _boundary().capture_market(_verified_identity(), message)

    assert fact.capture_id == "cap-1"
    assert fact.asset is AssetId.BTC
    assert fact.provider == "kalshi"
    assert fact.source_id == _TICKER
    assert fact.channel == channel
    assert fact.message_type == message_type
    assert fact.event_subtype == event_subtype
    assert fact.sid == message.sid
    assert fact.seq == message.seq
    assert fact.provider_timestamp == provider_timestamp
    assert fact.received_timestamp == 987_654_321
    assert fact.schema_version == "market-ingress/v1"
    assert isinstance(fact.payload, str)


@pytest.mark.parametrize(
    ("message", "asset", "source_id", "provider_timestamp"),
    [
        (_cf(), AssetId.BTC, "BRTI", None),
        (_pyth(), AssetId.GOLD, "Metal.XAU/USD", _TS_MS * 1_000_000),
    ],
)
def test_reference_data_messages_resolve_only_canonical_scope_bindings(
    message: object, asset: AssetId, source_id: str, provider_timestamp: int | None
) -> None:
    fact = _boundary().capture_reference(message)

    assert fact.asset is asset
    assert fact.source_id == source_id
    assert fact.provider == "kalshi"
    assert fact.provider_timestamp == provider_timestamp
    assert fact.received_timestamp == 987_654_321


def test_market_capture_rejects_copied_identity_and_mismatched_authority() -> None:
    identity = _verified_identity()

    with pytest.raises(CaptureAuthorityError):
        _boundary().capture_market(cast(VerifiedMarketIdentity, _TICKER), _snapshot())
    with pytest.raises(CaptureAuthorityError):
        _boundary().capture_market(replace(identity), _snapshot())
    with pytest.raises(IncompatibleCaptureInputError):
        _boundary().capture_market(identity, _snapshot("KXBTC15M-OTHER"))
    with pytest.raises(IncompatibleCaptureInputError):
        _boundary().capture_market(identity, _fee("KXBTC15M-OTHER-EVENT"))


def test_reference_capture_fails_closed_for_unknown_or_wrong_source_ids() -> None:
    with pytest.raises(CaptureAuthorityError):
        _boundary().capture_reference(_cf("UNKNOWN"))
    with pytest.raises(CaptureAuthorityError):
        _boundary().capture_reference(_pyth("BRTI"))
    with pytest.raises(CaptureAuthorityError):
        _boundary().capture_reference(_cf("Metal.XAG/USD"))


def test_control_unknown_and_subclass_messages_are_rejected() -> None:
    cf_control = CFBenchmarksIndexListMessage.model_validate(
        {
            "type": "cfbenchmarks_value_indexlist",
            "sid": 12,
            "msg": {"index_ids": ["BRTI"]},
        }
    )
    pyth_control = PythUnderlyingListMessage.model_validate(
        {
            "type": "pyth_value_underlying_list",
            "sid": 13,
            "seq": 14,
            "msg": {"underlying_tickers": ["Metal.XAU/USD"]},
        }
    )

    class SnapshotSubclass(OrderbookSnapshotMessage):
        pass

    with pytest.raises(UnsupportedCaptureMessageError):
        _boundary().capture_reference(cf_control)
    with pytest.raises(UnsupportedCaptureMessageError):
        _boundary().capture_reference(pyth_control)
    with pytest.raises(UnsupportedCaptureMessageError):
        _boundary().capture_reference(object())
    with pytest.raises(UnsupportedCaptureMessageError):
        _boundary().capture_market(
            _verified_identity(), SnapshotSubclass.model_validate(_snapshot().model_dump())
        )


def test_discriminator_mismatch_fails_closed_even_for_trade_model() -> None:
    invalid_trade = _trade().model_copy(update={"type": "not-trade"})

    with pytest.raises(IncompatibleCaptureInputError):
        _boundary().capture_market(_verified_identity(), invalid_trade)


def test_delta_timestamp_prefers_milliseconds_and_legacy_datetime_is_integer_exact() -> None:
    identity = _verified_identity()
    assert (
        _boundary().capture_market(identity, _delta()).provider_timestamp
        == _TS_MS * 1_000_000
    )

    legacy = datetime(2026, 1, 2, 3, 4, 5, 123456, tzinfo=UTC)
    fact = _boundary().capture_market(identity, _delta(ts_ms=None, ts=legacy.isoformat()))
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    interval = legacy - epoch
    expected = (
        (interval.days * 86_400 + interval.seconds) * 1_000_000_000
        + interval.microseconds * 1_000
    )
    assert fact.provider_timestamp == expected


def test_received_timestamp_is_never_provider_timestamp_substitute() -> None:
    boundary = CaptureBoundary(clock_ns=lambda: 333, capture_id_factory=lambda: "cap-2")
    fact = boundary.capture_reference(_cf())

    assert fact.provider_timestamp is None
    assert fact.received_timestamp == 333


def test_snapshot_is_frozen_before_sdk_managed_maps_can_mutate() -> None:
    snapshot = _snapshot()
    fact = _boundary().capture_market(_verified_identity(), snapshot)
    frozen_payload = fact.payload
    snapshot.msg.yes[Decimal("0.4200")] = Decimal("999.00")
    snapshot.msg.no.clear()

    assert fact.payload == frozen_payload
    assert '"12.00"' in fact.payload
    assert json.loads(fact.payload)["msg"]["unicode_note"] == "café 金"


def test_received_timestamp_is_sampled_before_serialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order: list[str] = []
    snapshot = _snapshot()
    original: Callable[..., str] = OrderbookSnapshotMessage.model_dump_json

    def clock() -> int:
        order.append("clock")
        return 444

    def serialize(message: OrderbookSnapshotMessage, *args: object, **kwargs: object) -> str:
        order.append("serialize")
        return original(message, *args, **kwargs)

    monkeypatch.setattr(OrderbookSnapshotMessage, "model_dump_json", serialize)
    fact = CaptureBoundary(clock_ns=clock, capture_id_factory=lambda: "cap-3").capture_market(
        _verified_identity(), snapshot
    )

    assert fact.received_timestamp == 444
    assert order == ["clock", "serialize"]
