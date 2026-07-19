from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from arc_bot_shell.approvals import JsonlApprovalStore
from arc_bot_shell.service.config import (
    ARC_STARTUP_TASK_NAME,
    ARC_V0_10_COMMIT,
    ARC_V0_10_ROLLBACK_TAG,
    ArcInstallPaths,
    OperatorConfig,
)
from arc_bot_shell.service.diagnostics import (
    create_diagnostics_bundle,
    redact_diagnostics,
)
from arc_bot_shell.service.local_service import (
    build_service_health_snapshot,
    run_local_service,
    status_local_service,
)
from arc_bot_shell.service.operator_runtime_cli import submit
from arc_bot_shell.service.pidfile import (
    DuplicateServiceError,
    ManagedProcessRecord,
    acquire_pidfile,
    read_pidfile,
    release_pidfile,
    stop_requested,
    write_stop_request,
)
from arc_bot_shell.tasks import JsonlTaskQueue


REPO_ROOT = Path(__file__).resolve().parents[1]


def _config(tmp_path: Path) -> OperatorConfig:
    root = tmp_path / "SparkPitLabs" / "ArcBot"
    return OperatorConfig(
        install_root=str(root.resolve()),
        app_root=str(REPO_ROOT.resolve()),
        python_executable=str(Path(sys.executable).resolve()),
        guardian_path=str((REPO_ROOT.parent / "LIMA-Guardian-Suite").resolve()),
        installed_tag="arc-harness-shell-v0-11-test",
        installed_commit="1" * 40,
    )


def test_install_paths_are_per_user_and_data_is_outside_repo(tmp_path: Path) -> None:
    config = _config(tmp_path)
    paths = config.paths
    paths.ensure()
    paths.assert_data_separated_from(REPO_ROOT)
    assert paths.data.parent == paths.root
    assert paths.evidence_dir.is_dir()
    assert paths.task_queue_path.parent.is_dir()
    assert paths.state_path.parent.is_dir()
    assert paths.approval_path.parent.is_dir()
    assert paths.startup_state_path.parent == paths.config


def test_data_path_inside_source_checkout_is_rejected() -> None:
    paths = ArcInstallPaths.from_root(REPO_ROOT / "operator-test")
    with pytest.raises(ValueError, match="outside"):
        paths.assert_data_separated_from(REPO_ROOT)


@pytest.mark.parametrize(
    "url",
    [
        "http://192.168.1.10:11434",
        "http://0.0.0.0:11434",
        "https://127.0.0.1:11434",
        "http://user:pass@127.0.0.1:11434",
        "http://127.0.0.1:11434/path",
        "http://127.0.0.1:11434?x=1",
        "http://127.0.0.1:11434#x",
        "http://127.0.0.1",
    ],
)
def test_operator_config_rejects_non_loopback_or_malformed_endpoints(
    tmp_path: Path,
    url: str,
) -> None:
    base = _config(tmp_path)
    with pytest.raises(ValueError):
        OperatorConfig.from_dict({**base.to_dict(), "ollama_url": url})


def test_operator_config_preserves_v0_10_authority_pins(tmp_path: Path) -> None:
    config = _config(tmp_path)
    assert config.guardian_reference == "guardian-core-v1.1-local-model-preview-policy"
    assert config.lima_reference == "lima-runtime-v1.1-loopback-ollama-executor"
    assert ARC_V0_10_ROLLBACK_TAG == "arc-harness-shell-v0.10"
    assert ARC_V0_10_COMMIT == "fa1e93ff18203218a863b679f3d3608aa46bd5a4"
    assert config.startup_task_name == ARC_STARTUP_TASK_NAME
    assert config.environment()["ARC_OLLAMA_URL"] == "http://127.0.0.1:11434"


def test_operator_config_round_trip_is_atomic(tmp_path: Path) -> None:
    config = _config(tmp_path)
    target = config.write()
    loaded = OperatorConfig.load(target)
    assert loaded == config
    assert not target.with_suffix(".json.tmp").exists()


def test_pidfile_duplicate_start_and_token_bound_release(tmp_path: Path) -> None:
    pid_path = tmp_path / "service.pid.json"
    record = ManagedProcessRecord.create(command="test")
    acquire_pidfile(pid_path, record)
    assert read_pidfile(pid_path) == record
    with pytest.raises(DuplicateServiceError):
        acquire_pidfile(
            pid_path,
            ManagedProcessRecord.create(command="duplicate"),
        )
    assert release_pidfile(pid_path, "wrong-token") is False
    assert pid_path.exists()
    assert release_pidfile(pid_path, record.token) is True
    assert not pid_path.exists()


def test_stop_request_requires_exact_managed_pid_and_token(tmp_path: Path) -> None:
    record = ManagedProcessRecord.create(command="test")
    path = tmp_path / "stop.json"
    write_stop_request(path, record)
    assert stop_requested(path, record) is True
    wrong = ManagedProcessRecord(
        pid=record.pid,
        token="wrong",
        started_at=record.started_at,
        command=record.command,
    )
    assert stop_requested(path, wrong) is False


def test_stale_pid_is_recovered_without_killing_a_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    config.paths.ensure()
    stale = ManagedProcessRecord.create(pid=424242, command="stale")
    config.paths.pid_path.write_text(json.dumps(stale.to_dict()), encoding="utf-8")
    monkeypatch.setattr(
        "arc_bot_shell.service.local_service.process_is_alive",
        lambda pid: False,
    )
    status = status_local_service(config)
    assert status.running is False
    assert status.stale_pid_recovered is True
    assert not config.paths.pid_path.exists()


