from __future__ import annotations

from pathlib import Path

from ci.router import discover_scopes

ROOT = Path(__file__).resolve().parents[1]
CI_FILES = (
    ROOT / ".github" / "workflows" / "ci.yml",
    ROOT / "ci" / "config.toml",
    ROOT / "ci" / "router.py",
    ROOT / "ci" / "run_scope.py",
    ROOT / "ci" / "scopes" / "foundation.toml",
    ROOT / "tests" / "test_ci_contract.py",
    ROOT / "tests" / "test_router.py",
    ROOT / "tests" / "test_run_scope.py",
)


def test_workflow_is_generic_and_uses_no_project_bootstrap() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    authority = (ROOT / ".python-version").read_text(encoding="utf-8").strip()

    assert authority
    assert "uv sync --locked --dev" not in workflow
    assert "Install locked foundation" not in workflow
    assert workflow.count('uv run --no-project --python "$UV_PYTHON_VERSION"') == 2
    assert workflow.count('uv python install "$UV_PYTHON_VERSION"') == 2
    assert workflow.count(".python-version") >= 4
    assert "if [[ ! -f .python-version ]]" in workflow
    assert 'if [[ -z "${UV_PYTHON_VERSION//[[:space:]]/}" ]]' in workflow


def test_no_ci_file_copies_python_authority_value() -> None:
    authority = (ROOT / ".python-version").read_text(encoding="utf-8").strip()

    for path in CI_FILES:
        assert authority not in path.read_text(encoding="utf-8"), path


def test_foundation_descriptor_owns_setup_and_all_foundation_paths() -> None:
    foundation = next(scope for scope in discover_scopes(ROOT) if scope.name == "foundation")

    assert foundation.commands[0] == ("uv", "sync", "--locked", "--dev")
    assert "tests/test_run_scope.py" in foundation.paths
    assert "ci/__init__.py" in (ROOT / "ci" / "config.toml").read_text(encoding="utf-8")


def test_python_authority_change_does_not_require_workflow_edit(tmp_path: Path) -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    authority = tmp_path / ".python-version"
    authority.write_text("3.13.0\n", encoding="utf-8")

    assert authority.read_text(encoding="utf-8").strip() == "3.13.0"
    assert "3.13.0" not in workflow
    assert 'uv python install "$UV_PYTHON_VERSION"' in workflow
    assert 'uv run --no-project --python "$UV_PYTHON_VERSION"' in workflow