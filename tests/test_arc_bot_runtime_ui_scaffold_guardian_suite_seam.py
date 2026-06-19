"""Fixture-driven Guardian Suite read seam validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from phase0_runtime_ui_scaffold import guardian_suite_seam as seam


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATH = REPO_ROOT / "tests" / "fixtures" / "arc_bot_guardian_suite_spine_payload.json"


def _load_payload() -> dict[str, object]:
    payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_guardian_suite_spine_projection_builds_readonly_summary() -> None:
    projection = seam.build_guardian_suite_seam_projection(payload_path=PAYLOAD_PATH)

    assert projection["artifact_type"] == "guardian_suite_spine_projection"
    assert projection["api_status"] == "CANDIDATE_ONLY"
    assert projection["phase"] == "phase-1"
    assert projection["projection_scope"] == "read_only"
    assert projection["source_reference"] == "app.services.guardian.suite"
    assert projection["source_access_mode"] == "read_only"
    assert projection["runtime_authority_enabled"] is False
    assert projection["runtime_authority_required_for_execution"] is True
    assert projection["phase_gate"]["name"] == seam.EXPECTED_PHASE_GATE_NAME
    assert projection["phase_gate"]["required"] is True
    assert projection["phase_gate"]["enabled"] is True
    assert projection["phase_gate"]["flag"] == seam.EXPECTED_PHASE_GATE_FLAG
    assert projection["spine_record_counts"] == {
        "guardian_spine_tasks": 3,
        "guardian_spine_events": 2,
        "guardian_spine_approvals": 2,
        "guardian_spine_projects": 2,
    }
    assert set(projection["surfaces"]) == {
        "overview",
        "runtime_settings",
        "work_queue",
    }


def test_guardian_suite_spine_projection_rejects_missing_required_source(tmp_path: Path) -> None:
    payload = _load_payload()
    payload = dict(payload)
    payload["spine_sources"] = ["guardian_spine_tasks", "guardian_spine_events"]

    with pytest.raises(seam.GuardianSuitePayloadError):
        seam.build_guardian_suite_seam_projection(payload_path=_write_temp_payload(tmp_path, payload))


def test_guardian_suite_spine_projection_rejects_runtime_authority_enabled(tmp_path: Path) -> None:
    payload = _load_payload()
    payload["runtime_authority_enabled"] = True

    with pytest.raises(seam.GuardianSuitePayloadError):
        seam.build_guardian_suite_seam_projection(payload_path=_write_temp_payload(tmp_path, payload))


def test_guardian_suite_spine_projection_rejects_wrong_source_reference(tmp_path: Path) -> None:
    payload = _load_payload()
    payload["source_reference"] = "bad.service.reference"

    with pytest.raises(seam.GuardianSuitePayloadError):
        seam.build_guardian_suite_seam_projection(payload_path=_write_temp_payload(tmp_path, payload))


def test_guardian_suite_spine_projection_rejects_unknown_projection_gate(tmp_path: Path) -> None:
    payload = _load_payload()
    payload["phase_gate_name"] = "RUNTIME_UI_BAD_GATE"

    with pytest.raises(seam.GuardianSuiteGateError):
        seam.build_guardian_suite_seam_projection(
            payload_path=_write_temp_payload(tmp_path, payload),
            expected_gate_name=seam.EXPECTED_PHASE_GATE_NAME,
        )


def test_guardian_suite_seam_preview_has_compact_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    status = seam.run_guardian_suite_seam_preview([str(PAYLOAD_PATH), "--compact"])

    assert status == 0
    output = json.loads(capsys.readouterr().out)
    assert output["artifact_type"] == "guardian_suite_spine_projection"
    assert output["phase_gate"]["name"] == seam.EXPECTED_PHASE_GATE_NAME


def _write_temp_payload(tmp_path: Path, payload: dict[str, object]) -> str:
    temp_path = tmp_path / "arc_bot_guardian_suite_spine_payload_tmp.json"
    temp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return str(temp_path)
