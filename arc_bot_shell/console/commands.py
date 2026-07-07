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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _state_store(path: Path | None = None) -> JsonlStateStore:
    return JsonlStateStore(path or default_state_path(_repo_root()))


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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read Arc Harness Shell console/state data.")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON output")
    parser.add_argument(
        "--state-path",
        type=Path,
        default=None,
        help="Optional path to a JSONL state store",
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
    parser.error(f"unsupported command {args.command!r}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
