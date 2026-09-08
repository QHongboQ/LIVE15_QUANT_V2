import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.storage.capture import CaptureFact

ROOT = Path(__file__).parents[1]
DATA_TRUTH = ROOT / "src" / "live15_quant_v2" / "data" / "data_truth"


def test_semantic_tree_is_exactly_event_and_observation_facts() -> None:
    modules = {path.stem for path in DATA_TRUTH.glob("*.py")}

    assert {"event_facts", "observation_facts"} <= modules
    assert "questdb_history" not in modules


def test_history_protocol_has_exactly_three_public_methods() -> None:
    source = ast.parse((DATA_TRUTH / "history.py").read_text(encoding="utf-8"))
    history = next(node for node in source.body if isinstance(node, ast.ClassDef) and node.name == "TruthDecisionHistory")

    assert [node.name for node in history.body if isinstance(node, ast.FunctionDef)] == [
        "find_subject_decision",
        "find_accepted_event",
        "append",
    ]


def test_event_and_observation_leaves_have_no_forbidden_sibling_or_storage_dependencies() -> None:
    event_source = (DATA_TRUTH / "event_facts.py").read_text(encoding="utf-8").lower()
    observation_source = (DATA_TRUTH / "observation_facts.py").read_text(encoding="utf-8").lower()

    assert "hot_store" not in event_source
    assert "questdb" not in event_source
    assert "observation_facts" not in event_source
    assert "event_facts" not in observation_source


def test_package_exports_only_provider_neutral_contracts() -> None:
    from live15_quant_v2.data import data_truth

    assert "EventFacts" not in data_truth.__all__
    assert "ObservationFacts" not in data_truth.__all__
    assert "QuestDB" not in " ".join(data_truth.__all__)


def test_capture_fact_contract_remains_exact_and_immutable() -> None:
    assert [field.name for field in fields(CaptureFact)] == [
        "capture_id", "asset", "provider", "source_id", "channel", "message_type",
        "event_subtype", "sid", "seq", "provider_timestamp", "received_timestamp",
        "schema_version", "payload",
    ]
    fact = CaptureFact("capture", AssetId.BTC, "kalshi", "source", "trade", "trade", None, 1, None, None, 2, "market-ingress/v1", "{}")
    with pytest.raises(FrozenInstanceError):
        fact.payload = "mutated"


def test_slice_one_contains_no_persistent_or_multi_writer_infrastructure() -> None:
    source = "\n".join(path.read_text(encoding="utf-8").lower() for path in DATA_TRUTH.glob("*.py"))

    for forbidden in ("import questdb", "threading", "multiprocessing", "lock(", "dedup", "upsert"):
        assert forbidden not in source


def test_production_package_contains_no_fake_history_or_stateful_observation_policy() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in DATA_TRUTH.glob("*.py"))
    observation_tree = ast.parse(
        (DATA_TRUTH / "observation_facts.py").read_text(encoding="utf-8")
    )
    observation_policy = next(
        node
        for node in observation_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ObservationFacts"
    )

    assert "FakeTruthDecisionHistory" not in source
    assert [
        node.name for node in observation_policy.body if isinstance(node, ast.FunctionDef)
    ] == ["decide"]
