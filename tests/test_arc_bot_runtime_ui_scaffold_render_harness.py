"""Tests for the Phase-0 read-only adapter render harness."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from phase0_runtime_ui_scaffold.adapter import (
    AdapterPayloadError,
    EXPECTED_SURFACES,
    PhaseGateError,
    build_phase0_readonly_projection,
)  # noqa: E402
ADAPTER_PAYLOAD_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "arc_bot_runtime_ui_scaffold_adapter_payload.json"
)
WORK_QUEUE_SNAPSHOT = (
    REPO_ROOT / "tests" / "fixtures" / "arc_bot_phase0_work_queue_state_snapshot.json"
)
RUNTIME_SETTINGS_SNAPSHOT = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_phase0_runtime_settings_state_snapshot.json"
)


def test_phase0_adapter_harness_renders_read_only_projection_for_expected_surfaces() -> None:
    rendered = build_phase0_readonly_projection(
        ADAPTER_PAYLOAD_PATH,
        enable_phase_gate=True,
        phase_gate_name="RUNTIME_UI_Scaffold",
    )

    assert rendered["payload_id"] == "arc_bot_runtime_ui_scaffold_readonly_adapter_v1"
    assert rendered["adapter_mode"] == "fixture_backed_read_only_projection"
    assert rendered["phase_gate"]["name"] == "RUNTIME_UI_Scaffold"
    assert rendered["phase_gate"]["enabled"] is True
    assert set(rendered["surfaces"].keys()) == EXPECTED_SURFACES

    for surface, surface_payload in rendered["surfaces"].items():
        assert surface_payload["surface"] == surface
        assert surface_payload["projection_mode"] == "read_only"
        assert surface_payload["runtime_authority_enforced"] is False
        assert surface_payload["phase_gate_required"] is True
        assert surface_payload["read_only_projection_only"] is True
        assert isinstance(surface_payload["allowed_metadata_actions"], list)
        assert isinstance(surface_payload["blocked_runtime_actions"], list)
        assert "tool_execution" in surface_payload["blocked_runtime_actions"]
        assert any(
            blocked_action.startswith("connector_")
            for blocked_action in surface_payload["blocked_runtime_actions"]
        )


def test_phase0_adapter_harness_blocks_projection_without_gate() -> None:
    with pytest.raises(PhaseGateError):
        build_phase0_readonly_projection(
            ADAPTER_PAYLOAD_PATH,
            enable_phase_gate=False,
            phase_gate_name="RUNTIME_UI_Scaffold",
        )


def test_phase0_adapter_harness_rejects_wrong_gate_name() -> None:
    with pytest.raises(PhaseGateError):
        build_phase0_readonly_projection(
            ADAPTER_PAYLOAD_PATH,
            enable_phase_gate=True,
            phase_gate_name="UNRECOGNIZED_GATE",
        )


def test_phase0_adapter_harness_rejects_snapshot_runtime_authority() -> None:
    temp_payload = (
        REPO_ROOT
        / "tests"
        / "fixtures"
        / "arc_bot_runtime_ui_scaffold_adapter_payload_breach_runtime.json"
    )
    temp_snapshot = (
        REPO_ROOT
        / "tests"
        / "fixtures"
        / "arc_bot_phase0_runtime_settings_state_snapshot_breach.json"
    )

    payload = json.loads(ADAPTER_PAYLOAD_PATH.read_text(encoding="utf-8"))
    runtime_payload = copy.deepcopy(payload)
    for entry in runtime_payload["surface_payloads"]:
        if entry["surface"] == "runtime_settings":
            entry["snapshot_file"] = str(temp_snapshot.relative_to(REPO_ROOT))

    runtime_snapshot = json.loads(
        RUNTIME_SETTINGS_SNAPSHOT.read_text(encoding="utf-8")
    )
    runtime_snapshot["live_model_inference_allowed"] = True

    try:
        temp_snapshot.write_text(
            json.dumps(runtime_snapshot, indent=2),
            encoding="utf-8",
        )
        temp_payload.write_text(
            json.dumps(runtime_payload, indent=2),
            encoding="utf-8",
        )

        with pytest.raises(AdapterPayloadError):
            build_phase0_readonly_projection(
                temp_payload,
                enable_phase_gate=True,
                phase_gate_name="RUNTIME_UI_Scaffold",
            )
    finally:
        for path in (temp_payload, temp_snapshot):
            if path.exists():
                path.unlink()


def test_phase0_adapter_harness_rejects_snapshot_with_runtime_exec_flags() -> None:
    work_queue_snapshot = json.loads(WORK_QUEUE_SNAPSHOT.read_text(encoding="utf-8"))
    tampered_snapshot = copy.deepcopy(work_queue_snapshot)
    tampered_snapshot["live_program_execution_allowed"] = True

    temp_snapshot = (
        REPO_ROOT
        / "tests"
        / "fixtures"
        / "arc_bot_phase0_work_queue_state_snapshot_breach.json"
    )
    temp_payload = (
        REPO_ROOT
        / "tests"
        / "fixtures"
        / "arc_bot_runtime_ui_scaffold_adapter_payload_breach_exec_flag.json"
    )

    backup_payload_path = (
        REPO_ROOT / "tests" / "fixtures" / "arc_bot_runtime_ui_scaffold_adapter_payload.json"
    )
    payload = json.loads(backup_payload_path.read_text(encoding="utf-8"))
    runtime_payload = copy.deepcopy(payload)
    for entry in runtime_payload["surface_payloads"]:
        if entry["surface"] == "work_queue":
            entry["snapshot_file"] = str(temp_snapshot.relative_to(REPO_ROOT))

    try:
        temp_snapshot.write_text(
            json.dumps(tampered_snapshot, indent=2),
            encoding="utf-8",
        )
        temp_payload.write_text(
            json.dumps(runtime_payload, indent=2),
            encoding="utf-8",
        )

        with pytest.raises(AdapterPayloadError):
            build_phase0_readonly_projection(
                temp_payload,
                enable_phase_gate=True,
                phase_gate_name="RUNTIME_UI_Scaffold",
            )
    finally:
        for path in (temp_payload, temp_snapshot):
            if path.exists():
                path.unlink()
