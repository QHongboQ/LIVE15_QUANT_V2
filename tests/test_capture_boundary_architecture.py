"""Architecture constraints for the narrow synchronous Capture Boundary."""

import ast
import inspect
from pathlib import Path

from live15_quant_v2.data.storage.capture_boundary import CaptureBoundary


def test_capture_boundary_stays_synchronous_and_side_effect_free() -> None:
    package = Path(__file__).parents[1] / "src/live15_quant_v2/data/storage/capture_boundary"
    source = "\n".join(path.read_text(encoding="utf-8") for path in package.glob("*.py"))
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert not inspect.iscoroutinefunction(CaptureBoundary.capture_market)
    assert not inspect.iscoroutinefunction(CaptureBoundary.capture_reference)
    assert "hot_store" not in source
    assert "questdb" not in source.lower()
    assert "async " not in source
    assert not any(
        token in source.lower()
        for token in ("queue", "thread", "socket", "requests", "http", "wal", "retry")
    )
    assert not any(name.startswith(("asyncio", "queue", "threading", "socket")) for name in imports)


def test_capture_boundary_consumes_the_existing_reference_scope_without_a_mapping() -> None:
    boundary_source = inspect.getsource(CaptureBoundary)

    assert "Live15ReferenceScopeConfig" in boundary_source
    assert "BRTI" not in boundary_source
    assert "Metal.XAU/USD" not in boundary_source
