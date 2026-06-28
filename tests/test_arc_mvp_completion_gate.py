"""Phase-12 MVP completion gate tests."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

from phase12_mvp_completion.completion import (
    build_arc_mvp_completion_gate_projection,
    run_arc_mvp_completion_gate_preview,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_mvp_completion_gate_does_not_claim_completion() -> None:
    projection = build_arc_mvp_completion_gate_projection()

    assert projection["artifact_type"] == "arc_mvp_completion_gate_projection"
    assert projection["phase"] == "phase-12-mvp-completion-gate"
    assert projection["status"] == "not_complete_blocked_by_runtime_dependencies"
    assert projection["mvp_complete"] is False
    assert projection["production_ready"] is False
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["requires_external_owner_input"] is False
    assert projection["requires_runtime_implementation_gate_approval"] is True
    assert projection["lima_office_external_handoff"]["source_commit"].startswith("4e1ed0e")


def test_mvp_completion_gate_covers_all_roadmap_criteria() -> None:
    projection = build_arc_mvp_completion_gate_projection()
    criteria_ids = {item["criterion_id"] for item in projection["completion_criteria"]}

    assert projection["criteria_total"] == 10
    assert projection["criteria_blocked_or_runtime_pending"] > 0
    assert {
        "local_arc_worker_attached_to_lima_office",
        "approved_local_model_preview_only",
        "document_intake_and_guarded_drafts",
        "guardian_gates_every_consequential_action",
        "spine_records_task_decision_approval_evidence",
        "lima_office_reads_worker_status",
        "operators_can_approve_deny_block",
        "no_hidden_background_actions",
        "no_live_connector_writes",
        "no_production_claims",
    } == criteria_ids


def test_mvp_completion_gate_blocks_runtime_capabilities() -> None:
    projection = build_arc_mvp_completion_gate_projection()
    blocked = set(projection["must_not_implement_until_unblocked"])

    assert "live_supervisor_attachment" in blocked
    assert "local_model_invocation" in blocked
    assert "approval_token_issuance_or_verification" in blocked
    assert "durable_evidence_write" in blocked
    assert "connector_read_or_write" in blocked
    assert "customer_system_mutation" in blocked
    assert "external_message_send" in blocked
    assert "production_deployment" in blocked


def test_mvp_completion_gate_records_answered_and_remaining_dependencies() -> None:
    projection = build_arc_mvp_completion_gate_projection()

    assert {
        "approval_token_reference_format",
        "approval_binding_fields",
        "signature_replay_verification_owner",
        "runtime_state_snapshot_projection_boundary",
        "durable_evidence_writer_owner",
        "operator_console_server_state_owner",
        "guardian_owned_local_model_executor_boundary",
    } == set(projection["answered_external_dependencies"])
    assert projection["blocking_external_dependencies"] == []
    assert len(projection["blocking_runtime_dependencies"]) == 7


def test_mvp_completion_gate_referenced_evidence_exists() -> None:
    projection = build_arc_mvp_completion_gate_projection()
    refs = list(projection["evidence_refs"])
    for criterion in projection["completion_criteria"]:
        refs.extend(criterion["evidence_refs"])

    missing = []
    for ref in refs:
        path_ref = ref.split("#", 1)[0]
        if not (REPO_ROOT / path_ref).exists():
            missing.append(ref)

    assert not missing




def test_mvp_completion_gate_tracks_runtime_gate_response_intake() -> None:
    projection = build_arc_mvp_completion_gate_projection()
    refs = set(projection["evidence_refs"])

    assert "runtime_gate_response_intake" in projection["safe_current_outputs"]
    assert "docs/requests/ARC_BOT_RUNTIME_IMPLEMENTATION_GATE_REQUEST.md" in refs
    assert "docs/proof_packets/ARC_BOT_RUNTIME_IMPLEMENTATION_GATE_REQUEST_PACKET.md" in refs
    assert "docs/contracts/schemas/arc_runtime_implementation_gate_response.schema.json" in refs
    assert "docs/examples/arc_lima/runtime_implementation_gate_response.template.json" in refs

    readiness = (REPO_ROOT / "docs/readiness/ARC_BOT_MVP_COMPLETION_GATE.md").read_text(
        encoding="utf-8"
    )
    phase_i_packet = (
        REPO_ROOT / "docs/proof_packets/ARC_BOT_PHASE_I_MVP_COMPLETION_GATE_PACKET.md"
    ).read_text(encoding="utf-8")
    roadmap = (REPO_ROOT / "docs/ROADMAP_ARC_BOT_COMPLETION.md").read_text(
        encoding="utf-8"
    )
    audit = (
        REPO_ROOT / "docs/audits/ARC_BOT_COMPLETION_AUDIT_AND_PHASE_PLAN.md"
    ).read_text(encoding="utf-8")

    for doc in (readiness, phase_i_packet, roadmap, audit):
        assert "docs/contracts/schemas/arc_runtime_implementation_gate_response.schema.json" in doc
        assert "docs/examples/arc_lima/runtime_implementation_gate_response.template.json" in doc
    assert "--response-path path\\to\\response.json --compact" in readiness
    assert "--response-path path\\to\\response.json --compact" in phase_i_packet

def test_mvp_completion_gate_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_arc_mvp_completion_gate_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_id"] == "arc_mvp_completion_gate_v1"
    assert parsed["mvp_complete"] is False
