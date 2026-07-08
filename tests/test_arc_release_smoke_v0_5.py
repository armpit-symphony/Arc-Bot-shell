"""Release-candidate smoke and artifact path tests for Arc Harness Shell."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from arc_bot_shell.evidence import default_evidence_dir
from arc_bot_shell.state import default_state_path
from arc_bot_shell.tasks import default_task_queue_path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_release_smoke_script_passes(tmp_path: Path) -> None:
    task_queue_path = tmp_path / "artifacts" / "tasks" / "release_smoke_tasks.jsonl"
    state_path = tmp_path / "artifacts" / "state" / "release_smoke_runs.jsonl"
    evidence_dir = tmp_path / "artifacts" / "evidence" / "release_smoke"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/smoke_arc_harness_release.py",
            "--repo-root",
            str(REPO_ROOT),
            "--task-queue-path",
            str(task_queue_path),
            "--state-path",
            str(state_path),
            "--evidence-dir",
            str(evidence_dir),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert task_queue_path.exists()
    assert state_path.exists()
    assert evidence_dir.exists()


def test_generated_artifact_paths_stay_under_ignored_artifacts_dirs() -> None:
    evidence_dir = default_evidence_dir(REPO_ROOT)
    state_path = default_state_path(REPO_ROOT)
    task_queue_path = default_task_queue_path(REPO_ROOT)

    assert evidence_dir == REPO_ROOT / "artifacts" / "evidence"
    assert state_path == REPO_ROOT / "artifacts" / "state" / "runs.jsonl"
    assert task_queue_path == REPO_ROOT / "artifacts" / "tasks" / "tasks.jsonl"
