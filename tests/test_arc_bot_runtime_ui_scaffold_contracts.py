"""Contract smoke checks for Phase-0 Work Queue and Runtime Settings scaffold snapshots."""

from __future__ import annotations

import json
from pathlib import Path

from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO_ROOT / "docs" / "contracts" / "schemas"

WORK_QUEUE_SCHEMA_PATH = SCHEMA_DIR / "arc_bot_work_queue_state.schema.json"
RUNTIME_SETTINGS_SCHEMA_PATH = SCHEMA_DIR / "arc_bot_runtime_settings_state.schema.json"
ENVELOPE_SCHEMA_PATH = SCHEMA_DIR / "arc_bot_console_state_envelope.schema.json"

WORK_QUEUE_FIXTURE_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "arc_bot_phase0_work_queue_state_snapshot.json"
)
RUNTIME_SETTINGS_FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_phase0_runtime_settings_state_snapshot.json"
)
CONTRACT_PACK_FIXTURE_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "arc_bot_runtime_ui_scaffold_contract_pack.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _assert_envelope(data: dict[str, Any], expected_view: str, allowed_statuses: set[str]) -> None:
    assert "envelope" in data
    envelope = data["envelope"]

    assert isinstance(envelope, dict)
    for key in (
        "tenant_id",
        "customer_context_id",
        "environment",
        "operator_role",
        "view_id",
        "view_type",
        "view_mode",
        "status",
        "policy_refs",
        "evidence_refs",
        "related_contract_refs",
        "runbook_refs",
        "future_lima_office_supervisor_seam",
        "future_lima_ai_os_seam",
    ):
        assert key in envelope

    assert envelope["view_type"] == expected_view
    assert envelope["status"] in allowed_statuses
    assert isinstance(envelope["policy_refs"], list) and len(envelope["policy_refs"]) >= 1
    assert isinstance(envelope["evidence_refs"], list) and len(envelope["evidence_refs"]) >= 1
    assert isinstance(envelope["related_contract_refs"], list) and len(envelope["related_contract_refs"]) >= 1
    assert envelope["runbook_refs"] is not None
    if envelope["status"] == "blocked":
        assert isinstance(envelope.get("blocked_reason"), list)
        assert len(envelope["blocked_reason"]) > 0


def _assert_no_runtime_authority_contracts(payload: dict[str, Any]) -> None:
    assert payload.get("runtime_route_change_without_approval_allowed") is False
    assert payload.get("live_model_inference_allowed") is False
    assert payload.get("tool_execution_allowed") is False
    assert payload.get("credential_storage_allowed") is False
    assert payload.get("provider_token_storage_allowed") is False
    assert payload.get("raw_runtime_payload_persistence_allowed") is False


def test_arc_bot_runtime_ui_scaffold_schema_documents_exist() -> None:
    assert WORK_QUEUE_SCHEMA_PATH.exists()
    assert RUNTIME_SETTINGS_SCHEMA_PATH.exists()
    assert ENVELOPE_SCHEMA_PATH.exists()

    payload = _load_json(WORK_QUEUE_FIXTURE_PATH)
    runtime_payload = _load_json(RUNTIME_SETTINGS_FIXTURE_PATH)
    assert "work_programs" in payload
    assert "local_runtime_install_routes" in runtime_payload


def test_arc_bot_work_queue_snapshot_conforms_phase0_scope() -> None:
    data = _load_json(WORK_QUEUE_FIXTURE_PATH)

    assert data["surface"] == "work_queue"
    assert data["display_state_only"] is True
    assert data["metadata_only_queue_entries"] is True
    assert data["future_intent_envelope_mapping"] is True
    assert data["live_program_execution_allowed"] is False
    assert data["customer_system_mutation_allowed"] is False
    assert data["external_message_send_allowed"] is False

    _assert_envelope(data, expected_view="work_queue", allowed_statuses={"review_required", "blocked"})

    programs = data["work_programs"]
    assert isinstance(programs, list)
    assert len(programs) >= 2
    for program in programs:
        assert program["status"] in {"draft", "ready", "active", "completed"}
        assert program["execution_mode"] in {
            "plan_only",
            "read_only",
            "draft_only",
            "mock_only",
            "blocked_mvp",
        }
        assert program["required_model_route_posture"] in {
            "mock_only",
            "local_planned",
            "subscription_planned",
            "blocked_mvp",
        }
        assert isinstance(program["blocked_reasons"], list)


def test_arc_bot_runtime_settings_snapshot_conforms_phase0_scope() -> None:
    data = _load_json(RUNTIME_SETTINGS_FIXTURE_PATH)

    assert data["surface"] == "runtime_settings"
    assert data["display_state_only"] is True
    assert data["local_runtime_install_route_documented"] is True
    assert data["model_route_readiness_metadata_documented"] is True
    _assert_no_runtime_authority_contracts(data)
    _assert_envelope(data, expected_view="runtime_settings", allowed_statuses={"rendered", "review_required", "degraded"})

    routes = data["local_runtime_install_routes"]
    assert isinstance(routes, list)
    assert len(routes) >= 1
    assert data["runtime_route_posture"]["status"] in {"selected", "degraded", "denied", "blocked", "unavailable"}


def test_arc_bot_runtime_ui_scaffold_contract_pack_is_phase0_ready() -> None:
    pack = _load_json(CONTRACT_PACK_FIXTURE_PATH)

    assert pack["packet_id"] == "arc_bot_runtime_ui_scaffold_contract_pack"
    assert pack["api_status"] == "CANDIDATE_ONLY"
    assert pack["docs_only_foundation_update"] is True
    assert pack["target_build_surface"] == "work_queue_and_runtime_settings"
    assert pack["contract_pack"]["contract_family"] == "phase-0"
    assert pack["contract_pack"]["display_mode_only"] is True
    assert pack["proof_branch"] == "arc-runtime-ui-scaffold-contract-pack"
    assert pack["source_commit_before_branch"] == (
        "a05faea14ab24341b4b4567967911e33e51ce88a"
    )
    assert pack["contract_pack"]["runtime_authority_required_for_execution"] is True
    assert set(pack["contract_pack"]["surface_bindings"].keys()) == {
        "work_queue",
        "runtime_settings",
    }

    assert pack["contract_pack"]["metadata_policy"]["require_policy_refs"] is True
    assert pack["contract_pack"]["metadata_policy"]["require_evidence_refs"] is True
    assert pack["contract_pack"]["metadata_policy"]["require_runbook_refs"] is True

    for blocked_action in pack["contract_pack"]["blocked_runtime_actions"]:
        assert blocked_action in {
            "provider_model_calls",
            "connector_reads",
            "connector_writes",
            "tool_execution",
            "runtime_route_mutation",
            "credential_storage",
            "customer_system_mutation",
        }

    for path in pack["contract_pack"]["artifacts"]:
        assert (REPO_ROOT / path).exists(), path
