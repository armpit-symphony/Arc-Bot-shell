"""Arc Guardian/Spine base contract tests."""

from __future__ import annotations

import json
import subprocess
import sys

from arc_guardian_spine import (
    ARC_ALLOWED_TOOL_PACKS,
    ArcActionRequest,
    ArcSpineEvent,
    ArcSpineLedger,
    build_arc_guardian_spine_base,
    evaluate_arc_action,
)


def test_arc_guardian_spine_base_is_local_model_only_and_fail_closed() -> None:
    projection = build_arc_guardian_spine_base()

    assert projection["artifact_type"] == "arc_guardian_spine_base_projection"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["local_model_only"] is True
    assert projection["cloud_fallback_allowed"] is False
    assert projection["connector_actions_allowed"] is False
    assert projection["customer_system_mutation_allowed"] is False
    assert projection["allowed_tool_packs"] == list(ARC_ALLOWED_TOOL_PACKS)
    assert projection["approval_request"] is None

    model = projection["local_model_seat"]
    assert model["provider_kind"] == "local_model"
    assert model["runtime"] == "ollama"
    assert model["model_id"] == "qwen2.5:7b"
    assert model["lima_office_attached"] is True
    assert model["cloud_fallback_allowed"] is False
    assert model["network_egress_allowed"] is False
    assert model["credential_required"] is False


def test_arc_document_intake_preview_allows_preview_only() -> None:
    request = ArcActionRequest(
        action_id="arc-action-test-intake",
        action_kind="document_intake_preview",
    )
    decision = evaluate_arc_action(request)

    assert decision.decision == "allow_preview"
    assert decision.approval_required is False
    assert decision.runtime_authority_blocked is True
    assert decision.runtime_execution_blocked is True
    assert decision.local_model_execution_blocked is True
    assert decision.evidence_refs
    assert decision.policy_refs


def test_arc_document_extract_preview_requires_guardian_approval() -> None:
    projection = build_arc_guardian_spine_base(
        ArcActionRequest(
            action_id="arc-action-test-extract",
            action_kind="document_extract_preview",
        )
    )

    decision = projection["guardian_decision"]
    assert decision["decision"] == "approval_required"
    assert decision["reason_code"] == "local_model_preview_requires_guardian_approval"
    assert decision["approval_required"] is True
    assert decision["local_model_execution_blocked"] is True

    approval = projection["approval_request"]
    assert approval["approval_id"] == "approval-request:arc-action-test-extract"
    assert approval["status"] == "pending"
    assert approval["reusable"] is False
    assert approval["grants_runtime_execution"] is False
    assert approval["grants_local_model_execution"] is False
    assert approval["policy_refs"]
    assert approval["evidence_refs"]

    event = projection["spine_event"]
    assert event["event_type"] == "guardian_decision_projected"
    assert event["persistence_mode"] == "projection_only"
    assert event["guardian_decision_ref"] == decision["decision_id"]
    assert event["guardian_decision_result"] == "approval_required"

    ledger = projection["spine_ledger"]
    assert ledger["persistence_mode"] == "projection_only"
    assert ledger["recent_events"] == [event]
    assert ledger["blocked_actions"] == []
    assert ledger["approval_required_actions"] == [event]


def test_arc_runtime_actions_deny_until_runtime_gate() -> None:
    for action_kind in (
        "local_model_call",
        "connector_request",
        "connector_action",
        "customer_record_mutation",
        "external_send",
        "runtime_tool_execution",
        "admin_remediation",
    ):
        decision = evaluate_arc_action(
            ArcActionRequest(
                action_id=f"arc-action-test-{action_kind}",
                action_kind=action_kind,
            )
        )
        assert decision.decision == "deny"
        assert decision.runtime_authority_blocked is True
        assert decision.runtime_execution_blocked is True
        assert decision.local_model_execution_blocked is True


def test_arc_draft_and_export_actions_require_approval_not_execution() -> None:
    for action_kind in ("document_draft_generation", "document_export_request"):
        projection = build_arc_guardian_spine_base(
            ArcActionRequest(
                action_id=f"arc-action-test-{action_kind}",
                action_kind=action_kind,
            )
        )
        assert projection["guardian_decision"]["decision"] == "approval_required"
        assert projection["approval_request"]["reusable"] is False
        assert projection["approval_request"]["grants_runtime_execution"] is False
        assert projection["runtime_execution_blocked"] is True


def test_arc_evidence_refs_are_structured_and_redacted_only() -> None:
    projection = build_arc_guardian_spine_base()

    evidence_refs = projection["evidence_refs"]
    assert len(evidence_refs) >= 3
    for evidence_ref in evidence_refs:
        assert evidence_ref["required"] is True
        assert evidence_ref["raw_content_persisted"] is False
        assert evidence_ref["redacted_summary_only"] is True
        assert evidence_ref["ref_id"].startswith("evidence://")


def test_arc_spine_ledger_lists_recent_blocked_and_approval_required_events() -> None:
    blocked = ArcSpineEvent(
        event_id="spine-event:blocked",
        event_type="guardian_decision_projected",
        action_id="blocked",
        task_ref="task://arc/blocked",
        worker_id="arc-worker-001",
        tenant_id="single_tenant_local",
        guardian_decision_ref="guardian-decision:blocked",
        guardian_decision_result="deny",
        reason_code="blocked",
    )
    approval = ArcSpineEvent(
        event_id="spine-event:approval",
        event_type="guardian_decision_projected",
        action_id="approval",
        task_ref="task://arc/approval",
        worker_id="arc-worker-001",
        tenant_id="single_tenant_local",
        guardian_decision_ref="guardian-decision:approval",
        guardian_decision_result="approval_required",
        reason_code="approval_required",
    )
    ledger = ArcSpineLedger().append_planned_event(blocked).append_planned_event(approval)

    assert ledger.list_recent_events() == (blocked, approval)
    assert ledger.list_recent_events(limit=1) == (approval,)
    assert ledger.list_blocked_actions() == (blocked,)
    assert ledger.list_approval_required_actions() == (approval,)


def test_arc_tool_pack_scope_denies_unknown_pack() -> None:
    decision = evaluate_arc_action(
        ArcActionRequest(
            action_id="arc-action-test-tool-pack",
            action_kind="document_intake_preview",
            requested_tool_pack="browser",
        )
    )

    assert decision.decision == "deny"
    assert decision.reason_code == "tool_pack_not_allowed_for_arc_bot"


def test_arc_guardian_spine_preview_cli_outputs_projection() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_guardian_spine.preview",
            "--action-kind",
            "document_extract_preview",
            "--compact",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    projection = json.loads(result.stdout)

    assert projection["guardian_decision"]["decision"] == "approval_required"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
