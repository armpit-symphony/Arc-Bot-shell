"""Stable manager CLI that invokes the selected Arc release's public commands."""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from typing import Any

from arc_bot_shell.approvals import ApprovalRecord, JsonlApprovalStore
from arc_bot_shell.tasks import JsonlTaskQueue, intake_task

from .config import ARC_V0_10_ROLLBACK_TAG, OperatorConfig
from .diagnostics import create_diagnostics_bundle
from .local_service import (
    start_local_service,
    status_local_service,
    stop_local_service,
)
from .views import (
    list_approvals,
    list_evidence,
    list_history,
    list_tasks,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _append_audit(config: OperatorConfig, event: str, **metadata: object) -> None:
    path = config.paths.audit_log_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(
                {"at": _utc_now(), "event": event, **metadata},
                sort_keys=True,
            )
        )
        handle.write("\n")


def _active_release(config: OperatorConfig) -> dict[str, str]:
    pointer_path = config.paths.current / "release.json"
    if not pointer_path.exists():
        return {
            "app_root": config.app_root,
            "python_executable": config.python_executable,
            "tag": config.installed_tag or "",
            "commit": config.installed_commit or "",
        }
    payload = json.loads(pointer_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise RuntimeError("active Arc release pointer is malformed")
    required = ("app_root", "python_executable", "tag", "commit")
    if any(not isinstance(payload.get(key), str) for key in required):
        raise RuntimeError("active Arc release pointer is incomplete")
    app_root = Path(str(payload["app_root"])).resolve()
    python_executable = Path(str(payload["python_executable"])).resolve()
    if not app_root.is_dir() or not python_executable.is_file():
        raise RuntimeError("active Arc release is unavailable")
    return {key: str(payload[key]) for key in required}


def _run_release(
    config: OperatorConfig,
    arguments: list[str],
    *,
    accepted_exit_codes: set[int] | None = None,
) -> tuple[dict[str, Any], int]:
    release = _active_release(config)
    completed = subprocess.run(
        [release["python_executable"], *arguments],
        cwd=release["app_root"],
        env={**os.environ, **config.environment()},
        capture_output=True,
        text=True,
        timeout=360,
        check=False,
    )
    accepted = {0} if accepted_exit_codes is None else accepted_exit_codes
    if completed.returncode not in accepted:
        message = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(
            f"Arc release command failed with {completed.returncode}: {message[:512]}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Arc release command returned malformed JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Arc release command did not return a JSON object")
    return payload, completed.returncode


def doctor(config: OperatorConfig) -> dict[str, Any]:
    payload, _ = _run_release(
        config,
        ["-m", "arc_bot_shell.integrations", "doctor"],
        accepted_exit_codes={0},
    )
    return payload


def health(config: OperatorConfig) -> dict[str, Any]:
    payload, _ = _run_release(
        config,
        ["-m", "arc_bot_shell.health"],
        accepted_exit_codes={0},
    )
    return payload


def status(config: OperatorConfig) -> dict[str, object]:
    doctor_report = doctor(config)
    release = _active_release(config)
    startup_state: dict[str, object] = {"registered": False}
    if config.paths.startup_state_path.exists():
        parsed = json.loads(
            config.paths.startup_state_path.read_text(encoding="utf-8-sig")
        )
        if isinstance(parsed, dict):
            startup_state = parsed
    return {
        "service": status_local_service(config).to_dict(),
        "guardian_ready": doctor_report.get("real_guardian_ready") is True,
        "lima_ready": doctor_report.get("guardian_to_lima_contract_compatible")
        is True,
        "ollama_reachable": doctor_report.get("ollama_reachable") is True,
        "configured_model": config.model,
        "configured_model_available": doctor_report.get(
            "ollama_model_available"
        )
        is True,
        "integrated_runtime_ready": doctor_report.get(
            "full_local_integration_ready"
        )
        is True,
        "startup": startup_state,
        "active_release": release,
        "network_listener": None,
    }


def _approval_from_result(
    task: object,
    payload: dict[str, Any],
) -> ApprovalRecord | None:
    guardian_status = str(payload.get("guardian_status", ""))
    if guardian_status not in {"deny", "requires_approval"}:
        return None
    timestamp = _utc_now()
    return ApprovalRecord(
        approval_id=f"arc-approval-{uuid.uuid4().hex[:12]}",
        task_id=str(getattr(task, "task_id")),
        run_id=str(payload.get("run_id", "")),
        action_id=str(payload.get("action_id", getattr(task, "action_id"))),
        task_ref=str(getattr(task, "task_ref")),
        requested_action=str(getattr(task, "requested_action")),
        guardian_decision_id=str(payload.get("guardian_decision_id", "")),
        guardian_status=(
            "requires_operator_approval"
            if guardian_status == "requires_approval"
            else "blocked"
        ),
        blocked_reason=(
            None
            if payload.get("blocked_reason") is None
            else str(payload["blocked_reason"])
        ),
        evidence_path=str(payload.get("evidence_path", "")),
        status="pending",
        created_at=timestamp,
        updated_at=timestamp,
    )


def submit(config: OperatorConfig, task_path: Path) -> dict[str, Any]:
    paths = config.paths
    paths.ensure()
    task = intake_task(task_path, queue_path=paths.task_queue_path)
    queue = JsonlTaskQueue(paths.task_queue_path)
    running = replace(task, status="running", updated_at=_utc_now())
    queue.upsert(running)
    arguments = [
        "-m",
        "arc_bot_shell.harness",
        "run",
        str(task_path),
        "--runtime",
        "lima",
        "--executor",
        "ollama",
        "--guardian",
        "guardian_core",
        "--model",
        config.model,
        "--evidence-dir",
        str(paths.evidence_dir),
        "--state-path",
        str(paths.state_path),
        "--compact",
    ]
    if config.guardian_path:
        arguments.extend(["--guardian-path", config.guardian_path])
    payload, exit_code = _run_release(
        config,
        arguments,
        accepted_exit_codes={0, 2, 3, 4},
    )
    result_status = str(payload.get("result_status", "failed"))
    queue_status = (
        "completed"
        if result_status == "lima_ollama_preview_completed"
        else (
            "blocked"
            if result_status in {"blocked", "requires_operator_approval"}
            else "failed"
        )
    )
    approval = _approval_from_result(running, payload)
    if approval is not None:
        JsonlApprovalStore(paths.approval_path).append(approval)
    final = replace(
        running,
        status=queue_status,  # type: ignore[arg-type]
        updated_at=_utc_now(),
        latest_run_id=str(payload.get("run_id", "")) or None,
        latest_guardian_status=str(payload.get("guardian_status", "")) or None,
        latest_result_status=result_status,
        latest_evidence_path=str(payload.get("evidence_path", "")) or None,
        latest_error_message=(
            None
            if payload.get("blocked_reason") is None
            else str(payload["blocked_reason"])
        ),
        latest_approval_id=None if approval is None else approval.approval_id,
        latest_approval_status=None if approval is None else approval.status,
    )
    queue.upsert(final)
    payload.update(
        {
            "task_id": final.task_id,
            "task_status": final.status,
            "exit_code": exit_code,
        }
    )
    _append_audit(
        config,
        "task_submitted",
        task_id=final.task_id,
        run_id=payload.get("run_id"),
        result_status=result_status,
        guardian_decision_id=payload.get("guardian_decision_id"),
    )
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Arc Windows operator commands.")
    parser.add_argument(
        "command",
        choices=(
            "start",
            "stop",
            "restart",
            "status",
            "doctor",
            "health",
            "submit",
            "tasks",
            "history",
            "approvals",
            "evidence",
            "diagnostics",
            "version",
        ),
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--task-file", type=Path)
    parser.add_argument("--limit", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = OperatorConfig.load(args.config)
    exit_code = 0
    if args.command == "start":
        payload: object = start_local_service(config).to_dict()
        _append_audit(config, "service_start")
    elif args.command == "stop":
        payload = stop_local_service(config).to_dict()
        _append_audit(config, "service_stop")
    elif args.command == "restart":
        stop_local_service(config)
        payload = start_local_service(config).to_dict()
        _append_audit(config, "service_restart")
    elif args.command == "status":
        payload = status(config)
    elif args.command == "doctor":
        payload = doctor(config)
        exit_code = 0 if not payload.get("blockers") else 4
    elif args.command == "health":
        payload = health(config)
    elif args.command == "submit":
        if args.task_file is None:
            raise SystemExit("--task-file is required for submit")
        payload = submit(config, args.task_file.resolve())
        exit_code = int(payload["exit_code"])
    elif args.command == "tasks":
        payload = list_tasks(config, args.limit)
    elif args.command == "history":
        payload = list_history(config, args.limit)
    elif args.command == "approvals":
        payload = list_approvals(config, args.limit)
    elif args.command == "evidence":
        payload = list_evidence(config, args.limit)
    elif args.command == "diagnostics":
        bundle = create_diagnostics_bundle(
            config,
            doctor_report=doctor(config),
            health_report=health(config),
        )
        payload = {"diagnostics_bundle": bundle, "sanitized": True}
        _append_audit(config, "diagnostics_created", path=bundle)
    else:
        payload = {
            "manager_version": config.installed_version,
            "active_release": _active_release(config),
            "rollback_tag": ARC_V0_10_ROLLBACK_TAG,
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
