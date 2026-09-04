from __future__ import annotations

from pathlib import Path

from ci.router import discover_scopes

ROOT = Path(__file__).resolve().parents[1]


def test_workflow_is_generic_and_uses_no_project_bootstrap() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "uv sync --locked --dev" not in workflow
    assert "Install locked foundation" not in workflow
    assert workflow.count("uv run --no-project --python 3.12.14") == 2


def test_foundation_descriptor_owns_setup_and_all_foundation_paths() -> None:
    foundation = next(scope for scope in discover_scopes(ROOT) if scope.name == "foundation")

    assert foundation.commands[0] == ("uv", "sync", "--locked", "--dev")
    assert "tests/test_run_scope.py" in foundation.paths
    assert "ci/__init__.py" in (ROOT / "ci" / "config.toml").read_text(encoding="utf-8")