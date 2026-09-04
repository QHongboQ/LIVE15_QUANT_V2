from __future__ import annotations

from pathlib import Path

from ci import run_scope as scope_runner


def make_root(tmp_path: Path) -> Path:
    (tmp_path / "ci" / "scopes").mkdir(parents=True)
    (tmp_path / "ci" / "config.toml").write_text(
        'scope_directory = "ci/scopes"\n'
        'control_plane_paths = ["ci/router.py", "ci/run_scope.py", "ci/config.toml"]\n',
        encoding="utf-8",
    )
    return tmp_path


def write_scope(root: Path, name: str, command: str) -> None:
    (root / "ci" / "scopes" / f"{name}.toml").write_text(
        f'name = "{name}"\nrunner = "ubuntu-latest"\n'
        f'depends_on = []\npaths = ["{name}.py"]\n'
        f'commands = [["{command}"]]\n',
        encoding="utf-8",
    )


def test_runner_executes_only_selected_scope_commands(tmp_path: Path, monkeypatch) -> None:
    root = make_root(tmp_path)
    write_scope(root, "foundation", "foundation-check")
    write_scope(root, "web", "web-check")
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def fake_run(command, **kwargs):
        calls.append((tuple(command), kwargs))
        return scope_runner.subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(scope_runner.subprocess, "run", fake_run)

    assert scope_runner.run_scope("foundation", root) == 0
    assert calls == [
        (("foundation-check",), {"cwd": root.resolve(), "check": False, "shell": False})
    ]
