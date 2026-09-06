from pathlib import Path

REFERENCE_STREAM_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "live15_quant_v2"
    / "data"
    / "market_ingress"
    / "reference_stream"
)


def test_pyth_sdk_private_registries_are_contained_to_compat_leaf() -> None:
    for path in REFERENCE_STREAM_ROOT.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if path.name == "sdk_compat.py":
            assert "kalshi.ws import channels" in source
            assert "kalshi.ws import dispatch" in source
            continue
        assert "kalshi.ws import channels" not in source
        assert "kalshi.ws import dispatch" not in source


def test_reference_stream_has_no_custom_transport_or_reliability_ownership() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in REFERENCE_STREAM_ROOT.rglob("*.py")
    )

    assert "websocket.connect" not in source
    assert "websockets" not in source
    assert "httpx" not in source
    assert "requests" not in source
    assert "SubscriptionManager" not in source.replace("sdk_compat.py", "")
    assert "_connection" not in source
    assert "_recv_loop" not in source
    assert "_handle_reconnect" not in source


def test_reference_stream_public_composition_owns_canonical_scope() -> None:
    source = (REFERENCE_STREAM_ROOT / "composition.py").read_text(encoding="utf-8")

    assert "self._scope = Live15ReferenceScopeConfig()" in source
    assert "scope: Live15ReferenceScopeConfig" not in source


def test_pyth_value_is_public_but_control_messages_remain_compat_leaf_only() -> None:
    from live15_quant_v2.data.market_ingress import reference_stream

    assert "PythValueMessage" in reference_stream.__all__
    assert hasattr(reference_stream, "PythValueMessage")
    assert "PythUnderlyingListMessage" not in reference_stream.__all__
    assert not hasattr(reference_stream, "PythUnderlyingListMessage")
