"""Console/state tests for Arc Harness Shell v0.2."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from arc_bot_shell.health import build_health_report
from arc_bot_shell.harness import run_task_packet
from arc_bot_shell.state import JsonlStateStore, StateRunRecord, default_state_path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_sample_tasks(tmp_path: Path) -> tuple[Path, Path]:
    state_path = tmp_path / "state" / "runs.jsonl"
    evidence_dir = tmp_path / "evidence"
    run_task_packet(
        REPO_ROOT / "samples" / "tasks" / "preview_summary.json",
        runtime_name="fake",
        evidence_dir=evidence_dir,
        state_path=state_path,
    )
    run_task_packet(
        REPO_ROOT / "samples" / "tasks" / "external_email_send.json",
        runtime_name="fake",
        evidence_dir=evidence_dir,
        state_path=state_path,
    )
    return state_path, evidence_dir


def test_completed_harness_run_appends_state(tmp_path: Path) -> None:
    state_path = tmp_path / "state" / "runs.jsonl"
    result = run_task_packet(
        REPO_ROOT / "samples" / "tasks" / "preview_summary.json",
        runtime_name="fake",
        evidence_dir=tmp_path / "evidence",
        state_path=state_path,
    )

    records = JsonlStateStore(state_path).list_runs()

    assert result.exit_code == 0
    assert len(records) == 1
    assert records[0].run_id == result.run_id
    assert records[0].requested_action == "arc.preview_operator_response"
    assert records[0].guardian_status == "allowed_preview_only"
    assert records[0].runtime_called is True


def test_blocked_harness_run_appends_state(tmp_path: Path) -> None:
    state_path = tmp_path / "state" / "runs.jsonl"
    result = run_task_packet(
        REPO_ROOT / "samples" / "tasks" / "external_email_send.json",
        runtime_name="fake",
        evidence_dir=tmp_path / "evidence",
        state_path=state_path,
    )

    records = JsonlStateStore(state_path).list_runs()

    assert result.exit_code == 2
    assert len(records) == 1
    assert records[0].run_id == result.run_id
    assert records[0].guardian_status == "blocked"
    assert records[0].runtime_called is False
    assert records[0].blocked_reason == "external_send is blocked in Arc Harness Shell v0.1"


def test_blocked_run_does_not_call_runtime_and_still_appears_in_history(tmp_path: Path) -> None:
    state_path, _ = _run_sample_tasks(tmp_path)

    completed, blocked = JsonlStateStore(state_path).list_runs(limit=2)

    assert completed.result_status == "blocked"
    assert completed.runtime_called is False
    history = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.console",
            "--state-path",
            str(state_path),
            "history",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(history.stdout)
    statuses = [item["guardian_status"] for item in payload["runs"]]
    assert "blocked" in statuses
    assert "allowed_preview_only" in statuses
    assert blocked.runtime_called is True


def test_console_history_reads_real_state(tmp_path: Path) -> None:
    state_path, _ = _run_sample_tasks(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.console",
            "--state-path",
            str(state_path),
            "history",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert len(payload["runs"]) == 2
    assert payload["runs"][0]["action_id"] == "arc-action-external-email-send-001"
    assert payload["runs"][1]["action_id"] == "arc-action-preview-summary-001"


def test_console_show_run_returns_selected_run(tmp_path: Path) -> None:
    state_path, _ = _run_sample_tasks(tmp_path)
    selected = JsonlStateStore(state_path).list_runs()[0]

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.console",
            "--state-path",
            str(state_path),
            "show-run",
            selected.run_id,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["run"]["run_id"] == selected.run_id
    assert payload["run"]["evidence_path"] == selected.evidence_path


def test_console_evidence_lists_evidence_bundles(tmp_path: Path) -> None:
    state_path, _ = _run_sample_tasks(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.console",
            "--state-path",
            str(state_path),
            "evidence",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert len(payload["evidence"]) == 2
    assert all(item["exists"] is True for item in payload["evidence"])


def test_console_inbox_lists_sample_task_packets() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.console",
            "inbox",
            "--task-dir",
            str(REPO_ROOT / "samples" / "tasks"),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    action_ids = [item["action_id"] for item in payload["tasks"]]
    assert "arc-action-preview-summary-001" in action_ids
    assert "arc-action-external-email-send-001" in action_ids


def test_health_reports_state_and_evidence_presence(tmp_path: Path) -> None:
    repo_root = tmp_path
    state_path = default_state_path(repo_root)
    state_record = StateRunRecord(
        run_id="arc-run-health-001",
        action_id="arc-action-health-001",
        task_ref="task://health/001",
        requested_action="arc.noop",
        guardian_decision_id="guardian-decision:arc-action-health-001",
        guardian_status="allowed_preview_only",
        blocked_reason=None,
        runtime_adapter="fake",
        runtime_called=True,
        result_status="preview_completed",
        evidence_path=str(repo_root / "artifacts" / "evidence" / "arc-run-health-001.json"),
        created_at="2026-01-01T00:00:00Z",
    )
    JsonlStateStore(state_path).append(state_record)
    (repo_root / "artifacts" / "evidence").mkdir(parents=True, exist_ok=True)

    payload = build_health_report(repo_root=repo_root)

    assert payload["state_store_present"] is True
    assert payload["evidence_dir_present"] is True
    assert payload["recent_run_count"] == 1
