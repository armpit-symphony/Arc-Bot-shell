"""Release smoke for Arc Harness Shell."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


def _json_command(command: list[str], *, cwd: Path) -> tuple[int, dict[str, Any]]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
    return completed.returncode, payload


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def _reset_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Arc Harness Shell release smoke path.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root",
    )
    parser.add_argument(
        "--task-queue-path",
        type=Path,
        default=None,
        help="Optional task queue path override",
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=None,
        help="Optional state path override",
    )
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=None,
        help="Optional evidence directory override",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    task_queue_path = args.task_queue_path or (repo_root / "artifacts" / "tasks" / "release_smoke_tasks.jsonl")
    state_path = args.state_path or (repo_root / "artifacts" / "state" / "release_smoke_runs.jsonl")
    evidence_dir = args.evidence_dir or (repo_root / "artifacts" / "evidence" / "release_smoke")

    _reset_path(task_queue_path)
    _reset_path(state_path)
    _reset_path(evidence_dir)

    python = sys.executable

    health_code, health = _json_command([python, "-m", "arc_bot_shell.health"], cwd=repo_root)
    _assert(health_code == 0, "health command failed")
    _assert(health.get("status") == "ok", "health status was not ok")

    intake_code, intake = _json_command(
        [
            python,
            "-m",
            "arc_bot_shell.console",
            "--task-queue-path",
            str(task_queue_path),
            "intake",
            "samples/tasks/local_model_preview.json",
        ],
        cwd=repo_root,
    )
    _assert(intake_code == 0, "intake command failed")
    task = intake.get("task", {})
    task_id = str(task.get("task_id", ""))
    _assert(task.get("status") == "queued", "intake did not create a queued task")
    _assert(task_id, "intake did not return a task_id")

    run_task_code, run_task = _json_command(
        [
            python,
            "-m",
            "arc_bot_shell.console",
            "--task-queue-path",
            str(task_queue_path),
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
        ],
        cwd=repo_root,
    )
    _assert(run_task_code == 0, "run-task command failed")
    completed_task = run_task.get("task", {})
    completed_run = run_task.get("run", {})
    _assert(completed_task.get("status") == "completed", "queued task did not complete")
    _assert(completed_run.get("result_status") == "preview_completed", "model preview run did not complete")
    _assert(completed_run.get("model_preview_called") is True, "model preview path was not used")

    blocked_code, blocked = _json_command(
        [
            python,
            "-m",
            "arc_bot_shell.harness",
            "run",
            "samples/tasks/external_email_send.json",
            "--runtime",
            "fake",
            "--evidence-dir",
            str(evidence_dir),
            "--state-path",
            str(state_path),
        ],
        cwd=repo_root,
    )
    _assert(blocked_code == 2, "blocked harness smoke did not exit with code 2")
    _assert(blocked.get("result_status") == "blocked", "external email sample was not blocked")
    _assert(blocked.get("runtime_called") is False, "blocked external send called runtime")
    _assert(blocked.get("model_preview_called") is False, "blocked external send called model preview")

    history_code, history = _json_command(
        [
            python,
            "-m",
            "arc_bot_shell.console",
            "--state-path",
            str(state_path),
            "history",
        ],
        cwd=repo_root,
    )
    _assert(history_code == 0, "history command failed")
    run_ids = {item.get("run_id") for item in history.get("runs", [])}
    _assert(completed_run.get("run_id") in run_ids, "history is missing the completed queue run")
    _assert(blocked.get("run_id") in run_ids, "history is missing the blocked harness run")

    evidence_code, evidence = _json_command(
        [
            python,
            "-m",
            "arc_bot_shell.console",
            "--state-path",
            str(state_path),
            "evidence",
        ],
        cwd=repo_root,
    )
    _assert(evidence_code == 0, "evidence command failed")
    evidence_run_ids = {item.get("run_id") for item in evidence.get("evidence", [])}
    _assert(completed_run.get("run_id") in evidence_run_ids, "evidence list is missing the completed queue run")
    _assert(blocked.get("run_id") in evidence_run_ids, "evidence list is missing the blocked harness run")

    tasks_code, tasks = _json_command(
        [
            python,
            "-m",
            "arc_bot_shell.console",
            "--task-queue-path",
            str(task_queue_path),
            "tasks",
        ],
        cwd=repo_root,
    )
    _assert(tasks_code == 0, "tasks command failed")
    task_items = {item.get("task_id"): item for item in tasks.get("tasks", [])}
    _assert(task_id in task_items, "tasks command is missing the queued task record")
    _assert(task_items[task_id].get("status") == "completed", "tasks command did not show the completed task status")

    summary = {
        "status": "ok",
        "task_id": task_id,
        "completed_run_id": completed_run.get("run_id"),
        "blocked_run_id": blocked.get("run_id"),
        "task_queue_path": str(task_queue_path),
        "state_path": str(state_path),
        "evidence_dir": str(evidence_dir),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
