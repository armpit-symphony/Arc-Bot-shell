"""Phase-2 runtime-control handoff preview seam for UI state."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest

from phase0_runtime_ui_scaffold.phase2_runtime_control import (
    Phase2RuntimeControlError,
    Phase2RuntimeControlShapeError,
    build_phase2_runtime_control_projection,
    run_phase2_runtime_control_preview,
)


def test_build_phase2_runtime_control_projection_happy_path() -> None:
    projected = build_phase2_runtime_control_projection()

    assert projected["artifact_type"] == "phase2_runtime_control_handoff_projection"
    assert projected["phase"] == "phase-1"
    assert projected["projection_scope"] == "read_only"
    assert projected["source_reference"] == "app.services.guardian.suite"
    assert projected["source_access_mode"] == "read_only"
    assert projected["runtime_authority_blocked"] is True
    assert projected["phase_gate"]["required"] is True
    assert projected["phase_gate"]["enabled"] is True
    assert projected["projection_source"] == "phase1_runtime_ui_consumer_projection"
    assert "work_queue" in projected["surface_bindings"]
    assert "runtime_settings" in projected["surface_bindings"]
    assert set(projected["surface_bindings"]) == set(projected["surfaces"].keys())

    for surface_projection in projected["surfaces"].values():
        assert surface_projection["downstream_mode"] == "read_only"
        assert surface_projection["projection_mode"] == "read_only"
        assert surface_projection["runtime_authority_blocked"] is True
        assert surface_projection["runtime_execution_blocked"] is True
        assert surface_projection["handoff_posture"] == "ui_control_handoff_read_only"
        assert set(surface_projection["blocked_runtime_actions"])
        assert set(surface_projection["contract_refs"])
        assert set(surface_projection["spine_sources"]).issubset(
            set(projected["projection_bindings"])
        )

    counts = projected["spine_source_record_counts"]
    assert counts["guardian_spine_tasks"] == 2
    assert counts["guardian_spine_events"] == 1
    assert counts["guardian_spine_approvals"] == 1
    assert counts["guardian_spine_projects"] == 1


def test_build_phase2_runtime_control_projection_rejects_disabled_gate() -> None:
    with patch(
        "phase0_runtime_ui_scaffold.phase2_runtime_control.build_phase1_runtime_ui_consumer_projection"
    ) as build_consumer:
        build_consumer.return_value = {
            "artifact_type": "phase1_runtime_ui_consumer_projection",
            "phase": "phase-1",
            "projection_scope": "read_only",
            "source_access_mode": "read_only",
            "source_reference": "app.services.guardian.suite",
            "runtime_authority_blocked": True,
            "spine_sources": [
                "guardian_spine_tasks",
                "guardian_spine_events",
            ],
            "spine_source_records": {},
            "phase_gate": {"required": False, "enabled": False, "name": "RUNTIME_UI_SCAFFOLD_PHASE1_FEED"},
            "surfaces": {
                "work_queue": {
                    "projection_mode": "read_only",
                    "tenant_id": "tenant",
                    "customer_context_id": "customer",
                    "environment": "phase0_lab",
                    "operator_role": "operator",
                    "view_type": "work_queue",
                    "status": "rendered",
                    "policy_refs": [],
                    "evidence_refs": [],
                    "runbook_refs": [],
                    "contract_refs": ["task.execution"],
                    "spine_sources": ["guardian_spine_tasks"],
                    "blocked_runtime_actions": ["dispatch_to_worker"],
                    "metadata_actions": ["annotate_readiness_notes"],
                }
            },
        }

        # This is gated by a required/active phase gate in phase-2 handoff.
        with pytest.raises(Phase2RuntimeControlError):
            build_phase2_runtime_control_projection()


def test_build_phase2_runtime_control_projection_rejects_execute_projection() -> None:
    projection = build_phase2_runtime_control_projection()
    projection["surfaces"]["work_queue"]["projection_mode"] = "execute"

    with patch(
        "phase0_runtime_ui_scaffold.phase2_runtime_control.build_phase1_runtime_ui_consumer_projection"
    ) as build_consumer:
        build_consumer.return_value = projection
        with pytest.raises(Phase2RuntimeControlShapeError):
            build_phase2_runtime_control_projection()


def test_run_phase2_runtime_control_preview_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_phase2_runtime_control_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_type"] == "phase2_runtime_control_handoff_projection"
    assert parsed["projection_source"] == "phase1_runtime_ui_consumer_projection"
    assert parsed["handoff_metadata"]["handoff_mode"] == "downstream_ui_state"


def test_run_phase2_runtime_control_preview_cli_bad_payload_path() -> None:
    status = run_phase2_runtime_control_preview(
        [
            "--payload-path",
            "does_not_exist.json",
            "--compact",
        ]
    )
    assert status == 1