def test_local_service_writes_non_listening_health_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    config.write()
    monkeypatch.setattr(
        "arc_bot_shell.service.local_service.build_service_health_snapshot",
        lambda current: {
            "captured_at": "test",
            "service_listening": False,
            "network_bind": None,
            "health": {"status": "ok"},
        },
    )
    assert run_local_service(config, once=True) == 0
    snapshot = json.loads(
        config.paths.health_snapshot_path.read_text(encoding="utf-8")
    )
    assert snapshot["service_listening"] is False
    assert snapshot["network_bind"] is None
    assert not config.paths.pid_path.exists()


def test_health_snapshot_has_no_listener_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    monkeypatch.setattr(
        "arc_bot_shell.service.local_service.build_health_report",
        lambda path: {"status": "ok", "root": str(path)},
    )
    snapshot = build_service_health_snapshot(config)
    assert snapshot["service_listening"] is False
    assert snapshot["network_bind"] is None


def test_diagnostics_redacts_sensitive_fields_and_omits_evidence(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    config.paths.ensure()
    config.write()
    config.paths.manifest_path.write_text(
        json.dumps({"token": "secret", "version": "0.11"}),
        encoding="utf-8",
    )
    sanitized = redact_diagnostics(
        {"password": "secret", "nested": {"output_text": "private", "ok": True}}
    )
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["nested"]["output_text"] == "[REDACTED]"
    bundle = Path(
        create_diagnostics_bundle(
            config,
            doctor_report={"blockers": [], "credential": "hidden"},
            health_report={"status": "ok", "prompt": "hidden"},
        )
    )
    with zipfile.ZipFile(bundle) as archive:
        names = set(archive.namelist())
        assert "doctor.json" in names
        assert "versions.json" in names
        assert not any("evidence" in name for name in names)
        doctor = json.loads(archive.read("doctor.json"))
        assert doctor["credential"] == "[REDACTED]"


def test_submit_uses_queue_then_guarded_runtime_without_permission_expansion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    config.paths.ensure()
    config.write()
    observed: dict[str, object] = {}

    def fake_release(current: OperatorConfig, arguments: list[str], **kwargs: object):
        observed["arguments"] = arguments
        return (
            {
                "action_id": "arc-action:local-model-preview-001",
                "run_id": "arc-run-test",
                "result_status": "lima_ollama_preview_completed",
                "guardian_status": "allow",
                "guardian_decision_id": "guardian-decision:test",
                "lima_called": True,
                "executor_called": True,
                "executor_call_count": 1,
                "ollama_called": True,
                "network_called": True,
                "network_scope": "loopback_only",
                "execution_allowed": False,
                "evidence_path": str(config.paths.evidence_dir / "run.json"),
                "output_text": "local response",
            },
            0,
        )

    monkeypatch.setattr(
        "arc_bot_shell.service.operator_runtime_cli._run_release",
        fake_release,
    )
    payload = submit(
        config,
        REPO_ROOT / "samples" / "tasks" / "local_model_preview.json",
    )
    args = observed["arguments"]
    assert isinstance(args, list)
    assert "--guardian" in args and "guardian_core" in args
    assert "--runtime" in args and "lima" in args
    assert "--executor" in args and "ollama" in args
    assert payload["guardian_decision_id"] == "guardian-decision:test"
    assert payload["execution_allowed"] is False
    tasks = JsonlTaskQueue(config.paths.task_queue_path).list_tasks()
    assert tasks[0].status == "completed"


def test_external_email_submit_remains_blocked_before_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    config.paths.ensure()
    config.write()

    def denied_release(current: OperatorConfig, arguments: list[str], **kwargs: object):
        return (
            {
                "action_id": "arc-action:external-email-001",
                "run_id": "arc-run-denied",
                "result_status": "blocked",
                "guardian_status": "deny",
                "guardian_decision_id": "guardian-decision:deny-test",
                "lima_called": False,
                "executor_called": False,
                "executor_call_count": 0,
                "ollama_called": False,
                "network_called": False,
                "execution_allowed": False,
                "blocked_reason": "External email remains blocked",
                "evidence_path": str(config.paths.evidence_dir / "denied.json"),
                "output_text": "",
            },
            2,
        )

    monkeypatch.setattr(
        "arc_bot_shell.service.operator_runtime_cli._run_release",
        denied_release,
    )
    payload = submit(
        config,
        REPO_ROOT / "samples" / "tasks" / "external_email_send.json",
    )
    assert payload["guardian_status"] == "deny"
    assert payload["lima_called"] is False
    assert payload["ollama_called"] is False
    assert payload["network_called"] is False
    assert payload["execution_allowed"] is False
    assert JsonlApprovalStore(config.paths.approval_path).list_approvals()[0].execution_allowed is False


def test_windows_scripts_do_not_add_firewall_or_non_loopback_listeners() -> None:
    script_root = REPO_ROOT / "scripts" / "windows"
    text = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in script_root.glob("*.ps1")
    )
    assert "new-netfirewallrule" not in text
    assert "netsh advfirewall" not in text
    assert "0.0.0.0:" not in text
    assert "/rl highest" not in text
    assert "ollama uninstall" not in text
    assert "ollama rm" not in text


@pytest.mark.skipif(os.name != "nt", reason="PowerShell parser check is Windows-only")
def test_windows_scripts_parse() -> None:
    scripts = sorted((REPO_ROOT / "scripts" / "windows").glob("*.ps1"))
    command = (
        "$ErrorActionPreference='Stop'; "
        + "; ".join(
            f"[scriptblock]::Create((Get-Content -Raw -LiteralPath '{path}')) | Out-Null"
            for path in scripts
        )
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
