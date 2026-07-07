"""Local model preview tests for Arc Harness Shell v0.3."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from arc_bot_shell.contracts import ArcActionRequest, GuardianDecision
from arc_bot_shell.health import build_health_report
from arc_bot_shell.harness import load_task_packet, run_task_packet
from arc_bot_shell.model import DeterministicPreviewAdapter, OllamaPreviewAdapter
from arc_bot_shell.state import JsonlStateStore


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_MODEL_PREVIEW_TASK = REPO_ROOT / "samples" / "tasks" / "local_model_preview.json"


class ExplodingModelPreviewAdapter:
    adapter_name = "exploding"
    model_name = "exploding-preview"

    def preview(self, task_packet, request, guardian_decision):  # pragma: no cover - test double
        raise AssertionError("model preview adapter should not be called")


class FailingOllamaPreviewAdapter(OllamaPreviewAdapter):
    def _invoke_ollama(self, prompt_summary: str) -> dict[str, object]:
        raise OSError("no local Ollama listener")


def test_deterministic_model_preview_adapter_creates_draft_without_network_or_credentials() -> None:
    request = load_task_packet(LOCAL_MODEL_PREVIEW_TASK)
    decision = GuardianDecision(
        decision_id=f"guardian-decision:{request.action_id}",
        action_id=request.action_id,
        status="allowed_preview_only",
        evaluator="test",
        reason="preview-only test request",
    )

    result = DeterministicPreviewAdapter().preview(request.payload, request, decision)

    assert result.status == "preview_completed"
    assert result.used_network is False
    assert result.used_credentials is False
    assert "No external action was taken" in result.draft_text
    assert request.task_ref in result.prompt_summary


def test_local_model_preview_action_passes_guardian_and_calls_preview_adapter(tmp_path: Path) -> None:
    result = run_task_packet(
        LOCAL_MODEL_PREVIEW_TASK,
        runtime_name="fake",
        model_adapter_name="deterministic",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state" / "runs.jsonl",
    )

    assert result.exit_code == 0
    assert result.result_status == "preview_completed"
    assert result.runtime_called is False
    assert result.model_preview_called is True
    assert result.model_preview is not None
    assert result.model_preview["adapter_name"] == "deterministic"


def test_blocked_external_action_does_not_call_model_adapter(tmp_path: Path) -> None:
    blocked_task = tmp_path / "blocked_local_model_preview.json"
    blocked_task.write_text(
        json.dumps(
            {
                "action_id": "arc-action-local-model-preview-blocked-001",
                "task_ref": "task://tests/local-model-preview-blocked",
                "action_name": "arc.local_model_preview",
                "summary": "Draft a blocked external send response.",
                "preview_only": True,
                "requested_capabilities": ["external_send"],
                "payload": {"task_packet": {"title": "Blocked send"}},
            }
        ),
        encoding="utf-8",
    )

    result = run_task_packet(
        blocked_task,
        runtime_name="fake",
        model_adapter_name="deterministic",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state" / "runs.jsonl",
        model_preview_adapter=ExplodingModelPreviewAdapter(),
    )

    assert result.exit_code == 2
    assert result.result_status == "blocked"
    assert result.model_preview_called is False
    assert result.runtime_called is False


def test_model_preview_evidence_includes_adapter_metadata(tmp_path: Path) -> None:
    result = run_task_packet(
        LOCAL_MODEL_PREVIEW_TASK,
        runtime_name="fake",
        model_adapter_name="deterministic",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state" / "runs.jsonl",
    )

    payload = json.loads(result.evidence_path.read_text(encoding="utf-8"))

    assert payload["model_preview"]["adapter_name"] == "deterministic"
    assert payload["model_preview"]["model_name"] == "deterministic-preview-v1"
    assert payload["model_preview"]["status"] == "preview_completed"
    assert payload["model_preview"]["used_network"] is False
    assert payload["model_preview"]["used_credentials"] is False
    assert payload["model_preview"]["draft_text"]


def test_state_record_is_appended_for_model_preview_run(tmp_path: Path) -> None:
    state_path = tmp_path / "state" / "runs.jsonl"
    result = run_task_packet(
        LOCAL_MODEL_PREVIEW_TASK,
        runtime_name="fake",
        model_adapter_name="deterministic",
        evidence_dir=tmp_path / "evidence",
        state_path=state_path,
    )

    records = JsonlStateStore(state_path).list_runs()

    assert records[0].run_id == result.run_id
    assert records[0].requested_action == "arc.local_model_preview"
    assert records[0].model_preview_called is True
    assert records[0].model_preview_adapter == "deterministic"
    assert records[0].model_name == "deterministic-preview-v1"


def test_console_history_and_show_run_can_read_model_preview_run(tmp_path: Path) -> None:
    state_path = tmp_path / "state" / "runs.jsonl"
    result = run_task_packet(
        LOCAL_MODEL_PREVIEW_TASK,
        runtime_name="fake",
        model_adapter_name="deterministic",
        evidence_dir=tmp_path / "evidence",
        state_path=state_path,
    )

    history = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.console",
            "--state-path",
            str(state_path),
            "history",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    show_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.console",
            "--state-path",
            str(state_path),
            "show-run",
            result.run_id,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    history_payload = json.loads(history.stdout)
    show_run_payload = json.loads(show_run.stdout)

    assert history_payload["runs"][0]["requested_action"] == "arc.local_model_preview"
    assert history_payload["runs"][0]["model_preview_called"] is True
    assert show_run_payload["model_preview"]["adapter_name"] == "deterministic"
    assert show_run_payload["model_preview"]["status"] == "preview_completed"


def test_health_reports_deterministic_model_adapter_availability() -> None:
    payload = build_health_report(repo_root=REPO_ROOT)

    assert payload["model_preview_available"] is True
    assert payload["deterministic_model_adapter_available"] is True
    assert "ollama_configured" in payload
    assert payload["samples"]["local_model_preview"] is True


def test_ollama_adapter_unavailable_path_is_controlled() -> None:
    request = ArcActionRequest.from_dict(json.loads(LOCAL_MODEL_PREVIEW_TASK.read_text(encoding="utf-8")))
    decision = GuardianDecision(
        decision_id=f"guardian-decision:{request.action_id}",
        action_id=request.action_id,
        status="allowed_preview_only",
        evaluator="test",
        reason="preview-only test request",
    )

    result = FailingOllamaPreviewAdapter().preview(request.payload, request, decision)

    assert result.status == "preview_unavailable"
    assert result.used_network is True
    assert result.used_credentials is False
    assert result.error_message == "no local Ollama listener"
