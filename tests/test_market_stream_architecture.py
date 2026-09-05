from pathlib import Path

MARKET_STREAM_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "live15_quant_v2"
    / "data"
    / "market_ingress"
    / "market_stream"
)


def test_market_stream_uses_only_public_sibling_interfaces_and_no_transport() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in MARKET_STREAM_ROOT.glob("*.py")
    )

    assert "ingress_boundary." not in source
    assert "kalshi_gateway.gateway" not in source
    assert "websocket.connect" not in source
    assert "websockets" not in source
    assert "httpx" not in source
    assert "requests" not in source
    assert "reconnect" not in source