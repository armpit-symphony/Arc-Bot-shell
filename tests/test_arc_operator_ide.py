"""Operator IDE projection tests over Arc's real queue contracts."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from arc_bot_shell.approvals import ApprovalRecord, JsonlApprovalStore
from arc_bot_shell.tasks import ArcOperatorIDE, JsonlTaskQueue, TaskRecord


def task(task_id: str, *, status: str = "queued") -> TaskRecord:
    return TaskRecord(
        task_id=task_id,
        action_id=f"action-{task_id}",
        task_ref=f"task:{task_id}",
        requested_action="arc.read_document",
        payload_summary="read a document",
        source="test",
        status=status,  # type: ignore[arg-type]
        created_at="2026-08-01T00:00:00Z",
        updated_at="2026-08-01T00:00:00Z",
        latest_result_status=(
            "requires_operator_approval" if status == "blocked" else None
        ),
    )


def approval(task_id: str) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=f"approval-{task_id}",
        task_id=task_id,
        run_id=f"run-{task_id}",
        action_id=f"action-{task_id}",
        task_ref=f"task:{task_id}",
        requested_action="arc.read_document",
        guardian_decision_id=f"guardian-{task_id}",
        guardian_status="requires_operator_approval",
        blocked_reason="operator review required",
        evidence_path="evidence.json",
        status="pending",
        created_at="2026-08-01T00:00:00Z",
        updated_at="2026-08-01T00:00:00Z",
    )


class ArcOperatorIDETests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.queue_path = root / "tasks.jsonl"
        self.approval_path = root / "approvals.jsonl"
        self.ide = ArcOperatorIDE(
            root,
            queue_path=self.queue_path,
            approval_path=self.approval_path,
        )

    def test_snapshot_uses_arc_selection_and_external_resolution_refs(self):
        queue = JsonlTaskQueue(self.queue_path)
        queue.append(task("waiting", status="blocked"))
        queue.append(task("fresh"))

        waiting = self.ide.snapshot()
        self.assertEqual("fresh", waiting["next_task"]["task_id"])
        resolved = self.ide.snapshot(resolved_task_refs=["task:waiting"])
        self.assertEqual("waiting", resolved["next_task"]["task_id"])
        self.assertEqual(
            "resumed_after_information_arrived", resolved["next_task"]["reason"]
        )
        self.assertNotIn("source", resolved["tasks"][0])
        self.assertNotIn("latest_evidence_path", resolved["tasks"][0])
        self.assertNotIn("latest_error_message", resolved["tasks"][0])

    def test_approval_is_human_evidence_not_execution_authority(self):
        JsonlTaskQueue(self.queue_path).append(task("waiting", status="blocked"))
        JsonlApprovalStore(self.approval_path).append(approval("waiting"))

        result = self.ide.decide(
            approval_id="approval-waiting",
            decision="approved",
            operator_id="operator-1",
            reason="Reviewed the bounded request.",
        )

        self.assertFalse(result["execution_allowed"])
        self.assertEqual("approved", result["approval"]["status"])
        self.assertNotIn("evidence_path", result["approval"])
        self.assertNotIn("source", result["task"])
        snapshot = self.ide.snapshot()
        self.assertEqual("waiting", snapshot["next_task"]["task_id"])
        self.assertEqual([], snapshot["pending_approvals"])

    def test_denied_approval_does_not_resolve_a_task(self):
        JsonlTaskQueue(self.queue_path).append(task("waiting", status="blocked"))
        JsonlApprovalStore(self.approval_path).append(approval("waiting"))
        self.ide.decide(
            approval_id="approval-waiting",
            decision="denied",
            operator_id="operator-1",
            reason="Scope is not acceptable.",
        )
        self.assertIsNone(self.ide.snapshot()["next_task"])


if __name__ == "__main__":
    unittest.main()
