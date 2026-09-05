import asyncio
from decimal import Decimal

import pytest
from kalshi.ws.backpressure import MessageQueue, OverflowStrategy
from kalshi.ws.channels import Subscription
from kalshi.ws.dispatch import MESSAGE_MODELS, MessageDispatcher

from live15_quant_v2.data.market_ingress.reference_stream import (
    Live15ReferenceScopeConfig,
    ReferenceSource,
    ReferenceStream,
)
from live15_quant_v2.data.market_ingress.reference_stream.pyth_value import sdk_compat
from live15_quant_v2.data.market_ingress.reference_stream.pyth_value.models import (
    PythUnderlyingListMessage,
    PythValueMessage,
)
from live15_quant_v2.data.market_ingress.reference_stream.pyth_value.sdk_compat import (
    install_pyth_sdk_compat,
)


class FakeSocket:
    def __init__(self) -> None:
        self.cf_result = object()
        self.pyth_result = object()
        self.cf_index_ids: list[str] | None = None
        self.pyth_call: tuple[str, dict[str, object], OverflowStrategy] | None = None

    async def subscribe_cfbenchmarks_value(
        self, *, index_ids: list[str] | None = None, maxsize: int = 1000
    ) -> object:
        self.cf_index_ids = index_ids
        return self.cf_result

    async def subscribe(
        self,
        channel: str,
        *,
        params: dict[str, object] | None = None,
        overflow: OverflowStrategy = OverflowStrategy.DROP_OLDEST,
        maxsize: int = 1000,
    ) -> object:
        self.pyth_call = (channel, params or {}, overflow)
        return self.pyth_result


def test_reference_scope_is_exact_and_fails_closed() -> None:
    scope = Live15ReferenceScopeConfig()
    expected = {
        "BTC": (ReferenceSource.CF_BENCHMARKS, "BRTI"),
        "ETH": (ReferenceSource.CF_BENCHMARKS, "ETHUSD_RTI"),
        "GOLD": (ReferenceSource.PYTH_VALUE, "Metal.XAU/USD"),
        "SILVER": (ReferenceSource.PYTH_VALUE, "Metal.XAG/USD"),
        "XRP": (ReferenceSource.CF_BENCHMARKS, "XRPUSD_RTI"),
        "SOL": (ReferenceSource.CF_BENCHMARKS, "SOLUSD_RTI"),
        "HYPE": (ReferenceSource.CF_BENCHMARKS, "HYPEUSD_RTI"),
        "DOGE": (ReferenceSource.CF_BENCHMARKS, "DOGEUSD_RTI"),
        "BNB": (ReferenceSource.CF_BENCHMARKS, "BNBUSD_RTI"),
    }

    assert len(scope.bindings) == 9
    assert scope.binding_for_asset("WTI") is None
    assert scope.binding_for_asset("UNKNOWN") is None
    assert len({binding.asset_id for binding in scope.bindings}) == 9
    assert len({binding.provider_id for binding in scope.bindings}) == 9
    for asset_id, (source, provider_id) in expected.items():
        binding = scope.binding_for_asset(asset_id)
        assert binding is not None
        assert (binding.source, binding.provider_id) == (source, provider_id)


def test_cfbenchmarks_uses_native_helper_for_only_approved_scope_ids() -> None:
    socket = FakeSocket()
    result = asyncio.run(
        ReferenceStream(Live15ReferenceScopeConfig(), socket).cfbenchmarks()
    )

    assert result is socket.cf_result
    assert socket.cf_index_ids == [
        "BRTI",
        "ETHUSD_RTI",
        "XRPUSD_RTI",
        "SOLUSD_RTI",
        "HYPEUSD_RTI",
        "DOGEUSD_RTI",
        "BNBUSD_RTI",
    ]


def test_pyth_models_parse_official_asyncapi_examples_with_exact_decimal() -> None:
    value = PythValueMessage.model_validate(
        {
            "type": "pyth_value",
            "sid": 1,
            "seq": 42,
            "msg": {
                "underlying_ticker": "Metal.XAU/USD",
                "value_usd": "2365.12345000",
                "source_ts_ms": 1710000000100,
                "received_at": 1710000000123,
            },
        }
    )
    underlying_list = PythUnderlyingListMessage.model_validate(
        {
            "type": "pyth_value_underlying_list",
            "id": 2,
            "sid": 1,
            "seq": 1,
            "msg": {"underlying_tickers": ["Metal.XAG/USD", "Metal.XAU/USD"]},
        }
    )

    assert value.msg.value_usd == Decimal("2365.12345000")
    assert underlying_list.msg.underlying_tickers == [
        "Metal.XAG/USD",
        "Metal.XAU/USD",
    ]


def test_pyth_compat_is_idempotent_and_uses_existing_sdk_subscription_dispatch() -> (
    None
):
    original_models = dict(MESSAGE_MODELS)
    install_pyth_sdk_compat()
    install_pyth_sdk_compat()

    subscription = Subscription(
        1,
        "pyth_value",
        {"underlying_tickers": ["Metal.XAU/USD", "Metal.XAG/USD"]},
        MessageQueue(),
    )
    assert subscription.to_subscribe_params() == {
        "channels": ["pyth_value"],
        "underlying_tickers": ["Metal.XAU/USD", "Metal.XAG/USD"],
    }
    assert MESSAGE_MODELS["pyth_value"] is PythValueMessage
    assert MESSAGE_MODELS["pyth_value_underlying_list"] is PythUnderlyingListMessage
    assert {
        name: model
        for name, model in MESSAGE_MODELS.items()
        if name not in {"pyth_value", "pyth_value_underlying_list"}
    } == original_models

    queue = MessageQueue()

    class ActiveSubscription:
        channel = "pyth_value"
        client_id = 1
        server_sid = 7

        def __init__(self) -> None:
            self.queue = queue

    class SubscriptionManager:
        def get_subscription_by_sid(self, sid: int) -> ActiveSubscription | None:
            return ActiveSubscription() if sid == 7 else None

    asyncio.run(
        MessageDispatcher(SubscriptionManager()).dispatch(
            {
                "type": "pyth_value",
                "sid": 7,
                "seq": 42,
                "msg": {
                    "underlying_ticker": "Metal.XAU/USD",
                    "value_usd": "2365.12345000",
                    "source_ts_ms": 1710000000100,
                    "received_at": 1710000000123,
                },
            }
        )
    )
    assert isinstance(asyncio.run(anext(queue)), PythValueMessage)


def test_pyth_compat_requires_the_exact_pinned_sdk_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sdk_compat, "version", lambda _: "13.0.1")

    with pytest.raises(RuntimeError, match="kalshi-sdk==13.0.0"):
        install_pyth_sdk_compat()

def test_pyth_compat_fails_closed_on_unexpected_sdk_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kalshi.ws import channels

    monkeypatch.setattr(channels, "_SUBSCRIBE_FORWARD_KEYS", ("unexpected",))

    with pytest.raises(RuntimeError, match="forwarding registry"):
        install_pyth_sdk_compat()


def test_pyth_stream_uses_only_approved_metal_scope_and_generic_sdk_subscribe() -> None:
    socket = FakeSocket()
    result = asyncio.run(
        ReferenceStream(Live15ReferenceScopeConfig(), socket).pyth_values()
    )

    assert result is socket.pyth_result
    assert socket.pyth_call == (
        "pyth_value",
        {"underlying_tickers": ["Metal.XAU/USD", "Metal.XAG/USD"]},
        OverflowStrategy.ERROR,
    )
