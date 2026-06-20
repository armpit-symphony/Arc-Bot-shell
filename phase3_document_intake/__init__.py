"""Phase-3 document intake contracts."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_REEXPORTS: dict[str, tuple[str, str]] = {
    "SUPPORTED_DOCUMENT_TYPES": (".intake", "SUPPORTED_DOCUMENT_TYPES"),
    "SUPPORTED_PROCESSING_MODES": (".intake", "SUPPORTED_PROCESSING_MODES"),
    "DocumentIntakeRequest": (".intake", "DocumentIntakeRequest"),
    "DocumentIntakePreviewError": (".intake", "DocumentIntakePreviewError"),
    "build_document_intake_preview": (".intake", "build_document_intake_preview"),
    "classify_document_type": (".intake", "classify_document_type"),
    "run_document_intake_preview": (".intake", "run_document_intake_preview"),
}


def __getattr__(name: str) -> Any:
    mapping = _REEXPORTS.get(name)
    if mapping is None:
        raise AttributeError(name)

    module_name, symbol_name = mapping
    symbol = getattr(import_module(module_name, package=__name__), symbol_name)
    globals()[name] = symbol
    return symbol


__all__ = list(_REEXPORTS)
