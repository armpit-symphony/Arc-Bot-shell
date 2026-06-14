"""Static checks for the Arc-Bot-shell LIMA V1-G7 proof packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_shell_lima_v1_g7_integration_proof_packet.json"
)


def _load_fixture() -> dict[str, Any]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(fixture, dict)
    return fixture


def test_arc_bot_shell_v1_g7_packet_files_exist() -> None:
    fixture = _load_fixture()
    assert fixture["proof_gap_id"] == "V1-G7"
    assert fixture["shell_repo"] == "Arc-Bot-shell"
    assert fixture["proof_branch"] == "v1-g7-arc-bot-shell-integration-proof-packet"

    for relative_path in fixture["proof_packet_files"]:
        assert (REPO_ROOT / relative_path).exists(), relative_path


def test_arc_bot_shell_v1_g7_runtime_boundaries_remain_false() -> None:
    fixture = _load_fixture()

    for key in (
        "can_consume_lima_runtime_outputs_live",
        "lima_runtime_wiring_added",
        "lima_runtime_behavior_added",
        "runtime_exports_required_from_lima",
        "runtime_exports_changed_in_lima",
        "lima_owns_haptic_device_behavior",
        "haptic_device_behavior_added",
        "device_haptic_command_added",
        "raw_natural_language_to_tool_execution_allowed",
        "sparkbot_code_copied_to_lima",
        "sparkbot_imported_by_lima",
        "lima_imported_by_shell_runtime",
        "production_readiness_claimed",
        "v1_product_readiness_claimed",
        "accepted_as_live_runtime_parity",
        "runtime_behavior_added",
        "provider_model_calls_added",
        "approval_enforcement_added",
        "guardian_decision_runtime_added",
        "audit_persistence_added",
        "connector_behavior_added",
        "file_browser_network_device_robotics_behavior_added",
        "physical_world_behavior_added",
        "runtime_export_cleanup_approved",
        "final_freeze_approved",
    ):
        assert fixture[key] is False

    assert fixture["can_consume_lima_contract_outputs_as_static_evidence"] is True
    assert fixture["accepted_as_static_shell_evidence"] is True


def test_arc_bot_shell_v1_g7_state_coverage_is_static_only() -> None:
    fixture = _load_fixture()
    required_states = {
        "received",
        "thinking",
        "preview_ready",
        "blocked",
        "needs_approval",
        "completed",
        "failed_safe",
        "deferred",
    }

    assert set(fixture["shell_response_states_evaluated"]) == required_states
    assert fixture["source_backed_shell_response_states"] == []
    assert set(fixture["docs_fixture_only_shell_response_states"]) == required_states
    assert fixture["missing_shell_response_states"] == []
    assert set(fixture["missing_runtime_behavior_states"]) == required_states


def test_arc_bot_shell_v1_g7_status_mapping_and_haptics() -> None:
    fixture = _load_fixture()

    assert fixture["kernel_status_mappings"]["proposed"] == "preview_only"
    assert fixture["kernel_status_mappings"]["needs_review"] == "explain_plan"
    assert fixture["kernel_status_mappings"]["blocked"] == "blocked"

    assert {"preview_only", "explain_plan", "blocked", "completed", "deferred"}.issubset(
        fixture["packet_statuses"]
    )
    assert fixture["currently_allowed_packet_statuses"] == [
        "preview_only",
        "explain_plan",
        "blocked",
        "deferred",
    ]
    assert fixture["completed_status_currently_runtime_backed"] is False

    assert fixture["haptic_intent_metadata_supported"] is False
    assert fixture["shell_owns_haptics"] is True
    assert fixture["lima_owns_haptic_device_behavior"] is False


def test_arc_bot_shell_v1_g7_approval_and_rejected_claims() -> None:
    fixture = _load_fixture()

    assert fixture["destructive_edit_delete_requires_operator_approval"] is True
    assert (
        fixture["destructive_edit_delete_current_behavior"]
        == "blocked_until_future_operator_approval_and_guardian_gate"
    )
    assert fixture["approval_enforcement_status"] == "docs_only_blocked_no_real_enforcement"
    assert fixture["guardian_decision_status"] == "docs_only_future_required_missing_real_authority"
    assert fixture["provider_model_routing_status"] == (
        "absent_docs_only_blocked_no_provider_model_routing"
    )
    assert fixture["audit_evidence_status"] == "static_only_reference_based_no_durable_persistence"
    assert fixture["connector_file_browser_network_device_robotics_status"] == (
        "absent_or_blocked_docs_only_no_runtime_behavior"
    )

    rejected = set(fixture["rejected_claims"])
    assert "live_lima_runtime_parity" in rejected
    assert "runtime_source_backed_arc_shell_behavior" in rejected
    assert "real_approval_enforcement" in rejected
    assert "real_guardian_decision_authority" in rejected
    assert "provider_model_routing" in rejected
    assert "runtime_export_cleanup_approval" in rejected
    assert "final_api_freeze" in rejected
