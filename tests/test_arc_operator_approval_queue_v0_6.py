"""Operator approval queue tests for Arc Harness Shell v0.6."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from arc_bot_shell.approvals import JsonlApprovalStore, default_approval_path
from arc_bot_shell.health import build_health_report
from arc_bot_shell.state import JsonlStateStore
from arc_bot_shell.tasks import JsonlTaskQueue

REPO_ROOT = Path(__file__).resolve().parents[1]


def _console(*args: str, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "arc_bot_shell.console", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _queue_blocked_email(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path, str, subprocess.CompletedProcess[str]]:
    queue_path = tmp_path / "tasks" / "tasks.jsonl"
    approval_path = default_approval_path(tmp_path)
    state_path = tmp_path / "state" / "runs.jsonl"
    evidence_dir = tmp_path / "evidence"
    intake = _console(
        "--task-queue-path",
        str(queue_path),
        "intake",
        "samples/tasks/external_email_send.json",
    )
    assert intake.returncode == 0
    task_id = json.loads(intake.stdout)["task"]["task_id"]
    run = _console(
        "--task-queue-path",
        str(queue_path),
        "--approval-path",
        str(approval_path),
        "--state-path",
        str(state_path),
        "run-task",
        task_id,
        "--runtime",
        "fake",
        "--evidence-dir",
        str(evidence_dir),
    )
    return queue_path, approval_path, state_path, evidence_dir, task_id, run


def test_blocked_run_task_creates_pending_approval_record(tmp_path: Path) -> None:
    queue_path, approval_path, state_path, _, task_id, run = _queue_blocked_email(
        tmp_path
    )
    payload = json.loads(run.stdout)
    approvals = JsonlApprovalStore(approval_path).list_approvals()
    task = JsonlTaskQueue(queue_path).get_task(task_id)
    state = JsonlStateStore(state_path).list_runs()

    assert run.returncode == 2
    assert payload["run"]["runtime_called"] is False
    assert payload["run"]["model_preview_called"] is False
    assert len(approvals) == 1
    assert approvals[0].status == "pending"
    assert approvals[0].guardian_status == "blocked"
    assert approvals[0].execution_allowed is False
    assert approvals[0].execution_status == "not_executable_in_v0_6"
    assert Path(approvals[0].evidence_path).exists()
    assert task is not None
    assert task.latest_approval_id == approvals[0].approval_id
    assert task.latest_approval_status == "pending"
    assert len(state) == 1


def test_console_approvals_and_show_approval_read_real_records(tmp_path: Path) -> None:
    queue_path, approval_path, _, _, _, run = _queue_blocked_email(tmp_path)
    approval_id = JsonlApprovalStore(approval_path).list_approvals()[0].approval_id

    listing = _console(
        "--task-queue-path",
        str(queue_path),
        "--approval-path",
        str(approval_path),
        "approvals",
    )
    shown = _console(
        "--approval-path",
        str(approval_path),
        "approval",
        approval_id,
    )

    assert run.returncode == 2
    assert listing.returncode == 0
    assert shown.returncode == 0
    assert json.loads(listing.stdout)["approvals"][0]["approval_id"] == approval_id
    assert json.loads(shown.stdout)["approval"]["approval_id"] == approval_id


def test_approve_records_local_decision_without_enabling_execution(
    tmp_path: Path,
) -> None:
    queue_path, approval_path, state_path, _, task_id, _ = _queue_blocked_email(
        tmp_path
    )
    approval_id = JsonlApprovalStore(approval_path).list_approvals()[0].approval_id
    initial_run_count = len(JsonlStateStore(state_path).list_runs())

    result = _console(
        "--task-queue-path",
        str(queue_path),
        "--approval-path",
        str(approval_path),
        "approve",
        approval_id,
        "--operator-id",
        "operator-test",
        "--reason",
        "reviewed locally",
    )
    payload = json.loads(result.stdout)
    task = JsonlTaskQueue(queue_path).get_task(task_id)
    approval = JsonlApprovalStore(approval_path).get_approval(approval_id)

    assert result.returncode == 0
    assert payload["approval"]["status"] == "approved"
    assert payload["execution_allowed"] is False
    assert payload["execution_status"] == "approved_but_not_executable_in_v0_6"
    assert approval is not None
    assert approval.execution_allowed is False
    assert approval.operator_id == "operator-test"
    assert task is not None
    assert task.latest_approval_status == "approved"
    assert len(JsonlStateStore(state_path).list_runs()) == initial_run_count


def test_deny_records_local_decision_without_execution(tmp_path: Path) -> None:
    queue_path, approval_path, state_path, _, task_id, _ = _queue_blocked_email(
        tmp_path
    )
    approval_id = JsonlApprovalStore(approval_path).list_approvals()[0].approval_id
    initial_run_count = len(JsonlStateStore(state_path).list_runs())

    result = _console(
        "--task-queue-path",
        str(queue_path),
        "--approval-path",
        str(approval_path),
        "deny",
        approval_id,
        "--operator-id",
        "operator-test",
        "--reason",
        "not approved",
    )
    task = JsonlTaskQueue(queue_path).get_task(task_id)
    approval = JsonlApprovalStore(approval_path).get_approval(approval_id)

    assert result.returncode == 0
    assert approval is not None
    assert approval.status == "denied"
    assert approval.execution_allowed is False
    assert approval.execution_status == "denied_not_executable"
    assert task is not None
    assert task.latest_approval_status == "denied"
    assert len(JsonlStateStore(state_path).list_runs()) == initial_run_count


def test_requires_operator_approval_task_creates_pending_approval(
    tmp_path: Path,
) -> None:
    task_packet = tmp_path / "approval_required.json"
    task_packet.write_text(
        json.dumps(
            {
                "action_id": "arc-action-approval-required-001",
                "task_ref": "task://approval-required/001",
                "action_name": "arc.preview_operator_response",
                "summary": "Preview-only task requiring local approval",
                "preview_only": True,
                "requires_operator_approval": True,
                "requested_capabilities": [],
                "payload": {"payload_summary": "requires local approval"},
            }
        ),
        encoding="utf-8",
    )
    queue_path = tmp_path / "tasks" / "tasks.jsonl"
    approval_path = default_approval_path(tmp_path)
    state_path = tmp_path / "state" / "runs.jsonl"
    intake = _console("--task-queue-path", str(queue_path), "intake", str(task_packet))
    task_id = json.loads(intake.stdout)["task"]["task_id"]

    run = _console(
        "--task-queue-path",
        str(queue_path),
        "--approval-path",
        str(approval_path),
        "--state-path",
        str(state_path),
        "run-task",
        task_id,
        "--runtime",
        "fake",
    )
    approvals = JsonlApprovalStore(approval_path).list_approvals()

    assert run.returncode == 3
    assert approvals[0].guardian_status == "requires_operator_approval"
    assert approvals[0].status == "pending"
    assert approvals[0].execution_allowed is False


def test_completed_preview_task_does_not_create_approval_record(tmp_path: Path) -> None:
    queue_path = tmp_path / "tasks" / "tasks.jsonl"
    approval_path = default_approval_path(tmp_path)
    state_path = tmp_path / "state" / "runs.jsonl"
    evidence_dir = tmp_path / "evidence"
    intake = _console(
        "--task-queue-path",
        str(queue_path),
        "intake",
        "samples/tasks/local_model_preview.json",
    )
    task_id = json.loads(intake.stdout)["task"]["task_id"]

    run = _console(
        "--task-queue-path",
        str(queue_path),
        "--approval-path",
        str(approval_path),
        "--state-path",
        str(state_path),
        "run-task",
        task_id,
        "--runtime",
        "fake",
        "--model-adapter",
        "deterministic",
        "--evidence-dir",
        str(evidence_dir),
    )
    task = JsonlTaskQueue(queue_path).get_task(task_id)

    assert run.returncode == 0
    assert JsonlApprovalStore(approval_path).list_approvals() == []
    assert task is not None
    assert task.latest_approval_id is None
    assert task.latest_approval_status is None


def test_health_reports_approval_queue_counts(tmp_path: Path) -> None:
    _, approval_path, _, _, _, _ = _queue_blocked_email(tmp_path)
    store = JsonlApprovalStore(approval_path)
    approval_id = store.list_approvals()[0].approval_id
    result = _console(
        "--task-queue-path",
        str(tmp_path / "tasks" / "tasks.jsonl"),
        "--approval-path",
        str(approval_path),
        "approve",
        approval_id,
    )
    assert result.returncode == 0

    payload = build_health_report(repo_root=tmp_path)

    assert payload["approval_queue_present"] is True
    assert payload["pending_approval_count"] == 0
    assert payload["approved_approval_count"] == 1
    assert payload["denied_approval_count"] == 0
