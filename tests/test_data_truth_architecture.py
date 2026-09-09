import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.storage.capture import CaptureFact

ROOT = Path(__file__).parents[1]
DATA_TRUTH = ROOT / "src" / "live15_quant_v2" / "data" / "data_truth"
_DATA_TRUTH_PACKAGE = "live15_quant_v2.data.data_truth"


def _imported_modules(source: str, *, module_name: str | None = None) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                if module_name is None:
                    raise ValueError("relative imports require a module name")
                package = module_name.rsplit(".", 1)[0].split(".")
                base = ".".join(package[: len(package) - node.level + 1])
                module = f"{base}.{node.module}" if node.module else base
            else:
                module = node.module
            if module is None:
                continue
            imports.add(module)
            imports.update(f"{module}.{alias.name}" for alias in node.names)
    return imports


def _module_imports(module_name: str) -> set[str]:
    source_module = f"{_DATA_TRUTH_PACKAGE}.{Path(module_name).stem}"
    return _imported_modules(
        (DATA_TRUTH / module_name).read_text(encoding="utf-8"),
        module_name=source_module,
    )


def _has_forbidden_import(imports: set[str], fragment: str) -> bool:
    return any(fragment.casefold() in imported.casefold() for imported in imports)


def test_ast_import_extraction_handles_normal_and_relative_import_forms() -> None:
    imports = _imported_modules(
        "import questdb\n"
        "import questdb as q\n"
        "import questdb, os\n"
        "from questdb import ingress\n"
        "from questdb.ingress import Sender\n"
        "from questdb.ingress import Sender as S\n"
        "from . import observation_facts\n"
        "from . import observation_facts as obs\n"
        "from .observation_facts import adjudicate\n"
        "from .observation_facts import adjudicate as a\n"
        "from .. import storage\n",
        module_name=f"{_DATA_TRUTH_PACKAGE}.event_facts",
    )

    assert {
        "questdb",
        "os",
        "questdb.ingress",
        "questdb.ingress.Sender",
        f"{_DATA_TRUTH_PACKAGE}.observation_facts",
        f"{_DATA_TRUTH_PACKAGE}.observation_facts.adjudicate",
        "live15_quant_v2.data.storage",
    } <= imports


def test_semantic_tree_is_exactly_event_and_observation_facts() -> None:
    modules = {path.stem for path in DATA_TRUTH.glob("*.py")}

    assert {"event_facts", "observation_facts"} <= modules
    assert "questdb_history" in modules


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
    assert "QuestDBTruthDecisionHistory" not in data_truth.__all__
    assert "QuestDBTruthDecisionHistory" not in vars(data_truth)


def test_capture_fact_contract_remains_exact_and_immutable() -> None:
    assert [field.name for field in fields(CaptureFact)] == [
        "capture_id", "asset", "provider", "source_id", "channel", "message_type",
        "event_subtype", "sid", "seq", "provider_timestamp", "received_timestamp",
        "schema_version", "payload",
    ]
    fact = CaptureFact("capture", AssetId.BTC, "kalshi", "source", "trade", "trade", None, 1, None, None, 2, "market-ingress/v1", "{}")
    with pytest.raises(FrozenInstanceError):
        fact.payload = "mutated"


def test_questdb_history_is_the_only_questdb_support_adapter() -> None:
    questdb_history_imports = _module_imports("questdb_history.py")

    assert "questdb" in questdb_history_imports
    assert "live15_quant_v2.data.storage.hot_store.port.HotStore" in questdb_history_imports
    for forbidden in ("questdb_adapter", "QuestDBHotStore"):
        assert not _has_forbidden_import(questdb_history_imports, forbidden)
    for module_name in ("event_facts.py", "observation_facts.py", "history.py", "composition.py", "models.py"):
        assert not _has_forbidden_import(_module_imports(module_name), "questdb")


def test_data_truth_has_no_multi_writer_or_history_dedup_infrastructure() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in DATA_TRUTH.glob("*.py"))
    trees = [ast.parse(path.read_text(encoding="utf-8")) for path in DATA_TRUTH.glob("*.py")]
    defined_names = {
        node.name.casefold()
        for tree in trees
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef))
    }

    assert "Kafka" not in source
    assert not {"lock", "lease", "scheduler", "daemon"} & defined_names
    assert "DEDUP" not in source
    assert "UPSERT" not in source


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

    assert "questdb_history.py" in modules
    assert not any("fake" in module or "memory" in module for module in modules)
