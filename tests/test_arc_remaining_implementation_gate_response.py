"""Remaining implementation-gate response inspection tests."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

from phase7_approval_evidence.remaining_gate_response import (
    build_remaining_implementation_gate_response_projection,
    run_remaining_implementation_gate_response_preview,
)


COMPLETE_RESPONSE = {
    "operator_console_server_state_owner": {
        "owner": "LIMA Office Guardian/Supervisor",
        "canonical_contract_family": "operator.console.state",
        "authoritative_fields": ["approval_queue", "operator_decision"],
        "arc_bot_may_consume": ["state_refs", "verifier_result_refs"],
        "arc_bot_must_not_do": ["own_authoritative_state"],
    },
    "guardian_owned_local_model_executor_boundary": {
        "owner": "LIMA Runtime Guardian Model Harness",
        "canonical_contract_family": "guardian.local_model.executor",
        "required_guardian_inputs": ["approval_token_id", "redaction_policy_ref"],
        "required_verifier_evidence_outputs": ["verifier_result_ref", "evidence_ref"],
        "arc_bot_may_consume": ["preview_result_refs"],
        "arc_bot_must_not_do": ["invoke_model_directly"],
    },
}


def test_remaining_gate_response_projection_defaults_to_awaiting_response() -> None:
    projection = build_remaining_implementation_gate_response_projection()

    assert projection["artifact_type"] == "arc_remaining_implementation_gate_response_projection"
    assert projection["status"] == "awaiting_or_incomplete_external_owner_response"
    assert projection["response_shape_complete"] is False
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert {
        "operator_console_server_state_owner",
        "guardian_owned_local_model_executor_boundary",
    } == set(projection["unresolved_external_dependencies"])


def test_remaining_gate_response_complete_shape_still_blocks_runtime() -> None:
    projection = build_remaining_implementation_gate_response_projection(COMPLETE_RESPONSE)

    assert projection["status"] == "response_shape_complete_runtime_still_blocked"
    assert projection["response_shape_complete"] is True
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["unresolved_external_dependencies"] == []
    assert "local_model_invocation" in projection["must_not_implement_from_response_alone"]
    assert "operator_console_state_authority" in projection["must_not_implement_from_response_alone"]


def test_remaining_gate_response_reports_missing_fields() -> None:
    projection = build_remaining_implementation_gate_response_projection(
        {
            "operator_console_server_state_owner": {
                "owner": "LIMA Office Guardian/Supervisor",
            }
        }
    )

    missing = projection["missing_response_fields"]
    assert "canonical_contract_family" in missing["operator_console_server_state_owner"]
    assert "owner" in missing["guardian_owned_local_model_executor_boundary"]


def test_remaining_gate_response_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_remaining_implementation_gate_response_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_id"] == "arc_remaining_implementation_gate_response_v1"
    assert parsed["runtime_execution_blocked"] is True
