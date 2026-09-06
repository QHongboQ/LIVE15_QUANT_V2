import re
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.storage.capture import CaptureFact

ROOT = Path(__file__).parents[1]


def test_questdb_hot_store_is_not_exported_from_hot_store_package_root() -> None:
    from live15_quant_v2.data.storage import hot_store

    assert "QuestDBHotStore" not in hot_store.__all__
    assert not hasattr(hot_store, "QuestDBHotStore")


def test_shared_capture_contract_is_not_owned_or_exported_by_hot_store() -> None:
    from live15_quant_v2.data.storage import hot_store
    from live15_quant_v2.data.storage.hot_store import models

    assert CaptureFact.__module__ == "live15_quant_v2.data.storage.capture"
    assert "CaptureFact" not in hot_store.__all__
    assert not hasattr(hot_store, "CaptureFact")
    assert not hasattr(models, "CaptureFact")


def test_shared_capture_contract_is_exact_and_immutable() -> None:
    assert [field.name for field in fields(CaptureFact)] == [
        "capture_id",
        "asset",
        "provider",
        "source_id",
        "channel",
        "message_type",
        "event_subtype",
        "sid",
        "seq",
        "provider_timestamp",
        "received_timestamp",
        "schema_version",
        "payload",
    ]
    fact = CaptureFact(
        "capture-1",
        AssetId.BTC,
        "kalshi",
        "KXBTC15M-TICKER",
        "orderbook",
        "orderbook_snapshot",
        None,
        1,
        2,
        3,
        4,
        "market-ingress/v1",
        "{}",
    )

    with pytest.raises(FrozenInstanceError):
        fact.payload = '{"mutated":true}'


def test_storage_shared_contract_has_no_hot_store_or_questdb_dependency() -> None:
    source = (
        ROOT / "src" / "live15_quant_v2" / "data" / "storage" / "capture.py"
    ).read_text(encoding="utf-8")

    assert "hot_store" not in source
    assert "questdb" not in source


def test_asset_id_is_the_exact_canonical_nine_without_normalization() -> None:
    assert tuple(AssetId) == (
        AssetId.BTC,
        AssetId.ETH,
        AssetId.GOLD,
        AssetId.SILVER,
        AssetId.XRP,
        AssetId.SOL,
        AssetId.HYPE,
        AssetId.DOGE,
        AssetId.BNB,
    )
    with pytest.raises(ValueError):
        AssetId("Gold")
    with pytest.raises(ValueError):
        AssetId("gold")


def test_capture_boundary_is_a_storage_sibling_without_hot_store_coupling() -> None:
    boundary = ROOT / "src" / "live15_quant_v2" / "data" / "storage" / "capture_boundary"
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in boundary.glob("*.py")
    )

    assert boundary.exists()
    assert "hot_store" not in source
    assert "questdb" not in source.lower()


def test_questdb_import_is_contained_inside_hot_store_adapter() -> None:
    imports = []
    for source in (ROOT / "src" / "live15_quant_v2").rglob("*.py"):
        if re.search(r"^import questdb$", source.read_text(encoding="utf-8"), re.MULTILINE):
            imports.append(source.relative_to(ROOT).as_posix())

    assert imports == [
        "src/live15_quant_v2/data/storage/hot_store/questdb_adapter.py",
    ]
