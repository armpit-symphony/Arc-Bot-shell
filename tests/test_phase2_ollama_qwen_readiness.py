"""Tests for Phase-2 Ollama/Qwen local model readiness."""

from __future__ import annotations

import inspect
import io
import json
from pathlib import Path
from unittest.mock import patch

from phase0_runtime_ui_scaffold.basic_console import build_basic_guardian_console_projection
from phase2_local_model_readiness import readiness as readiness_module
from phase2_local_model_readiness import (
    DEFAULT_OLLAMA_ENDPOINT_LABEL,
    DEFAULT_QWEN_MODEL_ID,
    OllamaQwenHardwareProfile,
    OllamaQwenReadinessInput,
    build_ollama_qwen_readiness_projection,
    run_ollama_qwen_readiness_preview,
)


def test_ollama_qwen_readiness_defaults_to_setup_required_without_execution() -> None:
    projection = build_ollama_qwen_readiness_projection()

    assert projection["artifact_type"] == "phase2_ollama_qwen_readiness_projection"
    assert projection["phase"] == "phase-2"
    assert projection["runtime"] == "ollama"
    assert projection["runtime_choice"] == "ollama"
    assert projection["model_family"] == "qwen"
    assert projection["model_id"] == DEFAULT_QWEN_MODEL_ID
    assert projection["endpoint_label"] == DEFAULT_OLLAMA_ENDPOINT_LABEL
    assert projection["readiness_status"] == "setup_required"
    assert projection["connection_indicator"] == "red_attention"
    assert projection["missing_requirements"] == [
        "lima_office_worker_attachment",
        "ollama_install",
        "ollama_localhost_service",
        "qwen_model_pull",
    ]

    assert projection["model_invocation_performed"] is False
    assert projection["network_probe_performed"] is False
    assert projection["ollama_api_call_performed"] is False
    assert projection["provider_sdk_used"] is False
    assert projection["provider_credentials_required"] is False
    assert projection["credential_material_present"] is False
    assert projection["cloud_fallback_allowed"] is False
    assert projection["network_egress_allowed"] is False
    assert projection["runtime_execution_blocked"] is True
    assert projection["guardian_required_before_model_call"] is True


def test_ollama_qwen_readiness_ready_is_operator_attested_only() -> None:
    projection = build_ollama_qwen_readiness_projection(
        OllamaQwenReadinessInput(
            ollama_installed=True,
            ollama_service_reachable=True,
            qwen_model_present=True,
            lima_office_attached=True,
            hardware_profile=OllamaQwenHardwareProfile(
                cpu_threads=12,
                system_ram_gb=32,
                gpu_label="rtx-local",
                gpu_vram_gb=12,
                storage_free_gb=100,
            ),
        )
    )

    assert projection["readiness_status"] == "ready"
    assert projection["connection_indicator"] == "green_check"
    assert projection["missing_requirements"] == []
    assert projection["hardware_posture"]["cpu_ready"] is True
    assert projection["hardware_posture"]["memory_ready"] is True
    assert projection["hardware_posture"]["gpu_required"] is False
    assert projection["hardware_posture"]["storage_ready"] is True
    assert projection["model_invocation_performed"] is False
    assert projection["network_probe_performed"] is False


def test_ollama_qwen_readiness_blocks_non_ollama_or_non_qwen() -> None:
    projection = build_ollama_qwen_readiness_projection(
        OllamaQwenReadinessInput(
            runtime="llama_cpp",
            model_family="mistral",
            ollama_installed=True,
            ollama_service_reachable=True,
            qwen_model_present=True,
            lima_office_attached=True,
        )
    )

    assert projection["readiness_status"] == "blocked"
    assert "runtime_must_be_ollama" in projection["missing_requirements"]
    assert "model_family_must_be_qwen" in projection["missing_requirements"]
    assert projection["runtime_execution_blocked"] is True


def test_ollama_qwen_readiness_preview_cli_can_export(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "ollama_qwen_readiness.json"
    output = io.StringIO()

    with patch("sys.stdout", output):
        status = run_ollama_qwen_readiness_preview(
            [
                "--ollama-installed",
                "--ollama-service-reachable",
                "--qwen-model-present",
                "--lima-office-attached",
                "--compact",
                f"--snapshot-path={snapshot_path}",
            ]
        )

    assert status == 0
    cli_payload = json.loads(output.getvalue())
    file_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert cli_payload == file_payload
    assert cli_payload["readiness_status"] == "ready"
    assert cli_payload["model_invocation_performed"] is False


def test_readiness_module_has_no_live_probe_imports_or_execution_paths() -> None:
    source = inspect.getsource(readiness_module)

    forbidden_terms = [
        "import socket",
        "import subprocess",
        "import requests",
        "import urllib",
        "import http.client",
        "ollama.Client",
        "generate(",
        "chat(",
    ]
    for term in forbidden_terms:
        assert term not in source


def test_basic_console_embeds_ollama_qwen_readiness_projection() -> None:
    readiness = build_ollama_qwen_readiness_projection(
        OllamaQwenReadinessInput(
            ollama_installed=True,
            ollama_service_reachable=True,
            qwen_model_present=True,
            lima_office_attached=True,
        )
    )
    projection = build_basic_guardian_console_projection(local_model_readiness=readiness)

    assert projection["connections"]["local_model"]["status"] == "connected"
    assert projection["connections"]["local_model"]["indicator"] == "green_check"
    assert projection["local_model_readiness"]["runtime"] == "ollama"
    assert projection["local_model_readiness"]["model_family"] == "qwen"
    assert projection["local_model_readiness"]["model_invocation_performed"] is False
