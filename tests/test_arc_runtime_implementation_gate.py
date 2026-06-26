"""Runtime implementation gate request and response tests."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

from phase12_mvp_completion.completion import RUNTIME_DEPENDENCIES
from phase12_mvp_completion.runtime_implementation_gate import (
    RUNTIME_IMPLEMENTATION_GATE_DECISION_FIELD,
    RUNTIME_IMPLEMENTATION_GATE_PACKET_REF,
    RUNTIME_IMPLEMENTATION_GATE_REQUEST_REF,
    RUNTIME_IMPLEMENTATION_GATE_RESPONSE_REQUIRED_FIELDS,
    RUNTIME_IMPLEMENTATION_GATE_RESPONSE_SCHEMA_REF,
    RUNTIME_IMPLEMENTATION_GATE_RESPONSE_TEMPLATE_REF,
    build_arc_runtime_implementation_gate_request_projection,
    build_arc_runtime_implementation_gate_response_projection,
    run_arc_runtime_implementation_gate_request_preview,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / RUNTIME_IMPLEMENTATION_GATE_RESPONSE_SCHEMA_REF
TEMPLATE_PATH = REPO_ROOT / RUNTIME_IMPLEMENTATION_GATE_RESPONSE_TEMPLATE_REF

COMPLETE_APPROVED_RESPONSE = {
    RUNTIME_IMPLEMENTATION_GATE_DECISION_FIELD: {
        "decision": "approved",
        "approving_owner": "LIMA Office runtime gate board",
        "approved_dependencies": list(RUNTIME_DEPENDENCIES),
        "rejected_or_deferred_dependencies": [],
        "required_contract_refs": ["contract://lima-office/runtime-gate/example"],
        "required_schema_refs": ["schema://lima-office/runtime-gate/example"],
        "required_test_gates": ["python -m pytest -q"],
        "explicit_runtime_limits": ["single_tenant", "guardian_required"],
        "evidence_writer_authority": "LIMA Office Supervisor evidence plane",
        "local_model_executor_authority": "LIMA Office Guardian plane",
        "operator_console_state_authority": "LIMA Office operator-console plane",
        "effective_after_commit_or_packet_ref": "packet://example/runtime-gate-approval",
    }
}


def test_runtime_implementation_gate_request_is_blocked() -> None:
    projection = build_arc_runtime_implementation_gate_request_projection()

    assert projection["artifact_type"] == "arc_runtime_implementation_gate_request_projection"
    assert projection["status"] == "awaiting_runtime_implementation_gate_approval"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["mvp_complete"] is False
    assert projection["production_ready"] is False
    assert projection["requires_external_owner_input"] is False
    assert projection["requires_runtime_implementation_gate_approval"] is True
    assert projection["response_schema_ref"] == RUNTIME_IMPLEMENTATION_GATE_RESPONSE_SCHEMA_REF
    assert projection["response_template_ref"] == RUNTIME_IMPLEMENTATION_GATE_RESPONSE_TEMPLATE_REF


def test_runtime_implementation_gate_covers_all_runtime_dependencies() -> None:
    projection = build_arc_runtime_implementation_gate_request_projection()
    approval_ids = {item["dependency_id"] for item in projection["approval_areas"]}

    assert set(projection["requested_runtime_dependencies"]) == set(RUNTIME_DEPENDENCIES)
    assert set(projection["blocking_runtime_dependencies"]) == set(RUNTIME_DEPENDENCIES)
    assert approval_ids == set(RUNTIME_DEPENDENCIES)


def test_runtime_implementation_gate_blocks_execution_surfaces() -> None:
    projection = build_arc_runtime_implementation_gate_request_projection()
    blocked = set(projection["must_not_start_until_approved"])

    assert "live_supervisor_attachment" in blocked
    assert "approval_token_issuance_or_verification" in blocked
    assert "durable_evidence_write" in blocked
    assert "local_model_invocation" in blocked
    assert "connector_read_or_write" in blocked
    assert "customer_system_mutation" in blocked
    assert "external_message_send" in blocked
    assert "production_deployment" in blocked


def test_runtime_implementation_gate_response_defaults_to_awaiting_response() -> None:
    projection = build_arc_runtime_implementation_gate_response_projection()

    assert projection["artifact_type"] == "arc_runtime_implementation_gate_response_projection"
    assert projection["status"] == "awaiting_or_incomplete_runtime_implementation_gate_response"
    assert projection["response_shape_complete"] is False
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["mvp_complete"] is False
    assert projection["production_ready"] is False
    assert set(projection["missing_response_fields"]) == set(
        RUNTIME_IMPLEMENTATION_GATE_RESPONSE_REQUIRED_FIELDS
    )


def test_runtime_implementation_gate_response_complete_shape_still_blocks_runtime() -> None:
    projection = build_arc_runtime_implementation_gate_response_projection(
        COMPLETE_APPROVED_RESPONSE
    )

    assert projection["status"] == "response_shape_complete_runtime_still_blocked"
    assert projection["response_shape_complete"] is True
    assert projection["decision_allowed"] is True
    assert projection["approved_dependencies_complete"] is True
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert "local_model_invocation" in projection["must_not_implement_from_response_alone"]


def test_runtime_implementation_gate_response_template_is_blank_and_blocked() -> None:
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))

    assert set(template) == {RUNTIME_IMPLEMENTATION_GATE_DECISION_FIELD}
    assert set(template[RUNTIME_IMPLEMENTATION_GATE_DECISION_FIELD]) == set(
        RUNTIME_IMPLEMENTATION_GATE_RESPONSE_REQUIRED_FIELDS
    )

    projection = build_arc_runtime_implementation_gate_response_projection(template)
    assert projection["response_shape_complete"] is False
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True


def test_runtime_implementation_gate_response_schema_matches_required_fields() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    decision_schema = schema["properties"][RUNTIME_IMPLEMENTATION_GATE_DECISION_FIELD]

    assert schema["$id"] == "schema://arc-bot/runtime-implementation-gate-response"
    assert schema["additionalProperties"] is False
    assert schema["required"] == [RUNTIME_IMPLEMENTATION_GATE_DECISION_FIELD]
    assert decision_schema["additionalProperties"] is False
    assert decision_schema["required"] == list(
        RUNTIME_IMPLEMENTATION_GATE_RESPONSE_REQUIRED_FIELDS
    )


def test_runtime_implementation_gate_docs_exist_and_reference_posture() -> None:
    request_path = REPO_ROOT / RUNTIME_IMPLEMENTATION_GATE_REQUEST_REF
    packet_path = REPO_ROOT / RUNTIME_IMPLEMENTATION_GATE_PACKET_REF

    request = request_path.read_text(encoding="utf-8")
    packet = packet_path.read_text(encoding="utf-8")

    assert request_path.exists()
    assert packet_path.exists()
    assert "runtime_authority_blocked = true" in request
    assert "runtime_execution_blocked = true" in request
    assert RUNTIME_IMPLEMENTATION_GATE_RESPONSE_SCHEMA_REF in request
    assert RUNTIME_IMPLEMENTATION_GATE_RESPONSE_TEMPLATE_REF in request
    assert "tests/test_arc_runtime_implementation_gate.py" in packet


def test_runtime_implementation_gate_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_arc_runtime_implementation_gate_request_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_id"] == "arc_runtime_implementation_gate_request_v1"
    assert parsed["runtime_execution_blocked"] is True


def test_runtime_implementation_gate_cli_accepts_response_path(tmp_path: Path) -> None:
    response_path = tmp_path / "runtime_gate_response.json"
    response_path.write_text(json.dumps(COMPLETE_APPROVED_RESPONSE), encoding="utf-8")

    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_arc_runtime_implementation_gate_request_preview(
            ["--response-path", str(response_path), "--compact"]
        )

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_id"] == "arc_runtime_implementation_gate_response_v1"
    assert parsed["response_shape_complete"] is True
    assert parsed["runtime_authority_blocked"] is True
    assert parsed["runtime_execution_blocked"] is True
