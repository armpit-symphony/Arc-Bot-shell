"""Task intake and queue-driven execution for Arc Harness Shell."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

from arc_bot_shell.approvals import (
    JsonlApprovalStore,
    create_approval_for_guarded_task,
    default_approval_path,
)
from arc_bot_shell.contracts import ArcActionRequest, ArcActionRequestError, HarnessRunResult

from .models import TaskRecord
from .queue import JsonlTaskQueue, default_task_queue_path


class TaskQueueError(RuntimeError):
    """Raised when a queued task operation cannot proceed."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_task_request(task_path: Path) -> ArcActionRequest:
    payload = json.loads(task_path.read_text(encoding="utf-8"))
    return ArcActionRequest.from_dict(payload)


def _payload_summary(request: ArcActionRequest) -> str:
    summary = request.payload.get("payload_summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
    task_packet = request.payload.get("task_packet")
    if isinstance(task_packet, dict):
        notes = task_packet.get("notes")
        if isinstance(notes, str) and notes.strip():
            return notes.strip()
    return request.summary


def intake_task(task_path: Path, *, queue_path: Path | None = None) -> TaskRecord:
    resolved_path = task_path.resolve()
    request = _load_task_request(resolved_path)
    timestamp = _utc_now()
    record = TaskRecord(
        task_id=f"arc-task-{uuid.uuid4().hex[:12]}",
        action_id=request.action_id,
        task_ref=request.task_ref,
        requested_action=request.action_name,
        payload_summary=_payload_summary(request),
        source=str(resolved_path),
        status="queued",
        created_at=timestamp,
        updated_at=timestamp,
    )
    JsonlTaskQueue(queue_path or default_task_queue_path(resolved_path.parents[2])).append(record)
    return record


def _map_harness_status(result_status: str) -> str:
    if result_status == "preview_completed":
        return "completed"
    if result_status in {"blocked", "requires_operator_approval"}:
        return "blocked"
    return "failed"


def run_queued_task(
    task_id: str,
    *,
    queue_path: Path,
    runtime_name: str,
    model_adapter_name: str | None = None,
    model_name: str | None = None,
    evidence_dir: Path | None = None,
    state_path: Path | None = None,
    approval_path: Path | None = None,
    repo_root: Path | None = None,
) -> tuple[TaskRecord, HarnessRunResult | None, int]:
    from arc_bot_shell.harness.service import run_task_packet

    store = JsonlTaskQueue(queue_path)
    record = store.get_task(task_id)
    if record is None:
        raise TaskQueueError(f"task {task_id!r} was not found")

    running_record = replace(
        record,
        status="running",
        updated_at=_utc_now(),
        latest_error_message=None,
    )
    store.upsert(running_record)

    try:
        source_path = Path(running_record.source)
        if not source_path.exists():
            raise FileNotFoundError(f"task packet not found: {source_path}")
        harness_result = run_task_packet(
            source_path,
            runtime_name=runtime_name,
            model_adapter_name=model_adapter_name,
            model_name=model_name,
            evidence_dir=evidence_dir,
            state_path=state_path,
            repo_root=repo_root,
        )
    except (FileNotFoundError, ArcActionRequestError, json.JSONDecodeError, ValueError, OSError) as exc:
        failed_record = replace(
            running_record,
            status="failed",
            updated_at=_utc_now(),
            latest_result_status="failed",
            latest_error_message=str(exc),
        )
        store.upsert(failed_record)
        return failed_record, None, 1
    except Exception as exc:  # pragma: no cover - defensive queue guard
        failed_record = replace(
            running_record,
            status="failed",
            updated_at=_utc_now(),
            latest_result_status="failed",
            latest_error_message=f"unexpected queue run failure: {exc}",
        )
        store.upsert(failed_record)
        return failed_record, None, 1

    approval_store = JsonlApprovalStore(
        approval_path or default_approval_path(repo_root or Path(__file__).resolve().parents[2])
    )
    approval_record = create_approval_for_guarded_task(
        running_record,
        harness_result,
        store=approval_store,
    )

    final_record = replace(
        running_record,
        status=_map_harness_status(harness_result.result_status),  # type: ignore[arg-type]
        updated_at=_utc_now(),
        latest_run_id=harness_result.run_id,
        latest_guardian_status=harness_result.guardian_decision.status,
        latest_result_status=harness_result.result_status,
        latest_evidence_path=str(harness_result.evidence_path),
        latest_error_message=(
            harness_result.blocked_reason
            if harness_result.result_status not in {"preview_completed", "blocked"}
            else None
        ),
        latest_approval_id=None if approval_record is None else approval_record.approval_id,
        latest_approval_status=None if approval_record is None else approval_record.status,
    )
    store.upsert(final_record)
    return final_record, harness_result, harness_result.exit_code
