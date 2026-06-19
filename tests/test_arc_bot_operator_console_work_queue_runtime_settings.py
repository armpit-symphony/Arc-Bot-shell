"""Static checks for Arc Bot operator console Work Queue and Runtime Settings docs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_operator_console_work_queue_runtime_settings.json"
)


def _load_fixture() -> dict[str, Any]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(fixture, dict)
    return fixture


def test_arc_bot_work_queue_runtime_settings_fixture_and_docs_exist() -> None:
    fixture = _load_fixture()

    assert fixture["packet_id"] == "arc_bot_operator_console_work_queue_runtime_settings"
    assert fixture["api_status"] == "CANDIDATE_ONLY"
    assert fixture["consumer_repo"] == "Arc-Bot-shell"
    assert fixture["consumer_repository"] == "armpit-symphony/Arc-Bot-shell"
    assert fixture["proof_branch"] == "arc-work-queue-runtime-settings-docs"
    assert fixture["source_commit_before_branch"] == "8358b8c"
    assert fixture["docs_only_foundation_update"] is True

    for relative_path in fixture["docs"].values():
        assert (REPO_ROOT / relative_path).exists()


def test_arc_bot_work_queue_and_runtime_settings_surfaces_are_recorded() -> None:
    fixture = _load_fixture()

    assert fixture["operator_console_surfaces_added"] == [
        "Work Queue",
        "Runtime Settings",
    ]
    assert set(fixture["aligned_contracts"]) == {
        "task.execution",
        "worker.lifecycle",
        "console.view",
        "model.route",
        "supervisor.health",
        "guardian.decision",
        "evidence.artifact",
    }


def test_arc_bot_work_queue_contract_is_docs_only_and_fail_closed() -> None:
    contract = _load_fixture()["work_queue_contract"]

    assert contract["display_state_only"] is True
    assert contract["metadata_only_queue_entries"] is True
    assert contract["future_intent_envelope_mapping"] is True
    assert contract["live_program_execution_allowed"] is False
    assert contract["customer_system_mutation_allowed"] is False
    assert contract["external_message_send_allowed"] is False


def test_arc_bot_runtime_settings_contract_blocks_runtime_authority() -> None:
    contract = _load_fixture()["runtime_settings_contract"]

    assert contract["display_state_only"] is True
    assert contract["local_runtime_install_route_documented"] is True
    assert contract["model_route_readiness_metadata_documented"] is True
    assert contract["live_model_inference_allowed"] is False
    assert contract["tool_execution_allowed"] is False
    assert contract["credential_storage_allowed"] is False
    assert contract["provider_token_storage_allowed"] is False
    assert contract["raw_runtime_payload_persistence_allowed"] is False
    assert contract["runtime_route_change_without_approval_allowed"] is False


def test_arc_bot_docs_update_adds_no_runtime_behavior() -> None:
    boundaries = _load_fixture()["boundaries"]

    for key in (
        "runtime_behavior_added",
        "frontend_code_added",
        "backend_code_added",
        "lima_runtime_imports_added",
        "lima_runtime_calls_added",
        "provider_model_calls_added",
        "provider_sdk_added",
        "network_calls_added",
        "secret_or_credential_access_added",
        "file_mutation_added",
        "connector_behavior_added",
        "browser_network_device_robotics_physical_world_behavior_added",
        "product_readiness_claimed",
        "production_readiness_claimed",
    ):
        assert boundaries[key] is False


def test_arc_bot_phase0_contract_schema_snapshots_exist() -> None:
    artifact_paths = [
        "docs/contracts/schemas/arc_bot_console_state_envelope.schema.json",
        "docs/contracts/schemas/arc_bot_work_queue_state.schema.json",
        "docs/contracts/schemas/arc_bot_runtime_settings_state.schema.json",
        "tests/fixtures/arc_bot_phase0_work_queue_state_snapshot.json",
        "tests/fixtures/arc_bot_phase0_runtime_settings_state_snapshot.json",
    ]

    for relative_path in artifact_paths:
        assert (REPO_ROOT / relative_path).exists(), relative_path


def test_arc_bot_runtime_ui_contract_pack_is_referenced_for_phase0() -> None:
    pack_path = REPO_ROOT / "tests" / "fixtures" / "arc_bot_runtime_ui_scaffold_contract_pack.json"
    assert pack_path.exists()


def test_arc_bot_operator_console_docs_contain_expected_boundaries() -> None:
    fixture = _load_fixture()
    foundation = (
        REPO_ROOT / fixture["docs"]["operator_console_foundation"]
    ).read_text(encoding="utf-8")
    state_contract = (
        REPO_ROOT / fixture["docs"]["operator_console_state_contract"]
    ).read_text(encoding="utf-8")

    assert "| Work Queue | Stage work programs" in foundation
    assert "| Runtime Settings | Configure local runtime install route" in foundation
    assert "### Work Queue" in foundation
    assert "Trigger live program execution." in foundation
    assert "Persist queue mutations directly to customer systems." in foundation
    assert "LIMA AI OS `HumanInput` and `IntentEnvelope`" in foundation
    assert "### Runtime Settings" in foundation
    assert "Perform live model inference or tool execution." in foundation
    assert "Store credentials or provider tokens in this shell surface." in foundation
    assert "Persist secrets or raw runtime payloads locally as product state." in foundation
    assert "Change runtime routes without approval posture." in foundation
    assert "### Work Program State" in state_contract
    assert "work program ID and title" in state_contract
    assert "required model route posture for dispatch readiness" in state_contract
    assert "model-route readiness refs before active/deployment transition" in state_contract
