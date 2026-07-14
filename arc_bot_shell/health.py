"""Health report for Arc Harness Shell release candidate."""

from __future__ import annotations

from pathlib import Path
import sys

from arc_bot_shell.approvals import JsonlApprovalStore, default_approval_path
from arc_bot_shell.console import render_json
from arc_bot_shell.evidence import default_evidence_dir
from arc_bot_shell.guardian import GuardianSuiteAdapter
from arc_bot_shell.lima import LimaRuntimeUnavailableError, LocalLimaImportRuntimePort, load_workspace_lock
from arc_bot_shell.model import (
    deterministic_model_adapter_available,
    model_preview_available,
    ollama_configured,
)
from arc_bot_shell.state import JsonlStateStore, default_state_path
from arc_bot_shell.tasks import JsonlTaskQueue, default_task_queue_path


def build_health_report(repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[1]
    lock_payload = load_workspace_lock(root)
    guardian_adapter = GuardianSuiteAdapter()
    local_runtime = LocalLimaImportRuntimePort(repo_root=root)
    state_path = default_state_path(root)
    evidence_dir = default_evidence_dir(root)
    state_store = JsonlStateStore(state_path)
    task_queue = JsonlTaskQueue(default_task_queue_path(root))
    task_counts = task_queue.counts_by_status()
    approval_store = JsonlApprovalStore(default_approval_path(root))
    approval_counts = approval_store.counts_by_status()
    try:
        resolved = local_runtime.resolve_lima_import()
    except LimaRuntimeUnavailableError as exc:
        lima_status: dict[str, object] = {
            "configured": False,
            "runtime": "local_import",
            "reason": str(exc),
        }
    else:
        lima_status = {
            "configured": True,
            "runtime": "local_import",
            "source": resolved.source,
            "checkout_path": str(resolved.checkout_path) if resolved.checkout_path else None,
        }
    samples_dir = root / "samples" / "tasks"
    return {
        "status": "ok",
        "artifact": "arc_harness_shell_v0_5_rc",
        "guardian": {
            "public_entrypoint": guardian_adapter.public_entrypoint,
            "available": guardian_adapter.is_available(),
            "fallback": "fail_closed_guardian",
        },
        "lima": lima_status,
        "workspace_lock_present": lock_payload is not None,
        "state_store_present": state_path.exists(),
        "evidence_dir_present": evidence_dir.exists(),
        "recent_run_count": len(state_store.list_runs()) if state_path.exists() else 0,
        "task_queue_present": task_queue.exists(),
        "queued_task_count": task_counts.get("queued", 0),
        "blocked_task_count": task_counts.get("blocked", 0),
        "completed_task_count": task_counts.get("completed", 0),
        "approval_queue_present": approval_store.exists(),
        "pending_approval_count": approval_counts.get("pending", 0),
        "approved_approval_count": approval_counts.get("approved", 0),
        "denied_approval_count": approval_counts.get("denied", 0),
        "model_preview_available": model_preview_available(),
        "deterministic_model_adapter_available": deterministic_model_adapter_available(),
        "ollama_configured": ollama_configured(),
        "samples": {
            "preview_summary": (samples_dir / "preview_summary.json").exists(),
            "external_email_send": (samples_dir / "external_email_send.json").exists(),
            "file_write_attempt": (samples_dir / "file_write_attempt.json").exists(),
            "local_model_preview": (samples_dir / "local_model_preview.json").exists(),
        },
        "smoke_commands": [
            "python scripts/smoke_arc_harness_release.py",
            "python -m arc_bot_shell.health",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    del argv
    print(render_json(build_health_report(), compact=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
