"""Evidence and CLI smoke tests for Arc Harness Shell v0.1."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from arc_bot_shell.harness import run_task_packet


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_evidence_bundle_is_written_for_successful_runs(tmp_path: Path) -> None:
    result = run_task_packet(
        REPO_ROOT / "samples" / "tasks" / "preview_summary.json",
        runtime_name="fake",
        evidence_dir=tmp_path,
    )

    assert result.exit_code == 0
    payload = json.loads(result.evidence_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == result.run_id
    assert payload["action_id"] == "arc-action-preview-summary-001"
    assert payload["guardian_status"] == "allowed_preview_only"
    assert payload["runtime_adapter"] == "fake"
    assert payload["redaction_metadata"]["status"] == "placeholder"


def test_cli_smoke_preview_and_blocked_paths(tmp_path: Path) -> None:
    preview = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.harness",
            "run",
            "samples/tasks/preview_summary.json",
            "--runtime",
            "fake",
            "--evidence-dir",
            str(tmp_path / "preview"),
            "--compact",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    blocked = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.harness",
            "run",
            "samples/tasks/external_email_send.json",
            "--runtime",
            "fake",
            "--evidence-dir",
            str(tmp_path / "blocked"),
            "--compact",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert preview.returncode == 0
    assert json.loads(preview.stdout)["result_status"] == "preview_completed"
    assert blocked.returncode == 2
    blocked_payload = json.loads(blocked.stdout)
    assert blocked_payload["result_status"] == "blocked"
    assert blocked_payload["runtime_called"] is False
