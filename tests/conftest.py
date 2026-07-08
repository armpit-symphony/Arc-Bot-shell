"""Pytest bootstrap for repo-root package imports."""

from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
repo_root_text = str(REPO_ROOT)
if repo_root_text not in sys.path:
    sys.path.insert(0, repo_root_text)


def resolve_lima_checkout() -> Path | None:
    for env_name in ("LIMA_AI_OS_REPO", "ARC_LIMA_PATH"):
        configured = os.environ.get(env_name)
        if configured:
            candidate = Path(configured)
            if (candidate / "lima").exists():
                return candidate

    default_candidate = REPO_ROOT.parent / "LIMA-AI-OS"
    if (default_candidate / "lima").exists():
        return default_candidate
    return None


def require_lima_checkout_path(*relative_parts: str) -> Path:
    checkout = resolve_lima_checkout()
    if checkout is None:
        pytest.skip(
            "Legacy LIMA proof tests require an explicit LIMA checkout; skipping in clean-clone CI.",
        )

    if not relative_parts:
        return checkout

    target = checkout.joinpath(*relative_parts)
    if not target.exists():
        pytest.skip(
            f"Legacy LIMA proof tests require {target} from a LIMA checkout; skipping in clean-clone CI.",
        )
    return target


def load_lima_module_or_skip(module_name: str, *required_checkout_parts: str):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name not in {"lima", module_name} and not str(exc.name).startswith("lima."):
            raise

    checkout = require_lima_checkout_path()
    if required_checkout_parts:
        require_lima_checkout_path(*required_checkout_parts)
    checkout_text = str(checkout)
    if checkout_text not in sys.path:
        sys.path.insert(0, checkout_text)

    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        pytest.skip(
            f"Legacy LIMA proof tests require importable module {module_name!r}; skipping in clean-clone CI.",
        )