"""Arc-owned task and approval projection for operator IDE consumers.

The queue files and selection policy stay in Arc. A UI consumer receives a
sanitized projection and may record an explicit human approval decision, but
an approval remains evidence-only and never becomes execution authority.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from threading import RLock
from typing import Any, Collection

from arc_bot_shell.approvals import (
    JsonlApprovalStore,
    decide_approval,
    default_approval_path,
)

from .queue import JsonlTaskQueue, default_task_queue_path
from .selection import queue_standing, select_next_task, selectable_tasks


class ArcOperatorIDE:
    """One serialization boundary over Arc's existing local queue stores."""

    def __init__(
        self,
        repo_root: Path,
        *,
        queue_path: Path | None = None,
        approval_path: Path | None = None,
    ) -> None:
        self.queue = JsonlTaskQueue(queue_path or default_task_queue_path(repo_root))
        self.approvals = JsonlApprovalStore(
            approval_path or default_approval_path(repo_root)
        )
        self._lock = RLock()

    @staticmethod
    def _resolved_ids(tasks: list[Any], refs: Collection[str]) -> set[str]:
        supplied = {str(value) for value in refs}
        return {
            task.task_id
            for task in tasks
            if task.latest_approval_status == "approved"
            or task.task_id in supplied
            or task.task_ref in supplied
        }

    def snapshot(self, *, resolved_task_refs: Collection[str] = ()) -> dict[str, Any]:
        """Return queue standing, next selection, and pending approvals."""

        with self._lock:
            tasks = self.queue.list_tasks()
            resolved = self._resolved_ids(tasks, resolved_task_refs)
            selection = select_next_task(tasks, resolved_task_ids=resolved)
            selectable_ids = {task.task_id for task in selectable_tasks(tasks)}
            approvals = self.approvals.list_approvals(status="pending", limit=50)
            return {
                "record_type": "arc_operator_ide_snapshot",
                "queue_standing": queue_standing(
                    tasks, resolved_task_ids=resolved
                ),
                "next_task": None if selection is None else selection.to_dict(),
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "action_id": task.action_id,
                        "task_ref": task.task_ref,
                        "requested_action": task.requested_action,
                        "payload_summary": task.payload_summary,
                        "status": task.status,
                        "created_at": task.created_at,
                        "updated_at": task.updated_at,
                        "latest_guardian_status": task.latest_guardian_status,
                        "latest_result_status": task.latest_result_status,
                        "latest_approval_id": task.latest_approval_id,
                        "latest_approval_status": task.latest_approval_status,
                        "resolved": task.task_id in resolved,
                        "selectable": task.task_id in selectable_ids,
                    }
                    for task in tasks[:100]
                ],
                "pending_approvals": [
                    {
                        "approval_id": approval.approval_id,
                        "task_id": approval.task_id,
                        "task_ref": approval.task_ref,
                        "requested_action": approval.requested_action,
                        "guardian_status": approval.guardian_status,
                        "blocked_reason": approval.blocked_reason,
                        "created_at": approval.created_at,
                        "execution_allowed": False,
                    }
                    for approval in approvals
                ],
                "authority": {
                    "queue": "arc_jsonl_task_queue",
                    "selection": "arc_task_selection",
                    "approval_execution_allowed": False,
                },
            }

    def decide(
        self,
        *,
        approval_id: str,
        decision: str,
        operator_id: str,
        reason: str,
    ) -> dict[str, Any]:
        """Record a human decision and synchronize its task projection."""

        with self._lock:
            approval = decide_approval(
                approval_id,
                decision=decision,
                store=self.approvals,
                operator_id=operator_id,
                reason=reason,
            )
            task = self.queue.get_task(approval.task_id)
            rendered_task: dict[str, Any] | None = None
            if task is not None:
                task = replace(
                    task,
                    latest_approval_id=approval.approval_id,
                    latest_approval_status=approval.status,
                )
                self.queue.upsert(task)
                rendered_task = {
                    "task_id": task.task_id,
                    "task_ref": task.task_ref,
                    "status": task.status,
                    "latest_approval_id": task.latest_approval_id,
                    "latest_approval_status": task.latest_approval_status,
                }
            return {
                "approval": {
                    "approval_id": approval.approval_id,
                    "task_id": approval.task_id,
                    "task_ref": approval.task_ref,
                    "status": approval.status,
                    "operator_id": approval.operator_id,
                    "decision_reason": approval.decision_reason,
                    "decided_at": approval.decided_at,
                    "execution_allowed": approval.execution_allowed,
                    "execution_status": approval.execution_status,
                },
                "task": rendered_task,
                "execution_allowed": False,
                "execution_status": approval.execution_status,
            }
