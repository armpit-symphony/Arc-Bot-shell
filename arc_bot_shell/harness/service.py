"""End-to-end Arc Harness Shell orchestration."""

from __future__ import annotations

import json
from pathlib import Path
import uuid

from arc_bot_shell.console import render_json
from arc_bot_shell.contracts import ArcActionRequest, HarnessRunResult
from arc_bot_shell.evidence import build_evidence_bundle, default_evidence_dir, write_evidence_bundle
from arc_bot_shell.guardian import GuardianFacade
from arc_bot_shell.lima import LimaRuntimePort, LimaRuntimeUnavailableError, build_runtime_port
from arc_bot_shell.model import LocalModelPreviewAdapter, build_model_preview_adapter, resolve_model_adapter_name
from arc_bot_shell.state import JsonlStateStore, StateRunRecord, default_state_path


def load_task_packet(task_path: Path) -> ArcActionRequest:
    payload = json.loads(task_path.read_text(encoding="utf-8"))
    return ArcActionRequest.from_dict(payload)


def run_task_packet(
    task_path: Path,
    *,
    runtime_name: str,
    model_adapter_name: str | None = None,
    model_name: str | None = None,
    evidence_dir: Path | None = None,
    state_path: Path | None = None,
    repo_root: Path | None = None,
    guardian_facade: GuardianFacade | None = None,
    runtime_port: LimaRuntimePort | None = None,
    model_preview_adapter: LocalModelPreviewAdapter | None = None,
) -> HarnessRunResult:
    root = repo_root or Path(__file__).resolve().parents[2]
    request = load_task_packet(task_path)
    guardian = guardian_facade or GuardianFacade()
    decision = guardian.evaluate(request)
    run_id = f"arc-run-{uuid.uuid4().hex[:12]}"

    is_model_preview = request.action_name == "arc.local_model_preview"
    selected_model_adapter_name = (
        resolve_model_adapter_name(model_adapter_name) if is_model_preview else None
    )

    runtime_called = False
    model_preview_called = False
    runtime_output: dict[str, object] = {}
    model_preview_result = None
    blocked_reason = None
    exit_code = 0
    runtime_adapter = selected_model_adapter_name or runtime_name
    result_status = "preview_completed"

    if decision.status == "allowed_preview_only":
        if is_model_preview:
            resolved_model_adapter = model_preview_adapter or build_model_preview_adapter(
                selected_model_adapter_name,
                model_name=model_name,
            )
            model_preview_result = resolved_model_adapter.preview(
                request.payload,
                request,
                decision,
            )
            model_preview_called = True
            runtime_adapter = model_preview_result.adapter_name
            result_status = model_preview_result.status
            if result_status != "preview_completed":
                blocked_reason = model_preview_result.error_message
                exit_code = 4
        else:
            resolved_runtime = runtime_port or build_runtime_port(runtime_name, root)
            runtime_adapter = resolved_runtime.adapter_name
            try:
                runtime_result = resolved_runtime.invoke(request, decision)
            except LimaRuntimeUnavailableError as exc:
                blocked_reason = str(exc)
                runtime_adapter = resolved_runtime.adapter_name
                result_status = "runtime_unavailable"
                exit_code = 4
            else:
                runtime_called = True
                runtime_adapter = runtime_result.runtime_adapter
                runtime_output = runtime_result.output
                result_status = runtime_result.result_status
    elif decision.status == "requires_operator_approval":
        blocked_reason = decision.reason
        result_status = "requires_operator_approval"
        exit_code = 3
    else:
        blocked_reason = decision.reason
        result_status = "blocked"
        exit_code = 2

    bundle = build_evidence_bundle(
        run_id=run_id,
        action_id=request.action_id,
        task_ref=request.task_ref,
        guardian_decision=decision,
        runtime_adapter=runtime_adapter,
        result_status=result_status,
        blocked_reason=blocked_reason,
        model_preview=model_preview_result,
    )
    evidence_path = write_evidence_bundle(
        bundle,
        evidence_dir or default_evidence_dir(root),
    )

    state_record = StateRunRecord(
        run_id=run_id,
        action_id=request.action_id,
        task_ref=request.task_ref,
        requested_action=request.action_name,
        guardian_decision_id=decision.decision_id,
        guardian_status=decision.status,
        blocked_reason=blocked_reason,
        runtime_adapter=runtime_adapter,
        runtime_called=runtime_called,
        result_status=result_status,
        evidence_path=str(evidence_path),
        created_at=bundle.created_at,
        model_preview_called=model_preview_called,
        model_preview_adapter=(None if model_preview_result is None else model_preview_result.adapter_name),
        model_name=(None if model_preview_result is None else model_preview_result.model_name),
    )
    JsonlStateStore(state_path or default_state_path(root)).append(state_record)

    return HarnessRunResult(
        run_id=run_id,
        action_id=request.action_id,
        task_ref=request.task_ref,
        guardian_decision=decision,
        runtime_adapter=runtime_adapter,
        runtime_called=runtime_called,
        result_status=result_status,
        blocked_reason=blocked_reason,
        evidence_path=evidence_path,
        exit_code=exit_code,
        model_preview_called=model_preview_called,
        model_preview=(None if model_preview_result is None else model_preview_result.to_dict()),
        runtime_output=runtime_output,
    )


def render_run_result(result: HarnessRunResult, compact: bool = False) -> str:
    return render_json(result.to_dict(), compact=compact)
