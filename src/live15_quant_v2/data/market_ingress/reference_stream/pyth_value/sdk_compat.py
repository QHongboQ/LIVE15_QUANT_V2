"""Contained v13.0.0 Pyth registry compatibility for Kalshi's official channel.

Provenance: TexasCoding/kalshi-python-sdk commit
16c0b8368cc27991311d513a8dc5a0814dd786e0. Delete this module when a pinned
SDK supplies native typed ``pyth_value`` registration and a public helper.
"""

from __future__ import annotations

from importlib.metadata import version
from typing import Any, cast

from kalshi.ws import channels as _channels
from kalshi.ws import dispatch as _dispatch

from live15_quant_v2.data.market_ingress.reference_stream.pyth_value.models import (
    PythUnderlyingListMessage,
    PythValueMessage,
)

_SDK_VERSION = "13.0.0"
_PYTH_CHANNEL = "pyth_value"
_PYTH_LIST_MESSAGE = "pyth_value_underlying_list"
_PYTH_PARAMS = frozenset({"underlying_tickers"})
_EXPECTED_FORWARD_KEYS = (
    "market_ticker",
    "market_tickers",
    "market_id",
    "market_ids",
    "shard_factor",
    "shard_key",
    "send_initial_snapshot",
    "skip_ticker_ack",
    "index_ids",
)


def install_pyth_sdk_compat() -> None:
    """Install the exact v13 registry entries once, or fail closed."""
    if version("kalshi-sdk") != _SDK_VERSION:
        raise RuntimeError("Pyth compatibility requires kalshi-sdk==13.0.0")
    _install_subscription_params()
    _install_message_models()


def _install_subscription_params() -> None:
    forward_keys = _channels._SUBSCRIBE_FORWARD_KEYS
    expected_with_pyth: tuple[str, ...] = _EXPECTED_FORWARD_KEYS + (
        "underlying_tickers",
    )
    if forward_keys == _EXPECTED_FORWARD_KEYS:
        cast(Any, _channels)._SUBSCRIBE_FORWARD_KEYS = expected_with_pyth
    elif forward_keys != expected_with_pyth:
        raise RuntimeError("unexpected kalshi-sdk v13 subscribe forwarding registry")

    existing = _channels._CHANNEL_PARAMS.get(_PYTH_CHANNEL)
    if existing is None:
        _channels._CHANNEL_PARAMS[_PYTH_CHANNEL] = _PYTH_PARAMS
    elif existing != _PYTH_PARAMS:
        raise RuntimeError("conflicting kalshi-sdk pyth_value parameter registry")


def _install_message_models() -> None:
    _install_message_model(_PYTH_CHANNEL, PythValueMessage)
    _install_message_model(_PYTH_LIST_MESSAGE, PythUnderlyingListMessage)


def _install_message_model(
    name: str, model: type[PythValueMessage | PythUnderlyingListMessage]
) -> None:
    existing = _dispatch.MESSAGE_MODELS.get(name)
    if existing is None:
        _dispatch.MESSAGE_MODELS[name] = model
    elif existing is not model:
        raise RuntimeError(f"conflicting kalshi-sdk {name} message registry")
