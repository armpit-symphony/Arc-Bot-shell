"""Remaining implementation-gate response inspection tests."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

from phase7_approval_evidence.remaining_gate_response import (
    REMAINING_GATE_RESPONSE_REQUIRED_FIELDS,
    REMAINING_GATE_RESPONSE_SCHEMA_REF,
    REMAINING_GATE_RESPONSE_TEMPLATE_REF,
    build_remaining_implementation_gate_response_projection,
    run_remaining_implementation_gate_response_preview,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / REMAINING_GATE_RESPONSE_SCHEMA_REF
TEMPLATE_PATH = REPO_ROOT / REMAINING_GATE_RESPONSE_TEMPLATE_REF

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
    assert projection["response_schema_ref"] == REMAINING_GATE_RESPONSE_SCHEMA_REF
    assert projection["response_template_ref"] == REMAINING_GATE_RESPONSE_TEMPLATE_REF
    assert projection["source_access_mode"] == "read_only"
    assert projection["inspection_mode"] == "local_json_inspection_only"
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


def test_remaining_gate_response_schema_matches_required_fields() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert schema["$id"] == "schema://arc-bot/remaining-implementation-gate-response"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(REMAINING_GATE_RESPONSE_REQUIRED_FIELDS)

    for dependency_id, required_fields in REMAINING_GATE_RESPONSE_REQUIRED_FIELDS.items():
        dependency_schema = schema["properties"][dependency_id]
        assert dependency_schema["additionalProperties"] is False
        assert dependency_schema["required"] == list(required_fields)


def test_remaining_gate_response_template_is_blank_and_runtime_blocked() -> None:
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))

    assert set(template) == set(REMAINING_GATE_RESPONSE_REQUIRED_FIELDS)
    for dependency_id, required_fields in REMAINING_GATE_RESPONSE_REQUIRED_FIELDS.items():
        assert set(template[dependency_id]) == set(required_fields)

    projection = build_remaining_implementation_gate_response_projection(template)
    assert projection["response_shape_complete"] is False
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert set(projection["unresolved_external_dependencies"]) == set(
        REMAINING_GATE_RESPONSE_REQUIRED_FIELDS
    )


def test_remaining_gate_response_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_remaining_implementation_gate_response_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_id"] == "arc_remaining_implementation_gate_response_v1"
    assert parsed["runtime_execution_blocked"] is True


def test_remaining_gate_response_cli_accepts_response_path(tmp_path: Path) -> None:
    response_path = tmp_path / "owner_response.json"
    response_path.write_text(json.dumps(COMPLETE_RESPONSE), encoding="utf-8")

    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_remaining_implementation_gate_response_preview(
            ["--response-path", str(response_path), "--compact"]
        )

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["response_shape_complete"] is True
    assert parsed["runtime_authority_blocked"] is True
    assert parsed["runtime_execution_blocked"] is True