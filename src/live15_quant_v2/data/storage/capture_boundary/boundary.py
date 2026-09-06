"""Synchronous immutable-fact issuance at the Storage capture boundary."""

from collections.abc import Callable
from datetime import UTC, datetime
from time import time_ns
from typing import cast
from uuid import uuid4

from kalshi.ws.models.cfbenchmarks import CFBenchmarksValueMessage
from kalshi.ws.models.event_fee import EventFeeUpdateMessage
from kalshi.ws.models.market_lifecycle import MarketLifecycleMessage
from kalshi.ws.models.orderbook_delta import (
    OrderbookDeltaMessage,
    OrderbookSnapshotMessage,
)
from kalshi.ws.models.ticker import TickerMessage
from kalshi.ws.models.trade import TradeMessage
from pydantic import BaseModel

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.market_ingress.ingress_boundary import (
    VerifiedMarketIdentity,
)
from live15_quant_v2.data.market_ingress.reference_stream import (
    Live15ReferenceScopeConfig,
    PythValueMessage,
    ReferenceSource,
)
from live15_quant_v2.data.storage.capture import CaptureFact
from live15_quant_v2.data.storage.capture_boundary.errors import (
    CaptureAuthorityError,
    IncompatibleCaptureInputError,
    UnsupportedCaptureMessageError,
)

_NANOSECONDS_PER_MILLISECOND = 1_000_000
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_SCHEMA_VERSION = "market-ingress/v1"


