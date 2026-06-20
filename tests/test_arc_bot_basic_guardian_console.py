"""Tests for the basic Guardian-gated Arc Bot console surface."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

from phase0_runtime_ui_scaffold.basic_console import (
    DEFAULT_HTML_PATH,
    build_basic_guardian_console_projection,
    run_basic_console_preview,
)


def test_basic_console_projection_defaults_to_disconnected_and_guarded() -> None:
    projection = build_basic_guardian_console_projection()

    assert projection["artifact_type"] == "arc_bot_basic_guardian_console_projection"
    assert projection["guardian_suite_boundary"] == "sparkbot_guardian_suite"
    assert projection["phase"] == "phase-1"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["local_model_only"] is True
    assert projection["cloud_fallback_allowed"] is False
    assert projection["local_model_readiness"]["runtime"] == "ollama"
    assert projection["local_model_readiness"]["model_family"] == "qwen"
    assert projection["local_model_readiness"]["model_invocation_performed"] is False
    assert projection["file_upload"]["document_intake_preview"]["phase"] == "phase-3"
    assert projection["file_upload"]["document_intake_preview"]["file_read_performed"] is False
    extraction = projection["file_upload"]["document_extraction_preview"]
    assert extraction["phase"] == "phase-4"
    assert extraction["extraction_status"] == "ready_for_review"
    assert extraction["file_read_performed"] is False
    assert extraction["model_invocation_performed"] is False
    assert extraction["runtime_execution_blocked"] is True

    local_model = projection["connections"]["local_model"]
    lima_office = projection["connections"]["lima_office"]
    assert local_model["status"] == "disconnected"
    assert local_model["indicator"] == "red_attention"
    assert local_model["connect_button_visible"] is True
    assert lima_office["status"] == "disconnected"
    assert lima_office["indicator"] == "red_attention"
    assert lima_office["connect_button_visible"] is True

    for connection in projection["connections"].values():
        assert connection["connect_action"]["guardian_required"] is True
        assert connection["connect_action"]["runtime_execution_blocked"] is True
        assert connection["connect_action"]["network_egress_blocked"] is True


def test_basic_console_projection_connected_states_show_green_check() -> None:
    projection = build_basic_guardian_console_projection(
        local_model_connected=True,
        lima_office_connected=True,
        self_learning_enabled=True,
    )

    assert projection["connections"]["local_model"]["status"] == "connected"
    assert projection["connections"]["local_model"]["indicator"] == "green_check"
    assert projection["connections"]["local_model"]["connect_button_visible"] is False
    assert projection["connections"]["lima_office"]["status"] == "connected"
    assert projection["connections"]["lima_office"]["indicator"] == "green_check"
    assert projection["self_learning"]["enabled"] is True
    assert projection["self_learning"]["automatic_memory_write_allowed"] is False
    assert projection["self_learning"]["cross_tenant_learning_allowed"] is False


def test_basic_console_surfaces_are_guardian_gated_and_no_execution() -> None:
    projection = build_basic_guardian_console_projection()

    assert projection["file_upload"]["raw_file_persistence_allowed"] is False
    assert projection["training"]["writes_memory_directly"] is False
    assert projection["chat"]["model_invocation_allowed"] is False

    for surface_name in ("file_upload", "training", "chat", "self_learning"):
        surface = projection[surface_name]
        assert surface["guardian_required"] is True
        assert surface["runtime_execution_blocked"] is True


def test_basic_console_preview_cli_exports_projection(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "basic_console_projection.json"
    output = io.StringIO()

    with patch("sys.stdout", output):
        status = run_basic_console_preview(
            [
                "--local-model-connected",
                "--lima-office-connected",
                "--ollama-qwen-ready",
                "--compact",
                f"--snapshot-path={snapshot_path}",
            ]
        )

    assert status == 0
    cli_payload = json.loads(output.getvalue())
    file_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert cli_payload == file_payload
    assert cli_payload["connections"]["local_model"]["status"] == "connected"
    assert cli_payload["connections"]["lima_office"]["status"] == "connected"
    assert cli_payload["local_model_readiness"]["readiness_status"] == "ready"
    assert cli_payload["static_html_path"] == str(DEFAULT_HTML_PATH)


def test_static_basic_console_html_contains_required_controls() -> None:
    html = DEFAULT_HTML_PATH.read_text(encoding="utf-8")

    required_ids = [
        'id="local-model-status"',
        'id="connect-local-model"',
        'id="ollama-qwen-readiness"',
        'id="ollama-qwen-model"',
        'id="ollama-qwen-endpoint"',
        'id="ollama-qwen-state"',
        'id="lima-office-status"',
        'id="connect-lima-office"',
        'id="file-upload-box"',
        'id="file-upload-input"',
        'id="document-intake-contract"',
        'id="document-extraction-contract"',
        'id="training-box"',
        'id="self-learning-toggle"',
        'id="chat-panel"',
        'id="chat-input"',
        'id="send-chat"',
    ]
    for required_id in required_ids:
        assert required_id in html

    assert 'data-guardian-action="connect-local-model"' in html
    assert 'data-guardian-action="connect-lima-office"' in html
    assert "qwen2.5:7b" in html
    assert "http://127.0.0.1:11434" in html
    assert "\\u2713" in html
    assert "No model call, connector action, file processing, training write" in html
    assert "Phase 3 intake accepts PDF, text, image scan, and Word metadata only" in html
    assert "Phase 4 extraction preview returns filename metadata" in html
    assert "<script src=" not in html
    assert "<form" not in html
