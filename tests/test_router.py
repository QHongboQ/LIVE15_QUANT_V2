from __future__ import annotations

import json
from pathlib import Path

import pytest

from ci.router import RouterError, discover_scopes, route_scopes


def write_scope(root: Path, name: str, *, paths: list[str], depends_on: list[str] | None = None, commands: list[list[str]] | None = None, runner: str = "ubuntu-latest", filename: str | None = None) -> None:
    scope_dir = root / "ci" / "scopes"
    scope_dir.mkdir(parents=True, exist_ok=True)
    dependencies = depends_on or []
    command_rows = commands or [["python", "-c", "pass"]]
    lines = [f'name = "{name}"', f'runner = "{runner}"', "depends_on = ["]
    lines.extend(f'  "{dependency}",' for dependency in dependencies)
    lines.extend(["]", "paths = ["])
    lines.extend(f'  "{path}",' for path in paths)
    lines.extend(["]", "commands = ["])
    for command in command_rows:
        lines.append("  [")
        lines.extend(f'    "{argument}",' for argument in command)
        lines.append("  ],")
    lines.append("]")
    (scope_dir / f"{filename or name}.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_root(tmp_path: Path) -> Path:
    (tmp_path / "ci").mkdir()
    (tmp_path / "ci" / "config.toml").write_text(
        'scope_directory = "ci/scopes"\n'
        'control_plane_paths = ["ci/__init__.py", "ci/router.py", "ci/run_scope.py", "ci/config.toml", ".github/workflows/ci.yml"]\n',
        encoding="utf-8",
    )
    return tmp_path


def test_direct_match_and_stable_matrix(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    write_scope(root, "foundation", paths=["src/foundation.py"], runner="windows-latest")

    result = route_scopes(root, changed_files=["src/foundation.py"])

    assert result.scope_names == ("foundation",)
    assert result.matrix == [{"scope": "foundation", "runner": "windows-latest"}]
    assert json.dumps(result.matrix, sort_keys=True) == '[{"runner": "windows-latest", "scope": "foundation"}]'


def test_unrelated_path_selects_no_leaf(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    write_scope(root, "foundation", paths=["src/foundation.py"])

    assert route_scopes(root, changed_files=["README.md"]).scope_names == ()


def test_multiple_direct_scopes_are_sorted(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    write_scope(root, "zeta", paths=["zeta.py"])
    write_scope(root, "alpha", paths=["alpha.py"])

    assert route_scopes(root, changed_files=["zeta.py", "alpha.py"]).scope_names == ("alpha", "zeta")


def test_dependency_and_downstream_closure_is_generic(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    write_scope(root, "foundation", paths=["foundation.py"])
    write_scope(root, "market-data", paths=["market.py"], depends_on=["foundation"])
    write_scope(root, "recorder", paths=["recorder.py"], depends_on=["market-data"])
    write_scope(root, "web", paths=["web.py"], depends_on=["foundation"])
    write_scope(root, "storage", paths=["storage.py"])

    assert route_scopes(root, changed_files=["recorder.py"]).scope_names == ("foundation", "market-data", "recorder")
    assert route_scopes(root, changed_files=["foundation.py"]).scope_names == ("foundation", "market-data", "recorder", "web")
    assert route_scopes(root, changed_files=["market.py"]).scope_names == ("foundation", "market-data", "recorder")
    assert route_scopes(root, changed_files=["storage.py"]).scope_names == ("storage",)


def test_full_and_manual_scope_modes(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    write_scope(root, "foundation", paths=["foundation.py"])
    write_scope(root, "web", paths=["web.py"])

    assert route_scopes(root, changed_files=[], mode="FULL").scope_names == ("foundation", "web")
    assert route_scopes(root, changed_files=[], mode="SCOPE", requested_scope="web").scope_names == ("web",)
    with pytest.raises(RouterError, match="unknown scope"):
        route_scopes(root, changed_files=[], mode="SCOPE", requested_scope="missing")



def test_scope_mode_selects_requested_scope_and_dependencies_only(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    write_scope(root, "foundation", paths=["foundation.py"])
    write_scope(root, "market-data", paths=["market.py"], depends_on=["foundation"])
    write_scope(root, "recorder", paths=["recorder.py"], depends_on=["market-data"])
    write_scope(root, "web", paths=["web.py"], depends_on=["foundation"])

    assert route_scopes(root, changed_files=[], mode="SCOPE", requested_scope="foundation").scope_names == ("foundation",)
    assert route_scopes(root, changed_files=[], mode="SCOPE", requested_scope="market-data").scope_names == ("foundation", "market-data")
    assert route_scopes(root, changed_files=[], mode="SCOPE", requested_scope="recorder").scope_names == ("foundation", "market-data", "recorder")


def test_deleted_descriptor_selects_all_current_scopes(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    write_scope(root, "foundation", paths=["foundation.py"])
    write_scope(root, "web", paths=["web.py"])

    assert route_scopes(root, changed_files=["ci/scopes/deleted.toml"]).scope_names == ("foundation", "web")


def test_ci_init_is_control_plane_path(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    write_scope(root, "foundation", paths=["foundation.py"])
    write_scope(root, "web", paths=["web.py"])

    assert route_scopes(root, changed_files=["ci/__init__.py"]).scope_names == ("foundation", "web")


def test_descriptor_change_selects_its_scope(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    write_scope(root, "foundation", paths=["foundation.py"])
    write_scope(root, "web", paths=["web.py"])

    assert route_scopes(root, changed_files=["ci/scopes/web.toml"]).scope_names == ("web",)


def test_control_plane_change_selects_all_registered_scopes(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    write_scope(root, "foundation", paths=["foundation.py"])
    write_scope(root, "web", paths=["web.py"])

    assert route_scopes(root, changed_files=["ci/router.py"]).scope_names == ("foundation", "web")


def test_zero_scope_matrix_is_empty(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    write_scope(root, "foundation", paths=["foundation.py"])

    result = route_scopes(root, changed_files=[])

    assert result.scope_names == ()
    assert result.matrix == []



def test_zero_registered_scopes_fails_closed(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    (root / "ci" / "scopes").mkdir(parents=True)

    with pytest.raises(RouterError, match="no registered scopes"):
        discover_scopes(root)
def test_empty_scope_name_fails_closed(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    write_scope(root, "", paths=["a.py"], filename="empty")

    with pytest.raises(RouterError, match="invalid scope name"):
        discover_scopes(root)


@pytest.mark.parametrize(
    ("kind", "message"),
    [
        ("duplicate", "duplicate scope name"),
        ("missing", "missing dependency"),
        ("cycle", "dependency cycle"),
        ("malformed", "malformed"),
        ("invalid-name", "invalid scope name"),
        ("bad-command", "malformed command"),
    ],
)
def test_invalid_topology_fails_closed(tmp_path: Path, kind: str, message: str) -> None:
    root = make_root(tmp_path)
    if kind == "duplicate":
        write_scope(root, "foundation", paths=["a.py"], filename="first")
        write_scope(root, "foundation", paths=["b.py"], filename="second")
    elif kind == "missing":
        write_scope(root, "foundation", paths=["a.py"], depends_on=["missing"])
    elif kind == "cycle":
        write_scope(root, "alpha", paths=["a.py"], depends_on=["beta"])
        write_scope(root, "beta", paths=["b.py"], depends_on=["alpha"])
    elif kind == "malformed":
        scope_dir = root / "ci" / "scopes"
        scope_dir.mkdir(parents=True, exist_ok=True)
        (scope_dir / "broken.toml").write_text('name = "broken"\n', encoding="utf-8")
    elif kind == "invalid-name":
        write_scope(root, "Bad_Name", paths=["a.py"])
    else:
        scope_dir = root / "ci" / "scopes"
        scope_dir.mkdir(parents=True, exist_ok=True)
        (scope_dir / "foundation.toml").write_text(
            'name = "foundation"\nrunner = "ubuntu-latest"\n'
            'depends_on = []\npaths = ["a.py"]\ncommands = [["python", 1]]\n',
            encoding="utf-8",
        )

    with pytest.raises(RouterError, match=message):
        discover_scopes(root)
