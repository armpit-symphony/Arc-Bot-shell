"""Approval queue operations for guarded Arc tasks."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import uuid
from typing import TYPE_CHECKING

from arc_bot_shell.contracts import HarnessRunResult

from .models import ApprovalRecord
from .store import JsonlApprovalStore

if TYPE_CHECKING:
    from arc_bot_shell.tasks.models import TaskRecord


class ApprovalQueueError(RuntimeError):
    """Raised when an approval operation cannot proceed."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def create_approval_for_guarded_task(
    task_record: TaskRecord,
    harness_result: HarnessRunResult,
    *,
    store: JsonlApprovalStore,
) -> ApprovalRecord | None:
    """Create a pending local approval for blocked/approval-required runs."""

    if harness_result.guardian_decision.status not in {
        "blocked",
        "requires_operator_approval",
    }:
        return None

    timestamp = _utc_now()
    record = ApprovalRecord(
        approval_id=f"arc-approval-{uuid.uuid4().hex[:12]}",
        task_id=task_record.task_id,
        run_id=harness_result.run_id,
        action_id=harness_result.action_id,
        task_ref=harness_result.task_ref,
        requested_action=task_record.requested_action,
        guardian_decision_id=harness_result.guardian_decision.decision_id,
        guardian_status=harness_result.guardian_decision.status,
        blocked_reason=harness_result.blocked_reason,
        evidence_path=str(harness_result.evidence_path),
        status="pending",
        created_at=timestamp,
        updated_at=timestamp,
    )
    store.append(record)
    return record


def decide_approval(
    approval_id: str,
    *,
    decision: str,
    store: JsonlApprovalStore,
    operator_id: str = "operator-local",
    reason: str | None = None,
) -> ApprovalRecord:
    if decision not in {"approved", "denied"}:
        raise ApprovalQueueError("approval decision must be 'approved' or 'denied'")

    record = store.get_approval(approval_id)
    if record is None:
        raise ApprovalQueueError(f"approval {approval_id!r} was not found")
    if record.status != "pending":
        raise ApprovalQueueError(f"approval {approval_id!r} is already {record.status}")

    timestamp = _utc_now()
    updated = replace(
        record,
        status=decision,  # type: ignore[arg-type]
        operator_id=operator_id,
        decision_reason=reason,
        decided_at=timestamp,
        updated_at=timestamp,
        execution_allowed=False,
        execution_status=(
            "approved_but_not_executable_in_v0_6"
            if decision == "approved"
            else "denied_not_executable"
        ),
    )
    store.upsert(updated)
    return updated
