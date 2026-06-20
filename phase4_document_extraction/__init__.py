"""Phase-4 document extraction preview contracts."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_REEXPORTS: dict[str, tuple[str, str]] = {
    "BlockedLocalModelPreviewProvider": (
        ".extraction",
        "BlockedLocalModelPreviewProvider",
    ),
    "DocumentExtractionPreviewError": (
        ".extraction",
        "DocumentExtractionPreviewError",
    ),
    "DocumentExtractionRequest": (".extraction", "DocumentExtractionRequest"),
    "LocalModelPreviewProvider": (".extraction", "LocalModelPreviewProvider"),
    "build_document_extraction_preview": (
        ".extraction",
        "build_document_extraction_preview",
    ),
    "run_document_extraction_preview": (
        ".extraction",
        "run_document_extraction_preview",
    ),
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
