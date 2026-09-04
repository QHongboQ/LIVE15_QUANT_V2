from __future__ import annotations

import re
import tomllib
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


def test_workflow_is_runner_neutral_and_uses_python_authority() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    authority = (ROOT / ".python-version").read_text(encoding="utf-8").strip()

    assert authority
    assert authority not in workflow
    assert "uv sync --locked --dev" not in workflow
    assert "Install locked foundation" not in workflow
    assert "UV_PYTHON_VERSION" not in workflow
    assert "$env:" not in workflow
    assert workflow.count("id: python_authority") == 1
    assert workflow.count("version-file: uv.toml") == workflow.count("uses: astral-sh/setup-uv@")
    assert workflow.count("python_version: ${{ steps.python_authority.outputs.version }}") == 1
    assert workflow.count('uv python install "$python_version"') == 1
    assert workflow.count('uv run --no-project --python "${{ steps.python_authority.outputs.version }}"') == 1
    assert workflow.count('uv python install "${{ needs.route.outputs.python_version }}"') == 1
    assert workflow.count('uv run --no-project --python "${{ needs.route.outputs.python_version }}"') == 1
    assert "if [[ ! -f .python-version ]]" in workflow
    assert 'if [[ -z "${python_version//[[:space:]]/}"' in workflow


def test_no_ci_file_copies_python_authority_value() -> None:
    authority = (ROOT / ".python-version").read_text(encoding="utf-8").strip()

    for path in CI_FILES:
        assert authority not in path.read_text(encoding="utf-8"), path


def test_uv_has_one_repository_owned_required_version_authority() -> None:
    uv_config_path = ROOT / "uv.toml"
    uv_config = tomllib.loads(uv_config_path.read_text(encoding="utf-8"))
    requirement = uv_config["required-version"]
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert isinstance(requirement, str)
    assert requirement.startswith("==")
    assert requirement not in workflow
    assert "required-version" not in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert list(ROOT.glob("uv.toml")) == [uv_config_path]


def test_checkout_and_setup_uv_are_immutable_sha_pins() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    checkout_shas = re.findall(r"uses: actions/checkout@([0-9a-f]{40})", workflow)
    setup_uv_shas = re.findall(r"uses: astral-sh/setup-uv@([0-9a-f]{40})", workflow)
    assert len(checkout_shas) == 2
    assert len(setup_uv_shas) == 2
    assert len(set(checkout_shas)) == 1
    assert len(set(setup_uv_shas)) == 1
    assert "actions/checkout@v7" not in workflow


def test_foundation_descriptor_owns_setup_and_all_foundation_paths() -> None:
    foundation = next(scope for scope in discover_scopes(ROOT) if scope.name == "foundation")
    config = (ROOT / "ci" / "config.toml").read_text(encoding="utf-8")
    foundation_paths = (ROOT / "ci" / "scopes" / "foundation.toml").read_text(encoding="utf-8")

    assert foundation.commands[0] == ("uv", "sync", "--locked", "--dev")
    assert "tests/test_run_scope.py" in foundation.paths
    assert ".python-version" in config and "uv.toml" in config
    assert ".python-version" not in foundation_paths
    assert "uv.toml" not in foundation_paths
    assert "ci/__init__.py" in config


def test_python_authority_change_does_not_require_workflow_edit(tmp_path: Path) -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    authority = tmp_path / ".python-version"
    authority.write_text("3.13.0\n", encoding="utf-8")

    assert authority.read_text(encoding="utf-8").strip() == "3.13.0"
    assert "3.13.0" not in workflow
    assert 'uv python install "${{ needs.route.outputs.python_version }}"' in workflow
    assert 'uv run --no-project --python "${{ needs.route.outputs.python_version }}"' in workflow