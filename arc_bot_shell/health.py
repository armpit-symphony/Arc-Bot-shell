"""Health report for Arc Harness Shell release candidate."""

from __future__ import annotations

from importlib.util import find_spec
import os
from pathlib import Path
import sys

from arc_bot_shell.approvals import JsonlApprovalStore, default_approval_path
from arc_bot_shell.console import render_json
from arc_bot_shell.evidence import default_evidence_dir
from arc_bot_shell.lima import (
    LIMA_ENTRYPOINT,
    LIMA_PINNED_COMMIT,
    LIMA_PINNED_REFERENCE,
    LIMA_PINNED_TAG_OBJECT,
    DEFAULT_OLLAMA_MODEL,
    LimaRuntimeUnavailableError,
    LocalLimaImportRuntimePort,
    load_workspace_lock,
)
from arc_bot_shell.integrations import DoctorConfig, run_doctor
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
    local_runtime = LocalLimaImportRuntimePort(repo_root=root)
    state_path = default_state_path(root)
    evidence_dir = default_evidence_dir(root)
    state_store = JsonlStateStore(state_path)
    task_queue = JsonlTaskQueue(default_task_queue_path(root))
    task_counts = task_queue.counts_by_status()
    approval_store = JsonlApprovalStore(default_approval_path(root))
    approval_counts = approval_store.counts_by_status()
    doctor_config = DoctorConfig.from_environ(os.environ)
    doctor_report = run_doctor(doctor_config)
    # Report the runtime Arc actually uses. The legacy local_import port needs
    # lima.adapters, which the published lima-runtime wheel does not ship, so
    # reporting LIMA solely through that port told every packaged install that
    # "LIMA runtime is not installed" while lima.runtime was imported and
    # working. That is a true statement about the legacy port and a false one
    # about LIMA.
    lima_status: dict[str, object] = {
        "configured": doctor_report.get("lima_available") is True,
        "runtime": "lima.runtime",
        "entrypoint": LIMA_ENTRYPOINT,
        "pinned_commit": LIMA_PINNED_COMMIT,
    }
    try:
        resolved = local_runtime.resolve_lima_import()
    except LimaRuntimeUnavailableError as exc:
        # Kept as its own field, and named for what it is. An operator reading
        # this needs to know a retired source-checkout adapter is unavailable,
        # not conclude that LIMA is missing.
        lima_status["legacy_local_import"] = {
            "available": False,
            "requires": "lima.adapters from a LIMA-AI-OS source checkout",
            "reason": str(exc),
        }
    else:
        lima_status["legacy_local_import"] = {
            "available": True,
            "source": resolved.source,
            "checkout_path": (
                str(resolved.checkout_path) if resolved.checkout_path else None
            ),
        }
    samples_dir = root / "samples" / "tasks"
    return {
        "status": "ok",
        "artifact": "arc_harness_shell_v0_5_rc",
        "guardian": {
            "public_entrypoint": "guardian_core",
            "available": find_spec("guardian_core") is not None,
            "fallback": "fail_closed_guardian",
        },
        "lima": lima_status,
        "lima_public_entrypoint": LIMA_ENTRYPOINT,
        "lima_pinned_reference": LIMA_PINNED_REFERENCE,
        "lima_pinned_commit": LIMA_PINNED_COMMIT,
        "lima_pinned_tag_object": LIMA_PINNED_TAG_OBJECT,
        # Sourced from the doctor rather than from whether a source checkout
        # was found: locating a checkout says nothing about executor readiness.
        "lima_fake_executor_smoke_ready": bool(
            doctor_report.get("fake_executor_smoke_ready")
        ),
        "lima_loopback_ollama_supported": bool(
            doctor_report.get("lima_loopback_ollama_supported")
        ),
        "ollama_integration_ready": bool(
            doctor_report.get("full_local_integration_ready")
        ),
        "local_model_runtime": "ollama",
        "ollama_available": bool(doctor_report.get("ollama_reachable")),
        "configured_model": doctor_config.ollama_model or DEFAULT_OLLAMA_MODEL,
        "configured_model_available": bool(
            doctor_report.get("ollama_model_available")
        ),
        "guardian_ready": bool(doctor_report.get("real_guardian_ready")),
        # The same source of truth the operator CLI's status uses. This
        # previously also required lima_loopback_ollama_supported, which the
        # non-executing v0.11 control plane retires by design, so lima_ready
        # could never be true and disagreed with status on every install.
        "lima_ready": bool(
            doctor_report.get("guardian_to_lima_contract_compatible")
        ),
        "integrated_runtime_ready": bool(
            doctor_report.get("full_local_integration_ready")
        ),
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
            "python scripts/smoke_arc_lima_guardian_ollama.py",
            "python -m arc_bot_shell.health",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    del argv
    print(render_json(build_health_report(), compact=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
