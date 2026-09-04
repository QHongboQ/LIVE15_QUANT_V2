"""Discover and select registered CI scopes from changed paths."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


class RouterError(ValueError):
    """Raised when CI configuration or a routing request is invalid."""


@dataclass(frozen=True)
class ScopeDescriptor:
    name: str
    runner: str
    paths: tuple[str, ...]
    depends_on: tuple[str, ...]
    commands: tuple[tuple[str, ...], ...]
    descriptor_path: str


@dataclass(frozen=True)
class RouteResult:
    scope_names: tuple[str, ...]
    matrix: list[dict[str, str]]


_SCOPE_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_REQUIRED_SCOPE_KEYS = {"name", "runner", "paths", "depends_on", "commands"}


def _normalise_path(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RouterError(f"invalid {label}")
    raw = value.strip().replace("\\", "/")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise RouterError(f"invalid {label}: absolute path")
    normalised = posixpath.normpath(raw)
    if normalised in {"", "."} or normalised == ".." or normalised.startswith("../"):
        raise RouterError(f"invalid {label}")
    return normalised


def _load_config(root: Path) -> tuple[str, tuple[str, ...]]:
    config_path = root / "ci" / "config.toml"
    try:
        with config_path.open("rb") as stream:
            data = tomllib.load(stream)
    except FileNotFoundError as exc:
        raise RouterError("malformed CI control-plane config: ci/config.toml is missing") from exc
    except tomllib.TOMLDecodeError as exc:
        raise RouterError(f"malformed CI control-plane config: {exc}") from exc
    if not isinstance(data, dict) or set(data) != {"scope_directory", "control_plane_paths"}:
        raise RouterError("malformed CI control-plane config")
    scope_directory = _normalise_path(data["scope_directory"], label="scope directory")
    control_paths = data["control_plane_paths"]
    if not isinstance(control_paths, list) or not control_paths:
        raise RouterError("malformed CI control-plane paths")
    normalised = {_normalise_path(path, label="control-plane path") for path in control_paths}
    normalised.add("ci/config.toml")
    return scope_directory, tuple(sorted(normalised))


def _parse_scope(path: Path, root: Path) -> ScopeDescriptor:
    try:
        with path.open("rb") as stream:
            data = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise RouterError(f"malformed descriptor: {path.as_posix()}") from exc
    if not isinstance(data, dict) or set(data) != _REQUIRED_SCOPE_KEYS:
        raise RouterError(f"malformed descriptor: {path.as_posix()}")

    name = data["name"]
    if not isinstance(name, str) or not _SCOPE_NAME.fullmatch(name):
        raise RouterError(f"invalid scope name in {path.as_posix()}")
    runner = data["runner"]
    if not isinstance(runner, str) or not runner.strip():
        raise RouterError(f"malformed descriptor: {path.as_posix()}")

    raw_paths = data["paths"]
    if not isinstance(raw_paths, list) or not raw_paths:
        raise RouterError(f"malformed descriptor: {path.as_posix()}")
    paths = tuple(_normalise_path(value, label="scope path") for value in raw_paths)

    raw_dependencies = data["depends_on"]
    if not isinstance(raw_dependencies, list) or any(not isinstance(value, str) or not value for value in raw_dependencies):
        raise RouterError(f"malformed descriptor: {path.as_posix()}")
    dependencies = tuple(raw_dependencies)

    raw_commands = data["commands"]
    if not isinstance(raw_commands, list) or not raw_commands:
        raise RouterError(f"malformed command definition: {path.as_posix()}")
    commands: list[tuple[str, ...]] = []
    for command in raw_commands:
        if not isinstance(command, list) or not command or any(not isinstance(argument, str) or not argument for argument in command):
            raise RouterError(f"malformed command definition: {path.as_posix()}")
        commands.append(tuple(command))

    descriptor_path = path.relative_to(root).as_posix()
    return ScopeDescriptor(name, runner.strip(), paths, dependencies, tuple(commands), descriptor_path)


def discover_scopes(root: Path | str = ".") -> tuple[ScopeDescriptor, ...]:
    """Discover, parse, and validate every registered scope descriptor."""

    root_path = Path(root).resolve()
    scope_directory, _ = _load_config(root_path)
    descriptor_dir = root_path / scope_directory
    try:
        descriptor_paths = sorted(descriptor_dir.glob("*.toml"))
    except OSError as exc:
        raise RouterError("malformed scope directory") from exc

    scopes = tuple(_parse_scope(path, root_path) for path in descriptor_paths)
    names = [scope.name for scope in scopes]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise RouterError(f"duplicate scope name: {duplicates[0]}")
    known = set(names)
    for scope in scopes:
        for dependency in scope.depends_on:
            if dependency not in known:
                raise RouterError(f"missing dependency: {scope.name} -> {dependency}")

    dependencies = {scope.name: set(scope.depends_on) for scope in scopes}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            raise RouterError(f"dependency cycle involving: {name}")
        if name in visited:
            return
        visiting.add(name)
        for dependency in sorted(dependencies[name]):
            visit(dependency)
        visiting.remove(name)
        visited.add(name)

    for name in sorted(known):
        visit(name)
    return tuple(sorted(scopes, key=lambda scope: scope.name))


def _path_matches(changed: str, owned: str) -> bool:
    return changed == owned or changed.startswith(f"{owned.rstrip('/')}/")


def _expand_graph(selected: set[str], scopes: tuple[ScopeDescriptor, ...]) -> set[str]:
    dependencies = {scope.name: set(scope.depends_on) for scope in scopes}
    dependents: dict[str, set[str]] = {scope.name: set() for scope in scopes}
    for scope in scopes:
        for dependency in scope.depends_on:
            dependents[dependency].add(scope.name)
    direct = set(selected)

    def walk(start: str, edges: dict[str, set[str]]) -> set[str]:
        found = {start}
        pending = [start]
        while pending:
            name = pending.pop()
            for neighbour in edges[name]:
                if neighbour not in found:
                    found.add(neighbour)
                    pending.append(neighbour)
        return found

    selected.clear()
    for name in direct:
        selected.update(walk(name, dependencies))
        selected.update(walk(name, dependents))
    return selected


def route_scopes(
    root: Path | str = ".",
    *,
    changed_files: Iterable[str],
    mode: str = "AUTO",
    requested_scope: str | None = None,
) -> RouteResult:
    """Return the deterministic scope matrix for AUTO, FULL, or SCOPE mode."""

    root_path = Path(root).resolve()
    scopes = discover_scopes(root_path)
    scope_by_name = {scope.name: scope for scope in scopes}
    mode_upper = mode.upper()
    if mode_upper not in {"AUTO", "FULL", "SCOPE"}:
        raise RouterError(f"unknown routing mode: {mode}")

    if mode_upper == "FULL":
        selected = set(scope_by_name)
    elif mode_upper == "SCOPE":
        if not requested_scope or requested_scope not in scope_by_name:
            raise RouterError(f"unknown scope: {requested_scope or ''}".rstrip())
        selected = {requested_scope}
    else:
        _, control_paths = _load_config(root_path)
        changed = {_normalise_path(path, label="changed file") for path in changed_files}
        if changed & set(control_paths):
            selected = set(scope_by_name)
        else:
            descriptor_by_path = {scope.descriptor_path: scope.name for scope in scopes}
            selected = {
                scope.name
                for scope in scopes
                if scope.descriptor_path in changed
                or any(_path_matches(changed_path, owned_path) for changed_path in changed for owned_path in scope.paths)
            }
            selected.update(descriptor_by_path[path] for path in changed if path in descriptor_by_path)

    selected = _expand_graph(selected, scopes)
    ordered = tuple(sorted(selected))
    return RouteResult(ordered, [{"scope": name, "runner": scope_by_name[name].runner} for name in ordered])


def _read_changed_files(path: str | None) -> list[str]:
    if not path:
        return []
    try:
        return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError as exc:
        raise RouterError(f"cannot read changed-files file: {path}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--mode", default="AUTO")
    parser.add_argument("--scope", dest="requested_scope")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--changed-files-file")
    args = parser.parse_args(argv)
    try:
        result = route_scopes(args.root, changed_files=[*args.changed_file, *_read_changed_files(args.changed_files_file)], mode=args.mode, requested_scope=args.requested_scope)
    except RouterError as exc:
        print(f"CI Router error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.matrix, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
