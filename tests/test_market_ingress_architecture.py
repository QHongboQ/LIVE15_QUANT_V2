from pathlib import Path

import live15_quant_v2.data.market_ingress.ingress_boundary as boundary_public
import live15_quant_v2.data.market_ingress.kalshi_gateway as gateway_public

SOURCE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "live15_quant_v2"
    / "data"
    / "market_ingress"
)


def test_sibling_ownership_and_parent_composition_are_structural() -> None:
    parent = (SOURCE_ROOT / "__init__.py").read_text(encoding="utf-8")
    gateway = (SOURCE_ROOT / "kalshi_gateway" / "gateway.py").read_text(
        encoding="utf-8"
    )
    discovery = (SOURCE_ROOT / "ingress_boundary" / "discovery.py").read_text(
        encoding="utf-8"
    )

    assert not (SOURCE_ROOT / "kalshi_gateway" / "identity").exists()
    assert gateway_public.__all__ == ["KalshiGateway"]
    assert "ingress_boundary" not in gateway
    assert "kalshi_gateway" not in discovery
    assert "build_market_identity_resolver" in parent
    for private_leaf in ("candidate", "discovery", "shadow", "verification"):
        assert f"ingress_boundary.{private_leaf}" not in parent


def test_boundary_public_surface_is_semantic_and_candidate_is_internal() -> None:
    assert "CandidateTickerPredictor" not in boundary_public.__all__
    assert "MarketIdentityResolver" in boundary_public.__all__
    assert "MarketScopePort" in boundary_public.__all__
    assert "build_market_identity_resolver" in boundary_public.__all__


def test_parent_composition_enforces_the_live15_scope_authority() -> None:
    parent = (SOURCE_ROOT / "__init__.py").read_text(encoding="utf-8")
    composition = (
        SOURCE_ROOT / "ingress_boundary" / "composition.py"
    ).read_text(encoding="utf-8")

    assert "Live15MarketScopeConfig()" in composition
    assert "MarketScopePort" not in parent
    assert "scope:" not in parent


def test_verified_identity_provenance_factory_is_contained_to_verifier() -> None:
    boundary_root = SOURCE_ROOT / "ingress_boundary"
    verification = (boundary_root / "verification.py").read_text(encoding="utf-8")
    assert "._from_official_verification(" in verification

    for path in SOURCE_ROOT.rglob("*.py"):
        if path.name in {"models.py", "verification.py"}:
            continue
        source = path.read_text(encoding="utf-8")
        assert "_VERIFIED_MARKET_IDENTITY_TOKEN" not in source
        assert "._from_official_verification(" not in source
