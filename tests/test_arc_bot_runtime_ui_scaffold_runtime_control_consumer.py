"""Downstream runtime-control consumer seam for phase-2 UI state handoff."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest

from phase0_runtime_ui_scaffold.runtime_control_consumer import (
    Phase2RuntimeControlConsumerError,
    Phase2RuntimeControlConsumerShapeError,
    build_phase2_runtime_control_consumer_projection,
    run_runtime_control_consumer_preview,
)


def test_build_phase2_runtime_control_consumer_projection_happy_path() -> None:
    projection = build_phase2_runtime_control_consumer_projection()

    assert projection["artifact_type"] == "phase2_runtime_control_ui_consumer_projection"
    assert projection["phase"] == "phase-1"
    assert projection["projection_source"] == "phase2_runtime_control_handoff_projection"
    assert projection["projection_scope"] == "read_only"
    assert projection["source_reference"] == "app.services.guardian.suite"
    assert projection["source_access_mode"] == "read_only"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["phase_gate"]["name"] == "RUNTIME_UI_SCAFFOLD_PHASE1_FEED"
    assert projection["phase_gate"]["required"] is True
    assert projection["phase_gate"]["enabled"] is True
    assert set(projection["surface_bindings"]) == {
        "work_queue",
        "runtime_settings",
        "overview",
    }
    assert projection["surface_bindings"] == sorted(projection["surface_bindings"])

    for surface_projection in projection["surfaces"].values():
        assert surface_projection["downstream_mode"] == "read_only"
        assert surface_projection["ui_control_mode"] == "preview_only"
        assert surface_projection["control_state"] == "blocked_preview"
        assert surface_projection["projection_mode"] == "read_only"
        assert surface_projection["handoff_posture"] == "ui_state_handoff_read_only"
        assert surface_projection["runtime_authority_blocked"] is True
        assert surface_projection["runtime_execution_blocked"] is True
        assert surface_projection["runtime_execution_blocked"] is True
        assert set(surface_projection["blocked_runtime_actions"])
        assert set(surface_projection["spine_sources"]).issubset(
            set(projection["projection_bindings"])
        )

    assert projection["surface_summary"]["blocked_runtime_actions"]
    assert projection["consumer_metadata"]["consumer_mode"] == "read_only"
    assert projection["consumer_metadata"]["execution_allowed"] is False


def test_build_phase2_runtime_control_consumer_projection_rejects_disabled_gate() -> None:
    with patch(
        "phase0_runtime_ui_scaffold.runtime_control_consumer.build_phase2_runtime_control_projection"
    ) as build_control:
        build_control.return_value = {
        "artifact_type": "phase2_runtime_control_handoff_projection",
        "phase": "phase-1",
        "projection_scope": "read_only",
        "source_reference": "app.services.guardian.suite",
        "source_access_mode": "read_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "phase_gate": {"required": False, "enabled": False, "name": "RUNTIME_UI_SCAFFOLD_PHASE1_FEED"},
            "surfaces": {
                "work_queue": {
                    "projection_mode": "read_only",
                    "downstream_mode": "read_only",
                    "tenant_id": "tenant",
                    "customer_context_id": "customer",
                    "environment": "phase0_lab",
                    "operator_role": "operator",
                    "view_type": "work_queue",
                    "status": "review_required",
                    "policy_refs": [],
                    "evidence_refs": [],
                    "runbook_refs": [],
                    "contract_refs": ["task.execution"],
                    "spine_sources": ["guardian_spine_tasks"],
                    "metadata_actions": ["annotate_readiness_notes"],
                    "blocked_runtime_actions": ["dispatch_to_worker"],
                    "runtime_authority_blocked": True,
                    "runtime_execution_blocked": True,
                    "handoff_posture": "ui_control_handoff_read_only",
                }
            },
            "projection_bindings": ["guardian_spine_tasks"],
        }

        with pytest.raises(Phase2RuntimeControlConsumerError):
            build_phase2_runtime_control_consumer_projection()


def test_build_phase2_runtime_control_consumer_projection_rejects_execute_projection() -> None:
    projection = build_phase2_runtime_control_consumer_projection()
    projection["surfaces"]["work_queue"]["projection_mode"] = "execute"

    with patch(
        "phase0_runtime_ui_scaffold.runtime_control_consumer.build_phase2_runtime_control_projection"
    ) as build_control:
        build_control.return_value = projection
        with pytest.raises(Phase2RuntimeControlConsumerShapeError):
            build_phase2_runtime_control_consumer_projection()


def test_run_runtime_control_consumer_preview_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_runtime_control_consumer_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_type"] == "phase2_runtime_control_ui_consumer_projection"
    assert parsed["consumer_metadata"]["consumer_mode"] == "read_only"


def test_run_runtime_control_consumer_preview_cli_bad_payload_path() -> None:
    status = run_runtime_control_consumer_preview(
        [
            "--payload-path",
            "does_not_exist.json",
            "--compact",
        ]
    )
    assert status == 1
