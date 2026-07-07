"""Health report for Arc Harness Shell v0.1."""

from __future__ import annotations

from pathlib import Path
import sys

from arc_bot_shell.console import render_json
from arc_bot_shell.guardian import GuardianSuiteAdapter
from arc_bot_shell.lima import LimaRuntimeUnavailableError, LocalLimaImportRuntimePort, load_workspace_lock


def build_health_report(repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[1]
    lock_payload = load_workspace_lock(root)
    guardian_adapter = GuardianSuiteAdapter()
    local_runtime = LocalLimaImportRuntimePort(repo_root=root)
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
        "artifact": "arc_harness_shell_v0_1",
        "guardian": {
            "public_entrypoint": guardian_adapter.public_entrypoint,
            "available": guardian_adapter.is_available(),
            "fallback": "fail_closed_guardian",
        },
        "lima": lima_status,
        "workspace_lock_present": lock_payload is not None,
        "samples": {
            "preview_summary": (samples_dir / "preview_summary.json").exists(),
            "external_email_send": (samples_dir / "external_email_send.json").exists(),
            "file_write_attempt": (samples_dir / "file_write_attempt.json").exists(),
        },
        "smoke_commands": [
            "python -m arc_bot_shell.harness run samples/tasks/preview_summary.json --runtime fake",
            "python -m arc_bot_shell.harness run samples/tasks/external_email_send.json --runtime fake",
            "python -m arc_bot_shell.health",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    del argv
    print(render_json(build_health_report(), compact=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
