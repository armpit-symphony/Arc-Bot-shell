"""Phase-2 local model readiness contracts."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_REEXPORTS: dict[str, tuple[str, str]] = {
    "DEFAULT_OLLAMA_ENDPOINT_LABEL": (".readiness", "DEFAULT_OLLAMA_ENDPOINT_LABEL"),
    "DEFAULT_QWEN_MODEL_ID": (".readiness", "DEFAULT_QWEN_MODEL_ID"),
    "OllamaQwenHardwareProfile": (".readiness", "OllamaQwenHardwareProfile"),
    "OllamaQwenReadinessInput": (".readiness", "OllamaQwenReadinessInput"),
    "OllamaQwenReadinessProjectionError": (
        ".readiness",
        "OllamaQwenReadinessProjectionError",
    ),
    "build_ollama_qwen_readiness_projection": (
        ".readiness",
        "build_ollama_qwen_readiness_projection",
    ),
    "build_ollama_qwen_readiness_from_lima_packet": (
        ".readiness",
        "build_ollama_qwen_readiness_from_lima_packet",
    ),
    "run_ollama_qwen_readiness_preview": (
        ".readiness",
        "run_ollama_qwen_readiness_preview",
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
