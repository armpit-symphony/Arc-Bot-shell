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


_inserted_checkout_paths: set[str] = set()


def _insert_checkout_path(checkout: Path) -> None:
    """Expose a LIMA source checkout, recording it so it can be withdrawn."""

    checkout_text = str(checkout)
    if checkout_text not in sys.path:
        sys.path.insert(0, checkout_text)
        _inserted_checkout_paths.add(checkout_text)


def _purge_lima_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "lima" or module_name.startswith("lima."):
            del sys.modules[module_name]


@pytest.fixture(autouse=True)
def _isolate_lima_checkout_imports():
    """Keep a legacy LIMA source checkout from shadowing the pinned install.

    The legacy proof tests need modules such as ``lima.harness`` that the
    supported v0.1 governed-kernel distribution deliberately does not ship, so
    they fall back to a sibling source checkout. Leaving that checkout on
    ``sys.path`` afterwards makes every later test resolve the whole ``lima``
    package from the checkout instead of the pinned installed wheel, which
    silently bypasses the consumer pin and re-exposes the retired
    ``lima.harness`` execution surface. Withdraw the checkout once the test
    that needed it is done.
    """

    yield
    if not _inserted_checkout_paths:
        return
    for checkout_text in list(_inserted_checkout_paths):
        while checkout_text in sys.path:
            sys.path.remove(checkout_text)
        _inserted_checkout_paths.discard(checkout_text)
    _purge_lima_modules()


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
    _insert_checkout_path(checkout)
    # ``lima`` is normally already bound to the pinned install, whose __path__
    # has no ``harness``/``adapters`` submodule. Drop the binding so the
    # checkout can supply the whole package for this test; the autouse
    # fixture drops it again afterwards so the pinned install is restored.
    _purge_lima_modules()

    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        pytest.skip(
            f"Legacy LIMA proof tests require importable module {module_name!r}; skipping in clean-clone CI.",
        )