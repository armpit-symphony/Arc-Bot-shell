"""Adapter implementations for local Arc model previews."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from arc_bot_shell.contracts import ArcActionRequest, GuardianDecision, ModelPreviewResult
from arc_bot_shell.model.prompts import build_deterministic_draft, build_prompt_summary


RETIRED_OLLAMA_MODEL_PREVIEW_DISABLED = (
    "retired direct Ollama model preview is disabled; use Arc governed preflight"
)


class LocalModelPreviewAdapter(Protocol):
    """Protocol for local model preview adapters."""

    adapter_name: str
    model_name: str

    def preview(
        self,
        task_packet: dict[str, Any],
        request: ArcActionRequest,
        guardian_decision: GuardianDecision,
    ) -> ModelPreviewResult:
        """Build a preview-safe local draft for an Arc task packet."""


@dataclass
class DeterministicPreviewAdapter:
    """Side-effect-free deterministic adapter for tests and clean clones."""

    adapter_name: str = "deterministic"
    model_name: str = "deterministic-preview-v1"

    def preview(
        self,
        task_packet: dict[str, Any],
        request: ArcActionRequest,
        guardian_decision: GuardianDecision,
    ) -> ModelPreviewResult:
        del task_packet
        prompt_summary = build_prompt_summary(request)
        draft_text = build_deterministic_draft(request, guardian_decision, prompt_summary)
        return ModelPreviewResult(
            adapter_name=self.adapter_name,
            model_name=self.model_name,
            prompt_summary=prompt_summary,
            draft_text=draft_text,
            used_network=False,
            used_credentials=False,
            status="preview_completed",
        )


@dataclass
class ModelPreviewUnavailableAdapter:
    """Controlled unavailable adapter used for unsupported preview selections."""

    adapter_name: str
    model_name: str = "unavailable"
    reason: str = "model preview adapter is unavailable"

    def preview(
        self,
        task_packet: dict[str, Any],
        request: ArcActionRequest,
        guardian_decision: GuardianDecision,
    ) -> ModelPreviewResult:
        del task_packet, guardian_decision
        return ModelPreviewResult(
            adapter_name=self.adapter_name,
            model_name=self.model_name,
            prompt_summary=build_prompt_summary(request),
            draft_text="",
            used_network=False,
            used_credentials=False,
            status="preview_unavailable",
            error_message=self.reason,
        )


@dataclass
class OllamaPreviewAdapter:
    """Retained compatibility type that always fails closed without network."""

    model_name: str = "llama3.1"
    base_url: str = "http://127.0.0.1:11434"
    timeout_seconds: float = 2.0
    adapter_name: str = "ollama"

    def _invoke_ollama(self, prompt_summary: str) -> dict[str, Any]:
        del prompt_summary
        raise RuntimeError(RETIRED_OLLAMA_MODEL_PREVIEW_DISABLED)

    def preview(
        self,
        task_packet: dict[str, Any],
        request: ArcActionRequest,
        guardian_decision: GuardianDecision,
    ) -> ModelPreviewResult:
        del task_packet, guardian_decision
        return ModelPreviewResult(
            adapter_name=self.adapter_name,
            model_name=self.model_name,
            prompt_summary=build_prompt_summary(request),
            draft_text="",
            used_network=False,
            used_credentials=False,
            status="preview_unavailable",
            error_message=RETIRED_OLLAMA_MODEL_PREVIEW_DISABLED,
        )
