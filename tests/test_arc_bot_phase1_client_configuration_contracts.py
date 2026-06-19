"""Phase-1 client configuration migration-gate contract checks."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "tests" / "fixtures" / "arc_bot_phase1_client_configuration.json"
SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "schemas" / "arc_bot_client_configuration.schema.json"
MIGRATION_GATE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_phase1_client_configuration_migration_gate_packet.json"
)
MIGRATION_PROOF_PACKET_PATH = (
    REPO_ROOT
    / "docs"
    / "proof_packets"
    / "ARC_BOT_PHASE1_CLIENT_CONFIGURATION_MIGRATION_GATE_PACKET.md"
)


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_client_configuration_contract_and_migration_artifacts_exist() -> None:
    for path in (CONFIG_PATH, SCHEMA_PATH, MIGRATION_GATE_PATH, MIGRATION_PROOF_PACKET_PATH):
        assert path.exists(), path


def test_client_configuration_migration_gate_packet_is_fail_closed() -> None:
    packet = _load_json(MIGRATION_GATE_PATH)

    assert packet["packet_id"] == "arc_bot_phase1_client_configuration_migration_gate_packet_v1"
    assert packet["api_status"] == "CANDIDATE_ONLY"
    assert packet["artifact_version"] == "phase-1"
    assert packet["source_client_configuration_fixture"] == (
        "tests/fixtures/arc_bot_phase1_client_configuration.json"
    )
    assert packet["schema_ref"] == "docs/contracts/schemas/arc_bot_client_configuration.schema.json"
    assert packet["proof_packet_ref"] == (
        "docs/proof_packets/ARC_BOT_PHASE1_CLIENT_CONFIGURATION_MIGRATION_GATE_PACKET.md"
    )

    gates = packet["migration_gates"]
    assert len(gates) == 3
    gate_ids = {item["gate_id"] for item in gates}
    assert gate_ids == {
        "client_configuration_shape_gate",
        "tenant_and_boundary_gate",
        "runtime_authority_stop_gate",
    }

    for gate in gates:
        assert gate["required"] is True
        assert gate["requires_guardian_review"] is True
        assert gate["requires_evidence_ref"] is True
        assert gate["requires_rollback_metadata"] is True
        assert gate["future_implementation_approval_required"] is True

    for action in (
        "frontend_route_activation",
        "interactive_action_controls_activation",
        "runtime_execution",
        "connector_oauth",
    ):
        assert action in gates[0]["blocked_runtime_actions"]


def test_client_configuration_migration_gate_packet_paths_are_addressable() -> None:
    packet = _load_json(MIGRATION_GATE_PATH)
    proof_text = MIGRATION_PROOF_PACKET_PATH.read_text(encoding="utf-8")

    for path_ref in (
        packet["source_client_configuration_fixture"],
        packet["schema_ref"],
        packet["proof_packet_ref"],
        ):
        assert path_ref in proof_text or (REPO_ROOT / path_ref).exists(), path_ref


def test_client_configuration_migration_gates_use_consistent_action_naming() -> None:
    packet = _load_json(MIGRATION_GATE_PATH)
    all_blocked = {
        action
        for gate in packet["migration_gates"]
        for action in gate["blocked_runtime_actions"]
    }
    required = {
        "frontend_route_activation",
        "interactive_action_controls_activation",
        "runtime_execution",
        "connector_oauth",
        "connector_live_read",
        "connector_live_write",
        "provider_model_calls",
        "worker_dispatch",
        "customer_system_mutation",
    }
    assert required.issubset(all_blocked)
    assert "connector_live_i/o" not in all_blocked
    assert "model_provider_call" not in all_blocked
