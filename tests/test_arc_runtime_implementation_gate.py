"""Runtime implementation gate request tests."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

from phase12_mvp_completion.completion import RUNTIME_DEPENDENCIES
from phase12_mvp_completion.runtime_implementation_gate import (
    RUNTIME_IMPLEMENTATION_GATE_PACKET_REF,
    RUNTIME_IMPLEMENTATION_GATE_REQUEST_REF,
    build_arc_runtime_implementation_gate_request_projection,
    run_arc_runtime_implementation_gate_request_preview,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


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


def test_runtime_implementation_gate_docs_exist_and_reference_posture() -> None:
    request_path = REPO_ROOT / RUNTIME_IMPLEMENTATION_GATE_REQUEST_REF
    packet_path = REPO_ROOT / RUNTIME_IMPLEMENTATION_GATE_PACKET_REF

    request = request_path.read_text(encoding="utf-8")
    packet = packet_path.read_text(encoding="utf-8")

    assert request_path.exists()
    assert packet_path.exists()
    assert "runtime_authority_blocked = true" in request
    assert "runtime_execution_blocked = true" in request
    assert "tests/test_arc_runtime_implementation_gate.py" in packet


def test_runtime_implementation_gate_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_arc_runtime_implementation_gate_request_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_id"] == "arc_runtime_implementation_gate_request_v1"
    assert parsed["runtime_execution_blocked"] is True
