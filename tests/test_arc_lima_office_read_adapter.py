"""Arc-to-LIMA Office read adapter contract tests."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest

from arc_guardian_spine import ArcActionRequest
from phase6_lima_office_integration.read_adapter import (
    ArcLimaOfficeReadAdapterError,
    build_arc_lima_office_read_adapter_projection,
    run_arc_lima_office_read_adapter_preview,
)


def test_arc_lima_office_read_adapter_exports_read_only_state() -> None:
    projection = build_arc_lima_office_read_adapter_projection()

    assert projection["artifact_type"] == "arc_lima_office_read_adapter_projection"
    assert projection["phase"] == "phase-6-read-adapter-contract"
    assert projection["projection_scope"] == "read_only"
    assert projection["source_access_mode"] == "read_only"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["connector_actions_allowed"] is False
    assert projection["customer_system_mutation_allowed"] is False
    assert projection["external_send_allowed"] is False
    assert projection["local_model_execution_allowed"] is False

    target = projection["lima_office_target"]
    assert target["target_contract"] == "RuntimeStateSnapshot"
    assert target["live_lima_imports_used"] is False
    assert target["supervisor_owns_authoritative_state"] is True


def test_arc_lima_office_read_adapter_exports_expected_queues() -> None:
    projection = build_arc_lima_office_read_adapter_projection()
    queues = projection["queues"]

    assert len(queues["preview_queue"]) == 1
    assert len(queues["approval_required_queue"]) == 1
    assert len(queues["blocked_queue"]) == 1
    assert queues["preview_queue"][0]["decision"] == "allow_preview"
    assert queues["approval_required_queue"][0]["decision"] == "approval_required"
    assert queues["blocked_queue"][0]["decision"] == "deny"

    for queue_name in ("preview_queue", "approval_required_queue", "blocked_queue"):
        for entry in queues[queue_name]:
            assert entry["runtime_authority_blocked"] is True
            assert entry["runtime_execution_blocked"] is True
            assert entry["guardian_decision_ref"]
            assert entry["evidence_refs"]
            assert entry["policy_refs"]


def test_arc_lima_office_read_adapter_enforces_single_tenant_worker_topology() -> None:
    projection = build_arc_lima_office_read_adapter_projection()

    assert projection["deployment_topology"] == {
        "supervisor_servers": 1,
        "worker_min": 1,
        "worker_max": 8,
        "tenant_mode": "single_tenant",
    }
    assert projection["worker_status"]["heartbeat_posture"] == "projection_only_not_live"
    assert projection["worker_status"]["local_model_seat"]["cloud_fallback_allowed"] is False
    assert projection["worker_status"]["local_model_seat"]["network_egress_allowed"] is False


def test_arc_lima_office_read_adapter_rejects_empty_requests() -> None:
    with pytest.raises(ArcLimaOfficeReadAdapterError):
        build_arc_lima_office_read_adapter_projection(action_requests=())


def test_arc_lima_office_read_adapter_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_arc_lima_office_read_adapter_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_type"] == "arc_lima_office_read_adapter_projection"
    assert parsed["handoff_requirements"]["execution_allowed"] is False


def test_arc_lima_office_read_adapter_preserves_custom_request_boundaries() -> None:
    projection = build_arc_lima_office_read_adapter_projection(
        action_requests=(
            ArcActionRequest(
                action_id="arc-action-custom-blocked",
                action_kind="customer_record_mutation",
            ),
        )
    )

    assert projection["queues"]["preview_queue"] == []
    assert projection["queues"]["approval_required_queue"] == []
    assert projection["queues"]["blocked_queue"][0]["action_id"] == "arc-action-custom-blocked"
    assert projection["queues"]["blocked_queue"][0]["decision"] == "deny"
