"""Adapter selection and health helpers for local Arc model previews."""

from __future__ import annotations

import os

from arc_bot_shell.model.adapters import (
    DeterministicPreviewAdapter,
    LocalModelPreviewAdapter,
    ModelPreviewUnavailableAdapter,
    OllamaPreviewAdapter,
)

DEFAULT_MODEL_ADAPTER = "deterministic"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"


def resolve_model_adapter_name(model_adapter_name: str | None) -> str:
    return model_adapter_name or os.environ.get("ARC_MODEL_ADAPTER", DEFAULT_MODEL_ADAPTER)


def build_model_preview_adapter(
    model_adapter_name: str | None = None,
    *,
    model_name: str | None = None,
) -> LocalModelPreviewAdapter:
    resolved = resolve_model_adapter_name(model_adapter_name)
    if resolved == "deterministic":
        return DeterministicPreviewAdapter(model_name=model_name or "deterministic-preview-v1")
    if resolved == "ollama":
        return OllamaPreviewAdapter(
            model_name=model_name or os.environ.get("ARC_MODEL_NAME", "llama3.1"),
            base_url=os.environ.get("ARC_OLLAMA_URL", DEFAULT_OLLAMA_URL),
        )
    return ModelPreviewUnavailableAdapter(
        adapter_name=resolved,
        reason=f"unsupported model preview adapter {resolved!r}",
    )


def model_preview_available() -> bool:
    return True


def deterministic_model_adapter_available() -> bool:
    return True


def ollama_configured() -> bool:
    return resolve_model_adapter_name(None) == "ollama" or bool(os.environ.get("ARC_OLLAMA_URL"))
