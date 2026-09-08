import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.storage.capture import CaptureFact

ROOT = Path(__file__).parents[1]
DATA_TRUTH = ROOT / "src" / "live15_quant_v2" / "data" / "data_truth"


def _imported_modules(source: str) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            imports.add(node.module)
            imports.update(f"{node.module}.{alias.name}" for alias in node.names)
    return imports


def _module_imports(module_name: str) -> set[str]:
    return _imported_modules((DATA_TRUTH / module_name).read_text(encoding="utf-8"))


def _has_forbidden_import(imports: set[str], fragment: str) -> bool:
    return any(fragment.casefold() in imported.casefold() for imported in imports)


def test_ast_import_extraction_handles_import_and_import_from() -> None:
    assert _imported_modules("import alpha.beta\nfrom gamma.delta import Value\n") == {
        "alpha.beta",
        "gamma.delta",
        "gamma.delta.Value",
    }


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
    event_imports = _module_imports("event_facts.py")
    observation_imports = _module_imports("observation_facts.py")

    for forbidden in (
        "observation_facts",
        "hot_store",
        "questdb",
        "sql",
        "table",
        "capture_boundary",
        "questdb_adapter",
    ):
        assert not _has_forbidden_import(event_imports, forbidden)
    for forbidden in ("event_facts", "hot_store", "questdb", "sql", "table", "kalshi"):
        assert not _has_forbidden_import(observation_imports, forbidden)


def test_support_modules_do_not_import_storage_or_provider_runtime_details() -> None:
    for module_name in ("history.py", "composition.py", "models.py"):
        imports = _module_imports(module_name)
        for forbidden in ("hot_store", "questdb", "sql"):
            assert not _has_forbidden_import(imports, forbidden)
    assert not _has_forbidden_import(_module_imports("models.py"), "kalshi")


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


def test_production_package_contains_no_fake_or_memory_backed_history_module() -> None:
    modules = {path.name for path in DATA_TRUTH.glob("*.py")}

    assert "questdb_history.py" not in modules
    assert not any("fake" in module or "memory" in module for module in modules)
