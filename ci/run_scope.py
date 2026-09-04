"""Execute exactly one validated CI scope descriptor."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from ci.router import RouterError, discover_scopes


def run_scope(scope_name: str, root: Path | str = ".", *, dry_run: bool = False) -> int:
    """Run one named scope's declared commands with shell=False."""

    root_path = Path(root).resolve()
    scopes = {scope.name: scope for scope in discover_scopes(root_path)}
    scope = scopes.get(scope_name)
    if scope is None:
        raise RouterError(f"unknown scope: {scope_name}")
    for command in scope.commands:
        print("$", " ".join(command), flush=True)
        if dry_run:
            continue
        completed = subprocess.run(command, cwd=root_path, check=False, shell=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        return run_scope(args.scope, args.root, dry_run=args.dry_run)
    except RouterError as exc:
        print(f"CI scope error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
