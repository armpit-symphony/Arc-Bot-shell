"""Arc Guardian/Spine base contract tests."""

from __future__ import annotations

import json
import subprocess
import sys

from arc_guardian_spine import (
    ARC_ALLOWED_TOOL_PACKS,
    ArcActionRequest,
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

    model = projection["local_model_seat"]
    assert model["provider_kind"] == "local_model"
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

    event = projection["spine_event"]
    assert event["event_type"] == "guardian_decision_projected"
    assert event["persistence_mode"] == "projection_only"
    assert event["guardian_decision_ref"] == decision["decision_id"]


def test_arc_runtime_actions_deny_until_runtime_gate() -> None:
    for action_kind in (
        "local_model_call",
        "connector_action",
        "customer_record_mutation",
        "external_send",
        "runtime_tool_execution",
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
