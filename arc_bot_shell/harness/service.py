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


def load_task_packet(task_path: Path) -> ArcActionRequest:
    payload = json.loads(task_path.read_text(encoding="utf-8"))
    return ArcActionRequest.from_dict(payload)


def run_task_packet(
    task_path: Path,
    *,
    runtime_name: str,
    evidence_dir: Path | None = None,
    repo_root: Path | None = None,
    guardian_facade: GuardianFacade | None = None,
    runtime_port: LimaRuntimePort | None = None,
) -> HarnessRunResult:
    root = repo_root or Path(__file__).resolve().parents[2]
    request = load_task_packet(task_path)
    guardian = guardian_facade or GuardianFacade()
    decision = guardian.evaluate(request)
    run_id = f"arc-run-{uuid.uuid4().hex[:12]}"

    runtime_called = False
    runtime_output: dict[str, object] = {}
    blocked_reason = None
    exit_code = 0
    resolved_runtime = runtime_port or build_runtime_port(runtime_name, root)
    runtime_adapter = resolved_runtime.adapter_name
    result_status = "preview_completed"

    if decision.status == "allowed_preview_only":
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
    )
    evidence_path = write_evidence_bundle(
        bundle,
        evidence_dir or default_evidence_dir(root),
    )

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
        runtime_output=runtime_output,
    )


def render_run_result(result: HarnessRunResult, compact: bool = False) -> str:
    return render_json(result.to_dict(), compact=compact)
