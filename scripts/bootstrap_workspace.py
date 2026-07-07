"""Bootstrap the pinned Arc workspace dependencies from workspace.lock.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def _run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, check=True, cwd=str(cwd) if cwd else None)


def _load_lock(lock_path: Path) -> dict[str, object]:
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("workspace.lock.json must contain a JSON object")
    return payload


def _sync_dependency(repo_root: Path, dependency: dict[str, object]) -> None:
    name = dependency.get("name")
    url = dependency.get("url")
    relative_path = dependency.get("path")
    ref = dependency.get("ref")
    if not all(isinstance(value, str) and value for value in (name, url, relative_path, ref)):
        raise ValueError(f"dependency entry is incomplete: {dependency}")
    target = (repo_root / relative_path).resolve()
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        _run(["git", "clone", url, str(target)])
    _run(["git", "-C", str(target), "fetch", "--tags", "origin"])
    _run(["git", "-C", str(target), "checkout", ref])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Arc workspace dependencies.")
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path("workspace.lock.json"),
        help="Path to the workspace lock file",
    )
    args = parser.parse_args(argv)
    lock_path = args.lock.resolve()
    repo_root = lock_path.parent
    payload = _load_lock(lock_path)
    dependencies = payload.get("dependencies", [])
    if not isinstance(dependencies, list):
        raise ValueError("workspace.lock.json dependencies must be a list")
    for dependency in dependencies:
        if isinstance(dependency, dict):
            _sync_dependency(repo_root, dependency)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
