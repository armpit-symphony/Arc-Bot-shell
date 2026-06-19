"""Tests for the Phase-0 runtime UI scaffold preview interface."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from phase0_runtime_ui_scaffold.adapter import (
    EXPECTED_SURFACES,
    PhaseGateError,
)
from phase0_runtime_ui_scaffold.preview import (
    DEFAULT_PAYLOAD_PATH,
    render_phase0_readonly_projection,
    run_preview,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PREVIEW_CONTRACT_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase0_preview_contract.json"
)


def _load_payload_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_render_phase0_readonly_projection_matches_preview_contract() -> None:
    rendered = render_phase0_readonly_projection(include_snapshot_payloads=True)
    contract = _load_payload_json(PREVIEW_CONTRACT_PATH)

    assert rendered["phase_gate"]["name"] == contract["phase_gate_name"]
    assert rendered["phase_gate"]["required"] == contract["phase_gate_required"]
    assert rendered["phase_gate"]["enabled"] is True
    assert set(rendered["surfaces"].keys()) == set(contract["surfaces"].keys())

    for surface_name, surface_contract in contract["surfaces"].items():
        rendered_surface = rendered["surfaces"][surface_name]
        rendered_snapshot = rendered["snapshots"][surface_name]
        snapshot_file = surface_contract["snapshot_file"]

        assert rendered_surface["surface"] == surface_name
        assert rendered_surface["projection_mode"] == surface_contract["projection_mode"]
        assert rendered_surface["runtime_authority_enforced"] is False
        assert rendered_surface["read_only_projection_only"] is True
        assert (
            set(surface_contract["required_envelope_status_modes"])
            == set(rendered_surface["required_envelope_status_modes"])
        )
        assert set(surface_contract["blocked_runtime_actions"]).issubset(
            set(rendered_surface["blocked_runtime_actions"])
        )
        assert rendered_surface["snapshot_source_file"] == snapshot_file
        assert rendered_snapshot["surface"] == surface_name

        for field in contract["shared_envelope_fields"]:
            assert (
                rendered_snapshot["envelope"][field]
                == contract["shared_envelope_fields"][field]
            )

        for field in surface_contract["snapshot_fields"]:
            assert field in rendered_snapshot or field in rendered_snapshot["envelope"]


def test_render_phase0_readonly_projection_defaults_to_expected_gate_and_surfaces() -> None:
    rendered = render_phase0_readonly_projection()

    assert set(rendered["surfaces"].keys()) == EXPECTED_SURFACES
    assert rendered["phase_gate"]["enabled"] is True
    assert rendered["phase_gate"]["name"] == "RUNTIME_UI_Scaffold"
    assert rendered["phase_gate"]["required"] is True
    assert rendered["surfaces"]["work_queue"]["projection_mode"] == "read_only"
    assert rendered["surfaces"]["runtime_settings"]["projection_mode"] == "read_only"
    assert rendered["surfaces"]["overview"]["projection_mode"] == "read_only"


def test_render_phase0_readonly_projection_defaults_match_payload_metadata() -> None:
    rendered = render_phase0_readonly_projection()
    fixture = _load_payload_json(DEFAULT_PAYLOAD_PATH)

    assert rendered["payload_id"] == fixture["payload_id"]
    assert rendered["adapter_phase"] == fixture["adapter_phase"]
    assert rendered["adapter_mode"] == fixture["adapter_mode"]


def test_render_phase0_preview_rejects_invalid_gate_name() -> None:
    with pytest.raises(PhaseGateError):
        render_phase0_readonly_projection(phase_gate_name="INVALID_GATE")


def test_run_preview_can_emit_compact_json_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    status = run_preview([str(DEFAULT_PAYLOAD_PATH), "--compact"])

    assert status == 0
    output = capsys.readouterr().out
    parsed = json.loads(output)

    assert set(parsed["surfaces"].keys()) == EXPECTED_SURFACES
    assert parsed["phase_gate"]["name"] == "RUNTIME_UI_Scaffold"


def test_run_preview_can_omit_snapshots(
    capsys: pytest.CaptureFixture[str],
) -> None:
    status = run_preview([str(DEFAULT_PAYLOAD_PATH), "--omit-snapshots", "--compact"])

    assert status == 0
    output = capsys.readouterr().out
    parsed = json.loads(output)

    assert "snapshots" not in parsed
    assert parsed["surface_bindings"]


def test_run_preview_handles_bad_payload_path() -> None:
    status = run_preview(["tests/fixtures/does_not_exist.json", "--compact"])
    assert status == 1


def test_run_preview_handles_invalid_phase_gate() -> None:
    status = run_preview([str(DEFAULT_PAYLOAD_PATH), "--phase-gate-name", "bad_gate"])
    assert status == 1


def test_run_preview_can_export_snapshot(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "phase0_preview_snapshot.json"
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_preview(
            [str(DEFAULT_PAYLOAD_PATH), "--compact", f"--snapshot-path={snapshot_path}"]
        )

    assert status == 0
    cli_payload = json.loads(output.getvalue())
    file_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert cli_payload == file_payload
