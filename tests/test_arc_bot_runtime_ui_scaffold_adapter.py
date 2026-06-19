"""Static checks for the Phase-0 runtime UI scaffold adapter payload and proof packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET_FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase0_adapter_packet.json"
)
PAYLOAD_FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_adapter_payload.json"
)
CONTRACT_PACK_FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_contract_pack.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(fixture, dict)
    return fixture


def _load_snapshot(path: str) -> dict[str, Any]:
    snapshot = json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(snapshot, dict)
    return snapshot


def test_arc_bot_runtime_ui_scaffold_phase0_adapter_packet_files_exist() -> None:
    packet = _load_json(PACKET_FIXTURE_PATH)

    assert packet["packet_id"] == "arc_bot_runtime_ui_scaffold_phase0_adapter_packet"
    assert packet["proof_gap_id"] == "PHASE-0-RUNTIME-UI-SCAFFOLD-ADAPTER"
    assert packet["api_status"] == "CANDIDATE_ONLY"
    assert packet["consumer_repo"] == "Arc-Bot-shell"
    assert packet["consumer_repository"] == "armpit-symphony/Arc-Bot-shell"
    assert packet["proof_branch"] == "arc-bot-runtime-ui-scaffold-readonly-adapter"
    assert packet["source_commit_before_branch"] == (
        "f11f726eebcae07f056421bd3ff46ee337c9f708"
    )
    assert packet["phase_gate_name"] == "RUNTIME_UI_Scaffold"

    for relative_path in packet["proof_packet_files"]:
        assert (REPO_ROOT / relative_path).exists(), relative_path

    for relative_path in packet["supporting_evidence_files"]:
        assert (REPO_ROOT / relative_path).exists(), relative_path


def test_arc_bot_runtime_ui_scaffold_adapter_payload_shape_is_phase0_readonly() -> None:
    payload = _load_json(PAYLOAD_FIXTURE_PATH)
    packet = _load_json(PACKET_FIXTURE_PATH)

    assert payload["payload_id"] == "arc_bot_runtime_ui_scaffold_readonly_adapter_v1"
    assert payload["adapter_mode"] == "fixture_backed_read_only_projection"
    assert payload["phase_gate_required"] is True
    assert payload["phase_gate_flag"] == "runtime_ui_scaffold_only_preview"
    assert payload["target_build_surface"] == "work_queue_and_runtime_settings"
    assert payload["adapter_phase"] == "phase-0"
    assert packet["requires_phase_gate"] is True
    assert payload["snapshot_schema_contracts"]
    assert payload["allowed_local_runtime_actions"] == [
        "annotate_readiness",
        "update_review_notes",
        "attach_runbook_ref",
    ]

    assert set(packet["adapter_surfaces"]) == {payload_entry["surface"] for payload_entry in payload["surface_payloads"]}  # noqa: E501

    required_surface_names = {"work_queue", "runtime_settings"}
    assert set(packet["adapter_surfaces"]) == required_surface_names
    assert set(payload["blocked_runtime_actions"]) >= {
        "provider_model_calls",
        "connector_reads",
        "connector_writes",
        "tool_execution",
        "runtime_route_mutation",
        "credential_storage",
        "customer_system_mutation",
    }


def test_arc_bot_runtime_ui_scaffold_adapter_matches_contract_pack() -> None:
    payload = _load_json(PAYLOAD_FIXTURE_PATH)
    packet = _load_json(PACKET_FIXTURE_PATH)
    contract_pack = _load_json(CONTRACT_PACK_FIXTURE_PATH)

    surface_bindings = contract_pack["contract_pack"]["surface_bindings"]
    binding_names = set(surface_bindings.keys())
    assert binding_names == {"work_queue", "runtime_settings"}

    payload_surfaces = {entry["surface"] for entry in payload["surface_payloads"]}
    assert payload_surfaces == binding_names

    for entry in payload["surface_payloads"]:
        surface = entry["surface"]
        assert surface in binding_names
        assert entry["snapshot_contract_binding"] == entry["schema"]
        assert entry["snapshot_file"] == surface_bindings[surface]["snapshot_file"]
        assert entry["schema"] == surface_bindings[surface]["schema"]
        assert entry["view_type"] == surface_bindings[surface]["view_type"]
        assert entry["runtime_authority_enforced_false"] is True
        assert entry["requires_phase_gate"] is True
        assert entry["read_only_projection_only"] is True
        assert isinstance(entry["blocked_runtime_actions"], list)


def test_arc_bot_runtime_ui_scaffold_adapter_snapshots_have_valid_shape() -> None:
    payload = _load_json(PAYLOAD_FIXTURE_PATH)

    for entry in payload["surface_payloads"]:
        snapshot = _load_snapshot(entry["snapshot_file"])

        assert snapshot["surface"] == entry["surface"]
        assert snapshot["display_state_only"] is True
        assert snapshot["envelope"]["view_type"] == entry["surface"]

        if entry["surface"] == "work_queue":
            assert snapshot["envelope"]["status"] in {"review_required", "blocked"}
            assert snapshot["live_program_execution_allowed"] is False
            assert snapshot["customer_system_mutation_allowed"] is False
            assert snapshot["external_message_send_allowed"] is False
        elif entry["surface"] == "runtime_settings":
            assert snapshot["envelope"]["status"] in {
                "rendered",
                "review_required",
                "degraded",
            }
            assert snapshot["live_model_inference_allowed"] is False
            assert snapshot["tool_execution_allowed"] is False
            assert snapshot["credential_storage_allowed"] is False
            assert snapshot["provider_token_storage_allowed"] is False
            assert snapshot["raw_runtime_payload_persistence_allowed"] is False
            assert snapshot["runtime_route_change_without_approval_allowed"] is False


def test_arc_bot_runtime_ui_scaffold_adapter_boundaries_remain_phase0() -> None:
    packet = _load_json(PACKET_FIXTURE_PATH)

    assert packet["adapter_runtime_authority_added"] is False
    assert packet["adapter_runtime_source_backed"] is False
    assert packet["frontend_code_added"] is False
    assert packet["backend_code_added"] is False
    assert packet["lima_runtime_imports_added"] is False
    assert packet["lima_runtime_calls_added"] is False
    assert packet["provider_model_calls_added"] is False
    assert (
        packet["connector_browser_network_file_device_robotics_behavior_added"] is False
    )
    assert packet["worker_dispatch_added"] is False
    assert packet["lifecycle_controls_added"] is False
    assert packet["evidence_persistence_added"] is False
    assert packet["proof_not_authority"] is True
    assert packet["requires_phase_gate"] is True

    for key, value in packet["required_confirmations"].items():
        assert value is True
