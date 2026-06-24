"""Phase-D approval/evidence dependency readiness tests."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

from phase7_approval_evidence.readiness import (
    build_arc_approval_evidence_dependency_projection,
    run_arc_approval_evidence_dependency_preview,
)


def test_arc_approval_evidence_dependency_projection_is_blocked() -> None:
    projection = build_arc_approval_evidence_dependency_projection()

    assert projection["artifact_type"] == "arc_phase_d_approval_evidence_dependency_projection"
    assert projection["status"] == "external_answers_recorded_runtime_still_blocked"
    assert projection["projection_scope"] == "planning_read_only"
    assert projection["source_access_mode"] == "read_only"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["requires_external_owner_input"] is True


def test_arc_approval_evidence_dependency_records_required_questions() -> None:
    projection = build_arc_approval_evidence_dependency_projection()
    dependency_ids = {
        answer["dependency_id"]
        for answer in projection["answered_external_dependencies"]
    }

    assert {
        "approval_token_reference_format",
        "approval_binding_fields",
        "signature_replay_verification_owner",
        "runtime_state_snapshot_canonical_fields",
        "durable_evidence_writer_boundary",
    }.issubset(dependency_ids)
    assert projection["lima_office_external_handoff"]["source_commit"].startswith("4e1ed0e")
    assert (
        "docs/requests/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_REQUEST.md"
        in projection["handoff_request_refs"]
    )
    assert "approval_token_issuance" in projection["blocked_capabilities"]
    assert "durable_evidence_writer" in projection["blocked_capabilities"]


def test_arc_approval_evidence_dependency_keeps_remaining_external_gates() -> None:
    projection = build_arc_approval_evidence_dependency_projection()

    assert {
        "operator_console_server_state_owner",
        "guardian_owned_local_model_executor_boundary",
    } == set(projection["unresolved_external_dependencies"])
    assert "durable_evidence_writer_implementation" in projection["runtime_implementation_blockers"]


def test_arc_approval_evidence_dependency_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_arc_approval_evidence_dependency_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_type"] == "arc_phase_d_approval_evidence_dependency_projection"
    assert parsed["requires_external_owner_input"] is True
    assert parsed["answered_external_dependencies"][0]["canonical_field"] == "approval_token_id"
