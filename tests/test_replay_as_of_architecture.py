"""Architecture boundaries for the provider-neutral Replay & As-Of pure core."""

import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]
REPLAY = ROOT / "src" / "live15_quant_v2" / "data" / "replay_as_of"
PACKAGE = "live15_quant_v2.data.replay_as_of"


def _imports(module_name: str) -> set[str]:
    imports: set[str] = set()
    source_module = f"{PACKAGE}.{Path(module_name).stem}"
    for node in ast.walk(ast.parse((REPLAY / module_name).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            if node.level:
                package = source_module.rsplit(".", 1)[0].split(".")
                base = ".".join(package[: len(package) - node.level + 1])
                module = f"{base}.{module}" if module else base
            if module is not None:
                imports.add(module)
                imports.update(f"{module}.{alias.name}" for alias in node.names)
    return imports


def test_slice_three_module_tree_is_exact_and_excludes_future_slices() -> None:
    assert {path.name for path in REPLAY.glob("*.py")} == {
        "__init__.py",
        "models.py",
        "service.py",
        "source.py",
        "availability.py",
        "questdb_availability.py",
        "questdb_source.py",
    }


def test_slice_two_core_never_imports_provider_or_physical_runtime_details() -> None:
    imports = set().union(
        *(
            _imports(name)
            for name in ("models.py", "service.py", "source.py", "availability.py")
        )
    )

    for forbidden in (
        "questdb",
        "pandas",
        "data_truth.composition",
        "QuestDBHotStore",
        "QuestDBTruthDecisionHistory",
    ):
        assert not any(forbidden.casefold() in item.casefold() for item in imports)


def test_slice_two_core_contains_no_data_truth_call_or_offset_pagination() -> None:
    source = "\n".join(
        (REPLAY / name).read_text(encoding="utf-8")
        for name in (
            "__init__.py",
            "models.py",
            "service.py",
            "source.py",
            "availability.py",
        )
    )

    assert "DataTruth.decide" not in source
    assert "OFFSET" not in source
    assert "questdb" not in source.casefold()
    assert "sql" not in source.casefold()


def test_package_exports_only_provider_neutral_slice_one_api() -> None:
    from live15_quant_v2.data import replay_as_of

    assert replay_as_of.__all__ == [
        "AsOfReplayView",
        "AsOfRequest",
        "AuthoritativeReplayRecord",
        "ReplayAsOf",
        "ReplayAsOfError",
        "ReplayCandidateScope",
        "ReplayErrorCode",
        "ReplayOrdering",
        "ReplaySource",
        "SelectionAxis",
        "SelectionWindow",
    ]
    assert "InMemoryReplaySource" not in vars(replay_as_of)
    assert "AvailabilityReference" not in vars(replay_as_of)


def test_slice_two_adapter_has_no_replacement_or_future_composition_surface() -> None:
    adapter = (REPLAY / "questdb_availability.py").read_text(encoding="utf-8")

    assert "UPDATE " not in adapter
    assert "DELETE " not in adapter
    assert "UPSERT" not in adapter
    assert "OFFSET" not in adapter
    assert "DataTruth.decide" not in adapter
    assert "recorder_composition" not in adapter
    assert "table_name: str =" not in adapter


def test_slice_three_source_is_read_only_and_has_no_runtime_or_composition_coupling() -> (
    None
):
    adapter = (REPLAY / "questdb_source.py").read_text(encoding="utf-8")

    for forbidden in (
        "CREATE ",
        "ALTER ",
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "UPSERT",
        "OFFSET",
        ".sender(",
        ".row(",
        ".flush",
        "DataTruth.decide",
        "recorder_composition",
        "QuestDBHotStore",
        "QuestDBTruthDecisionHistory",
        "QuestDBAvailabilityStore",
    ):
        assert forbidden not in adapter
