"""Task queue tests for Arc Harness Shell v0.4."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from arc_bot_shell.console.commands import build_evidence_payload, build_history_payload
from arc_bot_shell.health import build_health_report
from arc_bot_shell.tasks import JsonlTaskQueue, TaskRecord, default_task_queue_path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _console(*args: str, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "arc_bot_shell.console", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _intake_local_preview(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    queue_path = tmp_path / "tasks" / "tasks.jsonl"
    result = _console(
        "--task-queue-path",
        str(queue_path),
        "intake",
        "samples/tasks/local_model_preview.json",
    )
    assert result.returncode == 0
    return queue_path, json.loads(result.stdout)


def test_intake_creates_queued_task_record(tmp_path: Path) -> None:
    queue_path, payload = _intake_local_preview(tmp_path)

    record = JsonlTaskQueue(queue_path).list_tasks()[0]
    assert payload["task"]["status"] == "queued"
    assert record.requested_action == "arc.local_model_preview"
    assert record.status == "queued"


def test_tasks_command_lists_queued_task(tmp_path: Path) -> None:
    queue_path, intake_payload = _intake_local_preview(tmp_path)

    result = _console("--task-queue-path", str(queue_path), "tasks")
    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["tasks"][0]["task_id"] == intake_payload["task"]["task_id"]
    assert payload["tasks"][0]["status"] == "queued"


def test_task_command_shows_one_task(tmp_path: Path) -> None:
    queue_path, intake_payload = _intake_local_preview(tmp_path)
    task_id = intake_payload["task"]["task_id"]

    result = _console("--task-queue-path", str(queue_path), "task", task_id)
    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["task"]["task_id"] == task_id
    assert payload["task"]["requested_action"] == "arc.local_model_preview"


def test_run_task_local_model_preview_completes_and_writes_run_state_and_evidence(tmp_path: Path) -> None:
    queue_path, intake_payload = _intake_local_preview(tmp_path)
    state_path = tmp_path / "state" / "runs.jsonl"
    evidence_dir = tmp_path / "evidence"

    result = _console(
        "--task-queue-path",
        str(queue_path),
        "--state-path",
        str(state_path),
        "run-task",
        intake_payload["task"]["task_id"],
        "--runtime",
        "fake",
        "--model-adapter",
        "deterministic",
        "--evidence-dir",
        str(evidence_dir),
    )
    payload = json.loads(result.stdout)
    task_record = JsonlTaskQueue(queue_path).get_task(intake_payload["task"]["task_id"])

    assert result.returncode == 0
    assert task_record is not None
    assert task_record.status == "completed"
    assert task_record.latest_run_id == payload["run"]["run_id"]
    assert Path(task_record.latest_evidence_path).exists()
    assert state_path.exists()


def test_run_task_external_email_send_blocks_without_runtime_or_model_adapter(tmp_path: Path) -> None:
    queue_path = tmp_path / "tasks" / "tasks.jsonl"
    intake = _console(
        "--task-queue-path",
        str(queue_path),
        "intake",
        "samples/tasks/external_email_send.json",
    )
    task_id = json.loads(intake.stdout)["task"]["task_id"]

    result = _console(
        "--task-queue-path",
        str(queue_path),
        "run-task",
        task_id,
        "--runtime",
        "fake",
    )
    payload = json.loads(result.stdout)
    task_record = JsonlTaskQueue(queue_path).get_task(task_id)

    assert result.returncode == 2
    assert task_record is not None
    assert task_record.status == "blocked"
    assert payload["run"]["runtime_called"] is False
    assert payload["run"]["model_preview_called"] is False


def test_failed_task_path_is_controlled_if_task_packet_is_missing(tmp_path: Path) -> None:
    queue_path, intake_payload = _intake_local_preview(tmp_path)
    task_id = intake_payload["task"]["task_id"]
    queue = JsonlTaskQueue(queue_path)
    existing = queue.get_task(task_id)
    assert existing is not None
    queue.upsert(
        TaskRecord(
            task_id=existing.task_id,
            action_id=existing.action_id,
            task_ref=existing.task_ref,
            requested_action=existing.requested_action,
            payload_summary=existing.payload_summary,
            source=str(tmp_path / "missing-task-packet.json"),
            status=existing.status,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
    )

    result = _console("--task-queue-path", str(queue_path), "run-task", task_id, "--runtime", "fake")
    payload = json.loads(result.stdout)
    failed = queue.get_task(task_id)

    assert result.returncode == 1
    assert failed is not None
    assert failed.status == "failed"
    assert failed.latest_result_status == "failed"
    assert "task packet not found" in payload["error"]


def test_health_reports_task_queue_counts(tmp_path: Path) -> None:
    repo_root = tmp_path
    queue = JsonlTaskQueue(default_task_queue_path(repo_root))
    queue.append(
        TaskRecord(
            task_id="arc-task-queued-001",
            action_id="arc-action-queued-001",
            task_ref="task://queue/001",
            requested_action="arc.noop",
            payload_summary="queued task",
            source="samples/tasks/preview_summary.json",
            status="queued",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
    )
    queue.append(
        TaskRecord(
            task_id="arc-task-blocked-001",
            action_id="arc-action-blocked-001",
            task_ref="task://queue/002",
            requested_action="arc.preview_operator_response",
            payload_summary="blocked task",
            source="samples/tasks/external_email_send.json",
            status="blocked",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
    )
    queue.append(
        TaskRecord(
            task_id="arc-task-completed-001",
            action_id="arc-action-completed-001",
            task_ref="task://queue/003",
            requested_action="arc.local_model_preview",
            payload_summary="completed task",
            source="samples/tasks/local_model_preview.json",
            status="completed",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
    )

    payload = build_health_report(repo_root=repo_root)

    assert payload["task_queue_present"] is True
    assert payload["queued_task_count"] == 1
    assert payload["blocked_task_count"] == 1
    assert payload["completed_task_count"] == 1


def test_existing_history_and_evidence_commands_still_work(tmp_path: Path) -> None:
    queue_path, intake_payload = _intake_local_preview(tmp_path)
    state_path = tmp_path / "state" / "runs.jsonl"
    evidence_dir = tmp_path / "evidence"

    run_result = _console(
        "--task-queue-path",
        str(queue_path),
        "--state-path",
        str(state_path),
        "run-task",
        intake_payload["task"]["task_id"],
        "--runtime",
        "fake",
        "--model-adapter",
        "deterministic",
        "--evidence-dir",
        str(evidence_dir),
    )
    assert run_result.returncode == 0

    history = build_history_payload(state_path)
    evidence = build_evidence_payload(state_path)

    assert history["runs"][0]["requested_action"] == "arc.local_model_preview"
    assert evidence["evidence"][0]["model_preview_adapter"] == "deterministic"
