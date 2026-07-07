"""Console/state commands for Arc Harness Shell."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from arc_bot_shell.console.presenter import render_json
from arc_bot_shell.evidence import default_evidence_dir
from arc_bot_shell.state import JsonlStateStore, default_state_path
from arc_bot_shell.tasks import (
    TASK_STATUSES,
    JsonlTaskQueue,
    TaskQueueError,
    default_task_queue_path,
    intake_task,
    run_queued_task,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _state_store(path: Path | None = None) -> JsonlStateStore:
    return JsonlStateStore(path or default_state_path(_repo_root()))


def _task_queue(path: Path | None = None) -> JsonlTaskQueue:
    return JsonlTaskQueue(path or default_task_queue_path(_repo_root()))


def build_history_payload(state_path: Path | None = None) -> dict[str, Any]:
    store = _state_store(state_path)
    return {
        "runs": [record.to_dict() for record in store.list_runs()],
        "state_path": str(store.path),
    }


def build_show_run_payload(run_id: str, state_path: Path | None = None) -> tuple[dict[str, Any], int]:
    store = _state_store(state_path)
    record = store.get_run(run_id)
    if record is None:
        return {
            "error": "run_not_found",
            "run_id": run_id,
            "state_path": str(store.path),
        }, 1
    payload: dict[str, Any] = {
        "run": record.to_dict(),
        "state_path": str(store.path),
    }
    evidence_path = Path(record.evidence_path)
    if evidence_path.exists():
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        if isinstance(evidence, dict) and isinstance(evidence.get("model_preview"), dict):
            payload["model_preview"] = evidence["model_preview"]
    return payload, 0


def build_evidence_payload(state_path: Path | None = None) -> dict[str, Any]:
    store = _state_store(state_path)
    evidence: list[dict[str, Any]] = []
    for record in store.list_runs():
        evidence_path = Path(record.evidence_path)
        metadata: dict[str, Any] = {
            "run_id": record.run_id,
            "action_id": record.action_id,
            "guardian_status": record.guardian_status,
            "result_status": record.result_status,
            "evidence_path": record.evidence_path,
            "created_at": record.created_at,
            "exists": evidence_path.exists(),
        }
        if evidence_path.exists():
            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                metadata["evidence_guardian_status"] = payload.get("guardian_status")
                metadata["evidence_result_status"] = payload.get("result_status")
                model_preview = payload.get("model_preview")
                if isinstance(model_preview, dict):
                    metadata["model_preview_adapter"] = model_preview.get("adapter_name")
                    metadata["model_preview_model"] = model_preview.get("model_name")
                    metadata["model_preview_status"] = model_preview.get("status")
        evidence.append(metadata)
    return {
        "evidence": evidence,
        "evidence_dir": str(default_evidence_dir(_repo_root())),
    }


def build_inbox_payload(task_dir: Path | None = None) -> dict[str, Any]:
    resolved_dir = task_dir or (_repo_root() / "samples" / "tasks")
    tasks: list[dict[str, Any]] = []
    for path in sorted(resolved_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        tasks.append(
            {
                "file_name": path.name,
                "path": str(path),
                "action_id": payload.get("action_id"),
                "requested_action": payload.get("action_name"),
                "task_ref": payload.get("task_ref"),
            }
        )
    return {
        "task_dir": str(resolved_dir),
        "tasks": tasks,
    }


def build_intake_payload(task_path: Path, queue_path: Path | None = None) -> tuple[dict[str, Any], int]:
    record = intake_task(task_path, queue_path=queue_path)
    return {
        "task": record.to_dict(),
        "task_queue_path": str((queue_path or default_task_queue_path(_repo_root()))),
    }, 0


def build_tasks_payload(queue_path: Path | None = None, status: str | None = None) -> dict[str, Any]:
    queue = _task_queue(queue_path)
    return {
        "tasks": [record.to_dict() for record in queue.list_tasks(status=status)],
        "task_queue_path": str(queue.path),
    }


def build_task_payload(task_id: str, queue_path: Path | None = None) -> tuple[dict[str, Any], int]:
    queue = _task_queue(queue_path)
    record = queue.get_task(task_id)
    if record is None:
        return {
            "error": "task_not_found",
            "task_id": task_id,
            "task_queue_path": str(queue.path),
        }, 1
    return {
        "task": record.to_dict(),
        "task_queue_path": str(queue.path),
    }, 0


def build_run_task_payload(
    task_id: str,
    *,
    queue_path: Path | None = None,
    runtime_name: str,
    model_adapter_name: str | None = None,
    model_name: str | None = None,
    evidence_dir: Path | None = None,
    state_path: Path | None = None,
) -> tuple[dict[str, Any], int]:
    resolved_queue_path = queue_path or default_task_queue_path(_repo_root())
    try:
        task_record, harness_result, exit_code = run_queued_task(
            task_id,
            queue_path=resolved_queue_path,
            runtime_name=runtime_name,
            model_adapter_name=model_adapter_name,
            model_name=model_name,
            evidence_dir=evidence_dir,
            state_path=state_path,
            repo_root=_repo_root(),
        )
    except TaskQueueError as exc:
        return {
            "error": str(exc),
            "task_id": task_id,
            "task_queue_path": str(resolved_queue_path),
        }, 1

    payload: dict[str, Any] = {
        "task": task_record.to_dict(),
        "task_queue_path": str(resolved_queue_path),
    }
    if harness_result is not None:
        payload["run"] = harness_result.to_dict()
    elif task_record.latest_error_message is not None:
        payload["error"] = task_record.latest_error_message
    return payload, exit_code


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read Arc Harness Shell console/state data.")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON output")
    parser.add_argument(
        "--state-path",
        type=Path,
        default=None,
        help="Optional path to a JSONL state store",
    )
    parser.add_argument(
        "--task-queue-path",
        type=Path,
        default=None,
        help="Optional path to a JSONL task queue",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("history", help="List recorded harness runs")
    show_run = subparsers.add_parser("show-run", help="Show one run by run_id")
    show_run.add_argument("run_id", help="Run identifier")
    subparsers.add_parser("evidence", help="List recorded evidence bundles")
    inbox = subparsers.add_parser("inbox", help="List sample task packets")
    inbox.add_argument(
        "--task-dir",
        type=Path,
        default=None,
        help="Optional task directory",
    )
    intake = subparsers.add_parser("intake", help="Queue one task packet without running it")
    intake.add_argument("task_path", type=Path, help="Path to a task packet JSON file")
    tasks = subparsers.add_parser("tasks", help="List queued and completed tasks")
    tasks.add_argument(
        "--status",
        choices=TASK_STATUSES,
        default=None,
        help="Optional status filter",
    )
    task = subparsers.add_parser("task", help="Show one queued task")
    task.add_argument("task_id", help="Task identifier")
    run_task = subparsers.add_parser("run-task", help="Run one queued task through the harness")
    run_task.add_argument("task_id", help="Task identifier")
    run_task.add_argument(
        "--runtime",
        default="disabled",
        choices=("fake", "local_import", "disabled"),
        help="Runtime adapter to use for non-model-preview tasks",
    )
    run_task.add_argument(
        "--model-adapter",
        default=None,
        choices=("deterministic", "ollama"),
        help="Local model preview adapter for arc.local_model_preview tasks",
    )
    run_task.add_argument(
        "--model",
        default=None,
        help="Optional local model name override for model preview adapters",
    )
    run_task.add_argument(
        "--evidence-dir",
        type=Path,
        default=None,
        help="Optional evidence directory override",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "history":
        payload = build_history_payload(args.state_path)
        print(render_json(payload, compact=args.compact))
        return 0
    if args.command == "show-run":
        payload, exit_code = build_show_run_payload(args.run_id, args.state_path)
        print(render_json(payload, compact=args.compact))
        return exit_code
    if args.command == "evidence":
        payload = build_evidence_payload(args.state_path)
        print(render_json(payload, compact=args.compact))
        return 0
    if args.command == "inbox":
        payload = build_inbox_payload(args.task_dir)
        print(render_json(payload, compact=args.compact))
        return 0
    if args.command == "intake":
        payload, exit_code = build_intake_payload(args.task_path, args.task_queue_path)
        print(render_json(payload, compact=args.compact))
        return exit_code
    if args.command == "tasks":
        payload = build_tasks_payload(args.task_queue_path, args.status)
        print(render_json(payload, compact=args.compact))
        return 0
    if args.command == "task":
        payload, exit_code = build_task_payload(args.task_id, args.task_queue_path)
        print(render_json(payload, compact=args.compact))
        return exit_code
    if args.command == "run-task":
        payload, exit_code = build_run_task_payload(
            args.task_id,
            queue_path=args.task_queue_path,
            runtime_name=args.runtime,
            model_adapter_name=args.model_adapter,
            model_name=args.model,
            evidence_dir=args.evidence_dir,
            state_path=args.state_path,
        )
        print(render_json(payload, compact=args.compact))
        return exit_code
    parser.error(f"unsupported command {args.command!r}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
