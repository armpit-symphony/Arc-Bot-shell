"""Narrow pilot readiness projection tests."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

from phase11_pilot_readiness.pilot import (
    PILOT_WORKFLOW_IDS,
    build_arc_pilot_readiness_projection,
    run_arc_pilot_readiness_preview,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pilot_readiness_is_read_only_and_runtime_blocked() -> None:
    projection = build_arc_pilot_readiness_projection()

    assert projection["artifact_type"] == "arc_narrow_pilot_readiness_projection"
    assert projection["phase"] == "phase-h-narrow-pilot-readiness"
    assert projection["projection_scope"] == "planning_read_only"
    assert projection["source_access_mode"] == "sanitized_metadata_only"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["production_ready"] is False
    assert projection["pilot_execution_allowed"] is False


def test_pilot_readiness_preserves_mvp_topology_and_sample_boundary() -> None:
    scope = build_arc_pilot_readiness_projection()["pilot_scope"]

    assert scope["tenant_mode"] == "single_tenant"
    assert scope["supervisor_servers"] == 1
    assert scope["worker_min"] == 1
    assert scope["worker_max"] == 8
    assert scope["sample_data_mode"] == "sanitized_local_samples_only"
    assert scope["live_customer_data_allowed"] is False


def test_pilot_readiness_uses_expected_phase5_workflows() -> None:
    projection = build_arc_pilot_readiness_projection()

    assert tuple(projection["workflow_ids"]) == PILOT_WORKFLOW_IDS
    assert tuple(preview["workflow_id"] for preview in projection["workflow_previews"]) == (
        "insurance_claim_packet_triage",
        "missing_information_checklist",
    )
    for preview in projection["workflow_previews"]:
        assert preview["preview_status"] == "draft_preview_ready"
        assert preview["draft_output"]["output_mode"] == "draft_preview_only"
        assert preview["model_invocation_performed"] is False
        assert preview["connector_action_performed"] is False
        assert preview["customer_system_mutation_performed"] is False
        assert preview["external_message_send_performed"] is False
        assert preview["runtime_execution_blocked"] is True


def test_pilot_readiness_referenced_docs_exist() -> None:
    projection = build_arc_pilot_readiness_projection()
    refs = projection["pilot_docs"] + [projection["external_dependency_ref"]]

    missing = [ref for ref in refs if not (REPO_ROOT / ref).exists()]
    assert not missing


def test_pilot_readiness_blocks_live_pilot_capabilities() -> None:
    blocked = set(build_arc_pilot_readiness_projection()["blocked_runtime_capabilities"])

    assert "raw_customer_document_processing" in blocked
    assert "local_model_invocation" in blocked
    assert "connector_read_or_write" in blocked
    assert "customer_record_update" in blocked
    assert "external_message_send" in blocked
    assert "durable_evidence_write" in blocked
    assert "approval_token_issuance_or_verification" in blocked


def test_pilot_readiness_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_arc_pilot_readiness_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_id"] == "arc_narrow_pilot_readiness_v1"
    assert parsed["pilot_execution_allowed"] is False
