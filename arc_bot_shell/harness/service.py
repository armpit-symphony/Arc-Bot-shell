"""End-to-end Arc Harness Shell orchestration."""

from __future__ import annotations

import json
import os
from pathlib import Path
import uuid

from arc_bot_shell.console import render_json
from arc_bot_shell.contracts import ArcActionRequest, HarnessRunResult
from arc_bot_shell.evidence import (
    build_evidence_bundle,
    default_evidence_dir,
    write_evidence_bundle,
)
from arc_bot_shell.guardian import (
    DEFAULT_GUARDIAN_CONTRACT_REFERENCE,
    DEFAULT_OLLAMA_URL,
    GuardianFacade,
    build_guardian_facade,
    build_guardian_policy_context,
)
from arc_bot_shell.lima import (
    LimaRuntimePort,
    LimaRuntimeUnavailableError,
    build_runtime_port,
)
from arc_bot_shell.model import (
    LocalModelPreviewAdapter,
    build_model_preview_adapter,
    resolve_model_adapter_name,
)
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
    guardian_mode: str | None = None,
    guardian_path: Path | None = None,
    guardian_contract_reference: str | None = None,
    ollama_url: str | None = None,
    stop_after_guardian: bool = False,
) -> HarnessRunResult:
    root = repo_root or Path(__file__).resolve().parents[2]
    request = load_task_packet(task_path)
    resolved_guardian_mode = guardian_mode or os.environ.get(
        "ARC_GUARDIAN_MODE", "fail_closed"
    )
    configured_guardian_path = guardian_path
    if configured_guardian_path is None:
        path_text = os.environ.get("ARC_GUARDIAN_PATH", "").strip()
        configured_guardian_path = None if not path_text else Path(path_text)
    resolved_reference = guardian_contract_reference or os.environ.get(
        "ARC_GUARDIAN_REFERENCE",
        DEFAULT_GUARDIAN_CONTRACT_REFERENCE,
    )
    resolved_ollama_url = ollama_url or os.environ.get(
        "ARC_OLLAMA_URL", DEFAULT_OLLAMA_URL
    )
    guardian = guardian_facade or build_guardian_facade(
        resolved_guardian_mode,
        guardian_path=configured_guardian_path,
        ollama_url=resolved_ollama_url,
        contract_reference=resolved_reference,
    )
    decision = guardian.evaluate(
        request,
        policy_context=build_guardian_policy_context(request),
    )
    run_id = f"arc-run-{uuid.uuid4().hex[:12]}"

    is_model_preview = request.action_name == "arc.local_model_preview"
    selected_model_adapter_name = (
        resolve_model_adapter_name(model_adapter_name) if is_model_preview else None
    )

    runtime_called = False
    model_preview_called = False
    eligible_for_lima = False
    ollama_called = False
    runtime_output: dict[str, object] = {}
    model_preview_result = None
    blocked_reason = None
    exit_code = 0
    runtime_adapter = selected_model_adapter_name or runtime_name
    result_status = "preview_completed"
    guardian_only = stop_after_guardian or decision.evaluator == "guardian_core"

    if decision.status == "allowed_preview_only":
        if guardian_only:
            eligible_for_lima = True
            runtime_adapter = "guardian_only"
            result_status = "guardian_approved_for_lima"
        elif is_model_preview:
            resolved_model_adapter = (
                model_preview_adapter
                or build_model_preview_adapter(
                    selected_model_adapter_name,
                    model_name=model_name,
                )
            )
            model_preview_result = resolved_model_adapter.preview(
                request.payload,
                request,
                decision,
            )
            model_preview_called = True
            ollama_called = model_preview_result.adapter_name == "ollama"
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
        lima_called=runtime_called,
        ollama_called=ollama_called,
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
        guardian_status=str(decision.metadata.get("guardian_status", decision.status)),
        blocked_reason=blocked_reason,
        runtime_adapter=runtime_adapter,
        runtime_called=runtime_called,
        result_status=result_status,
        evidence_path=str(evidence_path),
        created_at=bundle.created_at,
        model_preview_called=model_preview_called,
        model_preview_adapter=(
            None if model_preview_result is None else model_preview_result.adapter_name
        ),
        model_name=(
            None if model_preview_result is None else model_preview_result.model_name
        ),
        guardian_mode=decision.evaluator,
        guardian_reason=decision.reason,
        guardian_allowed=decision.allowed,
        guardian_requires_approval=decision.requires_approval,
        guardian_contract_reference=decision.metadata.get(
            "guardian_contract_reference"
        ),
        eligible_for_lima=eligible_for_lima,
        lima_called=runtime_called,
        ollama_called=ollama_called,
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
        model_preview=(
            None if model_preview_result is None else model_preview_result.to_dict()
        ),
        runtime_output=runtime_output,
        guardian_mode=decision.evaluator,
        guardian_status=str(decision.metadata.get("guardian_status", decision.status)),
        guardian_decision_id=decision.decision_id,
        eligible_for_lima=eligible_for_lima,
        lima_called=runtime_called,
        ollama_called=ollama_called,
    )


def render_run_result(result: HarnessRunResult, compact: bool = False) -> str:
    return render_json(result.to_dict(), compact=compact)
