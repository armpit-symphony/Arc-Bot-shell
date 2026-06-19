"""Phase-1 client configuration and no-execution skeleton checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "tests" / "fixtures" / "arc_bot_phase1_client_configuration.json"
PACKET_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "arc_bot_phase1_client_configuration_no_execution_packet.json"
)
SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "schemas" / "arc_bot_client_configuration.schema.json"
SKELETON_PLAN_PATH = REPO_ROOT / "docs" / "NO_EXECUTION_SKELETON_PLAN.md"
PROOF_PACKET_PATH = (
    REPO_ROOT
    / "docs"
    / "proof_packets"
    / "ARC_BOT_PHASE1_CLIENT_CONFIGURATION_NO_EXECUTION_PACKET.md"
)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_client_configuration_artifacts_exist() -> None:
    for path in (CONFIG_PATH, PACKET_PATH, SCHEMA_PATH, SKELETON_PLAN_PATH, PROOF_PACKET_PATH):
        assert path.exists(), path


def test_client_configuration_schema_aligns_with_fixture() -> None:
    config = _load_json(CONFIG_PATH)
    schema = _load_json(SCHEMA_PATH)

    assert schema["title"] == "Arc Bot Phase-1 Client Configuration"
    assert schema["properties"]["artifact_id"]["const"] == config["artifact_id"]
    assert schema["properties"]["artifact_type"]["const"] == config["artifact_type"]
    assert schema["properties"]["artifact_version"]["const"] == config["artifact_version"]
    assert schema["properties"]["source_access_mode"]["const"] == config["source_access_mode"]
    assert set(schema["required"]).issubset(config.keys())

    phase_gate_schema = schema["properties"]["phase_gate"]["properties"]
    assert phase_gate_schema["name"]["const"] == config["phase_gate"]["name"]
    assert phase_gate_schema["flag"]["const"] == config["phase_gate"]["flag"]


def test_client_configuration_tenant_and_deployment_boundaries() -> None:
    config = _load_json(CONFIG_PATH)

    tenant = config["tenant_boundary"]
    assert tenant["single_tenant_only"] is True
    assert tenant["cross_tenant_memory_allowed"] is False
    assert tenant["customer_data_write_allowed"] is False
    assert tenant["tenant_switching_allowed"] is False
    assert tenant["raw_customer_data_storage_allowed"] is False

    deployment = config["deployment_profile"]
    assert deployment["target_topology"] == "one_supervisor_with_1_to_8_arc_workers"
    assert deployment["supervisor_count"] == 1
    assert deployment["worker_count_min"] == 1
    assert deployment["worker_count_max"] == 8
    assert deployment["deployment_status"] == "planning_only"
    assert deployment["production_deployment_allowed"] is False


def test_connector_profiles_are_metadata_only() -> None:
    config = _load_json(CONFIG_PATH)

    assert config["connector_profiles"]
    for connector in config["connector_profiles"]:
        assert connector["readiness"] in {"blocked_mvp", "missing_contract", "review_required"}
        assert connector["credential_value_allowed"] is False
        assert connector["live_read_allowed"] is False
        assert connector["live_write_allowed"] is False
        assert connector["oauth_flow_allowed"] is False
        assert connector["webhook_allowed"] is False
        assert connector["metadata_actions"]


def test_client_configuration_runtime_boundaries_are_false() -> None:
    config = _load_json(CONFIG_PATH)
    packet = _load_json(PACKET_PATH)

    for source in (config["runtime_boundaries"], packet["runtime_boundaries"]):
        for key, value in source.items():
            assert value is False, key


def test_no_execution_packet_links_artifacts_and_gates() -> None:
    packet = _load_json(PACKET_PATH)

    assert packet["packet_id"] == "arc_bot_phase1_client_configuration_no_execution_packet_v1"
    assert packet["api_status"] == "CANDIDATE_ONLY"
    assert packet["phase_gate"] == {
        "name": "ARC_BOT_PHASE1_CLIENT_CONFIGURATION",
        "required": True,
        "flag": "arc_bot_client_configuration_docs_only",
    }

    for path_ref in (
        packet["client_configuration_fixture"],
        packet["client_configuration_schema"],
        packet["no_execution_skeleton_plan"],
        packet["proof_packet"],
    ):
        assert (REPO_ROOT / path_ref).exists(), path_ref

    assert "guardian_runtime_authority_approval" in packet["required_future_gates"]
    assert "connector_authority_approval" in packet["required_future_gates"]
    assert "production_readiness_approval" in packet["required_future_gates"]


def test_no_execution_skeleton_plan_blocks_runtime_paths() -> None:
    text = SKELETON_PLAN_PATH.read_text(encoding="utf-8")

    for phrase in (
        "No frontend route activation.",
        "No persistence or customer data writes.",
        "No connector live I/O",
        "No provider/model/local inference call.",
        "No worker dispatch or service control.",
        "No production deployment or product-readiness claim.",
    ):
        assert phrase in text


def test_no_execution_proof_packet_names_validation_and_boundaries() -> None:
    proof_text = PROOF_PACKET_PATH.read_text(encoding="utf-8")
    packet = _load_json(PACKET_PATH)

    for command in packet["validation_commands"]:
        assert command in proof_text

    for phrase in (
        "Client configuration is docs-only and phase-gated.",
        "Single-tenant assumptions are explicit.",
        "Connector profiles contain readiness metadata only.",
        "No credential values",
        "cannot authorize implementation or runtime behavior",
    ):
        assert phrase in proof_text


def test_client_configuration_contains_no_secret_material() -> None:
    text = CONFIG_PATH.read_text(encoding="utf-8").lower()

    forbidden_value_markers = [
        "sk-",
        "api_key_value",
        "secret_value",
        "bearer ",
        "oauth_client_secret",
        "refresh_token_value",
    ]
    for marker in forbidden_value_markers:
        assert marker not in text
