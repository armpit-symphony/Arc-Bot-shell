"""Adapter implementations for local Arc model previews."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Protocol
from urllib import error, request as urllib_request

from arc_bot_shell.contracts import ArcActionRequest, GuardianDecision, ModelPreviewResult
from arc_bot_shell.model.prompts import build_deterministic_draft, build_prompt_summary


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
    """Optional Ollama-backed preview adapter behind explicit opt-in config."""

    model_name: str = "llama3.1"
    base_url: str = "http://127.0.0.1:11434"
    timeout_seconds: float = 2.0
    adapter_name: str = "ollama"

    def _invoke_ollama(self, prompt_summary: str) -> dict[str, Any]:
        payload = {
            "model": self.model_name,
            "prompt": prompt_summary,
            "stream": False,
        }
        request = urllib_request.Request(
            url=f"{self.base_url.rstrip('/')}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib_request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def preview(
        self,
        task_packet: dict[str, Any],
        request: ArcActionRequest,
        guardian_decision: GuardianDecision,
    ) -> ModelPreviewResult:
        del task_packet, guardian_decision
        prompt_summary = build_prompt_summary(request)
        try:
            payload = self._invoke_ollama(prompt_summary)
        except (OSError, ValueError, error.URLError) as exc:
            return ModelPreviewResult(
                adapter_name=self.adapter_name,
                model_name=self.model_name,
                prompt_summary=prompt_summary,
                draft_text="",
                used_network=True,
                used_credentials=False,
                status="preview_unavailable",
                error_message=str(exc),
            )
        draft_text = str(payload.get("response", "")).strip()
        if not draft_text:
            return ModelPreviewResult(
                adapter_name=self.adapter_name,
                model_name=self.model_name,
                prompt_summary=prompt_summary,
                draft_text="",
                used_network=True,
                used_credentials=False,
                status="preview_unavailable",
                error_message="ollama preview returned an empty response",
            )
        return ModelPreviewResult(
            adapter_name=self.adapter_name,
            model_name=self.model_name,
            prompt_summary=prompt_summary,
            draft_text=draft_text,
            used_network=True,
            used_credentials=False,
            status="preview_completed",
        )