class CaptureBoundary:
    """Freeze approved typed ingress messages into immutable CaptureFacts."""

    def __init__(
        self,
        *,
        clock_ns: Callable[[], int] = time_ns,
        capture_id_factory: Callable[[], str] = lambda: str(uuid4()),
    ) -> None:
        self._clock_ns = clock_ns
        self._capture_id_factory = capture_id_factory
        self._reference_scope = Live15ReferenceScopeConfig()

    def capture_market(
        self, identity: VerifiedMarketIdentity, message: object
    ) -> CaptureFact:
        """Capture one verified prediction-market data-plane message."""
        received_timestamp = self._received_timestamp()
        verified_identity = self._require_verified_identity(identity)

        if type(message) is OrderbookSnapshotMessage:
            snapshot = cast(OrderbookSnapshotMessage, message)
            self._require_discriminator(snapshot, "orderbook_snapshot")
            self._require_market_ticker(snapshot.msg.market_ticker, verified_identity)
            return self._issue(
                asset=self._identity_asset(verified_identity),
                source_id=verified_identity.ticker,
                channel="orderbook_delta",
                message_type="orderbook_snapshot",
                event_subtype=None,
                sid=snapshot.sid,
                seq=snapshot.seq,
                provider_timestamp=None,
                received_timestamp=received_timestamp,
                message=snapshot,
            )
        if type(message) is OrderbookDeltaMessage:
            delta = cast(OrderbookDeltaMessage, message)
            self._require_discriminator(delta, "orderbook_delta")
            self._require_market_ticker(delta.msg.market_ticker, verified_identity)
            return self._issue(
                asset=self._identity_asset(verified_identity),
                source_id=verified_identity.ticker,
                channel="orderbook_delta",
                message_type="orderbook_delta",
                event_subtype=None,
                sid=delta.sid,
                seq=delta.seq,
                provider_timestamp=self._delta_timestamp(delta),
                received_timestamp=received_timestamp,
                message=delta,
            )
        if type(message) is TickerMessage:
            ticker = cast(TickerMessage, message)
            self._require_discriminator(ticker, "ticker")
            self._require_market_ticker(ticker.msg.market_ticker, verified_identity)
            return self._issue(
                asset=self._identity_asset(verified_identity),
                source_id=verified_identity.ticker,
                channel="ticker",
                message_type="ticker",
                event_subtype=None,
                sid=ticker.sid,
                seq=ticker.seq,
                provider_timestamp=self._milliseconds_to_ns(ticker.msg.ts_ms),
                received_timestamp=received_timestamp,
                message=ticker,
            )
        if type(message) is TradeMessage:
            trade = cast(TradeMessage, message)
            self._require_discriminator(trade, "trade")
            self._require_market_ticker(trade.msg.market_ticker, verified_identity)
            return self._issue(
                asset=self._identity_asset(verified_identity),
                source_id=verified_identity.ticker,
                channel="trade",
                message_type="trade",
                event_subtype=None,
                sid=trade.sid,
                seq=trade.seq,
                provider_timestamp=self._milliseconds_to_ns(trade.msg.ts_ms),
                received_timestamp=received_timestamp,
                message=trade,
            )
        if type(message) is MarketLifecycleMessage:
            lifecycle = cast(MarketLifecycleMessage, message)
            self._require_discriminator(lifecycle, "market_lifecycle_v2")
            self._require_market_ticker(lifecycle.msg.market_ticker, verified_identity)
            return self._issue(
                asset=self._identity_asset(verified_identity),
                source_id=verified_identity.ticker,
                channel="market_lifecycle_v2",
                message_type="market_lifecycle_v2",
                event_subtype=lifecycle.msg.event_type,
                sid=lifecycle.sid,
                seq=lifecycle.seq,
                provider_timestamp=None,
                received_timestamp=received_timestamp,
                message=lifecycle,
            )
        if type(message) is EventFeeUpdateMessage:
            fee_update = cast(EventFeeUpdateMessage, message)
            self._require_discriminator(fee_update, "event_fee_update")
            if fee_update.msg.event_ticker != verified_identity.event_ticker:
                raise IncompatibleCaptureInputError(
                    "event fee update event_ticker does not match verified identity"
                )
            return self._issue(
                asset=self._identity_asset(verified_identity),
                source_id=verified_identity.ticker,
                channel="market_lifecycle_v2",
                message_type="event_fee_update",
                event_subtype=None,
                sid=fee_update.sid,
                seq=fee_update.seq,
                provider_timestamp=None,
                received_timestamp=received_timestamp,
                message=fee_update,
            )
        raise UnsupportedCaptureMessageError("unsupported prediction-market message")

    def capture_reference(self, message: object) -> CaptureFact:
        """Capture one approved reference data-plane message."""
        received_timestamp = self._received_timestamp()

        if type(message) is CFBenchmarksValueMessage:
            cf_value = cast(CFBenchmarksValueMessage, message)
            self._require_discriminator(cf_value, "cfbenchmarks_value")
            binding = self._reference_binding(
                ReferenceSource.CF_BENCHMARKS, cf_value.msg.index_id
            )
            return self._issue(
                asset=self._binding_asset(binding.asset_id),
                source_id=binding.provider_id,
                channel="cfbenchmarks_value",
                message_type="cfbenchmarks_value",
                event_subtype=None,
                sid=cf_value.sid,
                seq=cf_value.seq,
                provider_timestamp=None,
                received_timestamp=received_timestamp,
                message=cf_value,
            )
        if type(message) is PythValueMessage:
            pyth_value = cast(PythValueMessage, message)
            self._require_discriminator(pyth_value, "pyth_value")
            binding = self._reference_binding(
                ReferenceSource.PYTH_VALUE, pyth_value.msg.underlying_ticker
            )
            return self._issue(
                asset=self._binding_asset(binding.asset_id),
                source_id=binding.provider_id,
                channel="pyth_value",
                message_type="pyth_value",
                event_subtype=None,
                sid=pyth_value.sid,
                seq=pyth_value.seq,
                provider_timestamp=self._milliseconds_to_ns(pyth_value.msg.source_ts_ms),
                received_timestamp=received_timestamp,
                message=pyth_value,
            )
        raise UnsupportedCaptureMessageError("unsupported or control reference message")

    def _issue(
        self,
        *,
        asset: AssetId,
        source_id: str,
        channel: str,
        message_type: str,
        event_subtype: str | None,
        sid: int,
        seq: int | None,
        provider_timestamp: int | None,
        received_timestamp: int,
        message: BaseModel,
    ) -> CaptureFact:
        capture_id = self._capture_id_factory()
        if not isinstance(capture_id, str):
            raise IncompatibleCaptureInputError("capture ID factory must return str")
        return CaptureFact(
            capture_id=capture_id,
            asset=asset,
            provider="kalshi",
            source_id=source_id,
            channel=channel,
            message_type=message_type,
            event_subtype=event_subtype,
            sid=sid,
            seq=seq,
            provider_timestamp=provider_timestamp,
            received_timestamp=received_timestamp,
            schema_version=_SCHEMA_VERSION,
            payload=message.model_dump_json(),
        )

    def _require_verified_identity(
        self, identity: VerifiedMarketIdentity
    ) -> VerifiedMarketIdentity:
        if type(identity) is not VerifiedMarketIdentity:
            raise CaptureAuthorityError("Capture Boundary requires VerifiedMarketIdentity")
        if not identity.has_verified_provenance:
            raise CaptureAuthorityError(
                "Capture Boundary requires verifier-issued market identity"
            )
        return identity

    @staticmethod
    def _require_discriminator(message: BaseModel, expected: str) -> None:
        if getattr(message, "type", None) != expected:
            raise IncompatibleCaptureInputError(
                f"message discriminator must be {expected}"
            )

    @staticmethod
    def _require_market_ticker(
        market_ticker: str, identity: VerifiedMarketIdentity
    ) -> None:
        if market_ticker != identity.ticker:
            raise IncompatibleCaptureInputError(
                "message market_ticker does not match verified identity"
            )

    @staticmethod
    def _milliseconds_to_ns(value: int) -> int:
        if not isinstance(value, int):
            raise IncompatibleCaptureInputError("provider timestamp milliseconds must be int")
        return value * _NANOSECONDS_PER_MILLISECOND

    @staticmethod
    def _delta_timestamp(message: OrderbookDeltaMessage) -> int | None:
        if message.msg.ts_ms is not None:
            return CaptureBoundary._milliseconds_to_ns(message.msg.ts_ms)
        legacy_timestamp = message.msg.ts
        if not isinstance(legacy_timestamp, datetime):
            return None
        if legacy_timestamp.tzinfo is None or legacy_timestamp.utcoffset() is None:
            return None
        delta = legacy_timestamp.astimezone(UTC) - _EPOCH
        return (
            (delta.days * 86_400 + delta.seconds) * 1_000_000_000
            + delta.microseconds * 1_000
        )

    def _reference_binding(self, source: ReferenceSource, provider_id: str):
        binding = next(
            (
                candidate
                for candidate in self._reference_scope.bindings
                if candidate.source is source and candidate.provider_id == provider_id
            ),
            None,
        )
        if binding is None:
            raise CaptureAuthorityError("reference provider ID is not approved")
        return binding

    @staticmethod
    def _identity_asset(identity: VerifiedMarketIdentity) -> AssetId:
        return CaptureBoundary._binding_asset(identity.binding.asset_id)

    @staticmethod
    def _binding_asset(asset_id: str) -> AssetId:
        try:
            return AssetId(asset_id)
        except ValueError as error:
            raise CaptureAuthorityError("authority has a non-canonical asset") from error

    def _received_timestamp(self) -> int:
        received_timestamp = self._clock_ns()
        if not isinstance(received_timestamp, int):
            raise IncompatibleCaptureInputError("clock must return nanoseconds as int")
        return received_timestamp
