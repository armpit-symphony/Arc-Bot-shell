"""Phase-1 business inventory schema, wireframe, and migration-gate checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = REPO_ROOT / "tests" / "fixtures" / "arc_bot_phase1_business_inventory.json"
MIGRATION_GATE_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "arc_bot_phase1_business_inventory_migration_gate_packet.json"
)
SCHEMA_PATH = (
    REPO_ROOT / "docs" / "contracts" / "schemas" / "arc_bot_phase1_business_inventory.schema.json"
)
WIREFRAME_PATH = (
    REPO_ROOT / "docs" / "wireframes" / "ARC_BOT_PHASE1_BUSINESS_INVENTORY_WIREFRAMES.md"
)
PROOF_PACKET_PATH = (
    REPO_ROOT
    / "docs"
    / "proof_packets"
    / "ARC_BOT_PHASE1_BUSINESS_INVENTORY_MIGRATION_GATE_PACKET.md"
)


EXPECTED_SURFACES = {
    "approvals",
    "connectors",
    "evidence",
    "governance",
    "guardian",
    "model_local_readiness",
    "overview",
    "runbooks",
    "runtime_settings",
    "tasks",
    "work_queue",
    "workers",
}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_phase1_inventory_schema_fixture_and_docs_exist() -> None:
    for path in (INVENTORY_PATH, MIGRATION_GATE_PATH, SCHEMA_PATH, WIREFRAME_PATH, PROOF_PACKET_PATH):
        assert path.exists(), path


def test_phase1_inventory_schema_aligns_with_fixture_shape() -> None:
    schema = _load_json(SCHEMA_PATH)
    inventory = _load_json(INVENTORY_PATH)

    assert schema["title"] == "Arc Bot Phase-1 Business Inventory"
    assert schema["properties"]["artifact_id"]["const"] == inventory["artifact_id"]
    assert schema["properties"]["artifact_type"]["const"] == inventory["artifact_type"]
    assert schema["properties"]["artifact_version"]["const"] == inventory["artifact_version"]
    assert schema["properties"]["source_reference"]["const"] == inventory["source_reference"]
    assert schema["properties"]["source_access_mode"]["const"] == inventory["source_access_mode"]

    required = set(schema["required"])
    assert required.issubset(inventory.keys())

    schema_surfaces = set(schema["properties"]["surfaces"]["required"])
    assert schema_surfaces == EXPECTED_SURFACES
    assert set(inventory["surfaces"]) == EXPECTED_SURFACES


def test_phase1_inventory_wireframes_cover_all_surfaces_and_stop_conditions() -> None:
    text = WIREFRAME_PATH.read_text(encoding="utf-8")

    for surface in EXPECTED_SURFACES:
        assert f"`{surface}`" in text

    for phrase in (
        "no dispatch",
        "no route mutation",
        "no provider calls",
        "no OAuth/live I/O",
        "Stop and request a new approval gate",
    ):
        assert phrase in text


def test_phase1_inventory_migration_gate_packet_links_evidence() -> None:
    packet = _load_json(MIGRATION_GATE_PATH)

    assert packet["packet_id"] == "arc_bot_phase1_business_inventory_migration_gate_packet_v1"
    assert packet["api_status"] == "CANDIDATE_ONLY"
    assert packet["source_inventory_fixture"] == "tests/fixtures/arc_bot_phase1_business_inventory.json"
    assert packet["schema_ref"] == "docs/contracts/schemas/arc_bot_phase1_business_inventory.schema.json"
    assert packet["wireframe_ref"] == (
        "docs/wireframes/ARC_BOT_PHASE1_BUSINESS_INVENTORY_WIREFRAMES.md"
    )
    assert packet["proof_packet_ref"] == (
        "docs/proof_packets/ARC_BOT_PHASE1_BUSINESS_INVENTORY_MIGRATION_GATE_PACKET.md"
    )
    assert set(packet["surface_bindings"]) == EXPECTED_SURFACES

    for path_ref in (
        packet["source_inventory_fixture"],
        packet["schema_ref"],
        packet["wireframe_ref"],
        packet["proof_packet_ref"],
    ):
        assert (REPO_ROOT / path_ref).exists(), path_ref


def test_phase1_inventory_migration_gates_are_fail_closed() -> None:
    packet = _load_json(MIGRATION_GATE_PATH)

    expected_gate_ids = {
        "schema_alignment_gate",
        "wireframe_alignment_gate",
        "downstream_consumer_readiness_gate",
        "runtime_authority_stop_gate",
        "evidence_and_rollback_gate",
    }
    gates = packet["migration_gates"]

    assert {gate["gate_id"] for gate in gates} == expected_gate_ids
    for gate in gates:
        assert gate["required"] is True
        assert gate["requires_guardian_review"] is True
        assert gate["requires_evidence_ref"] is True
        assert gate["requires_rollback_metadata"] is True
        assert gate["future_implementation_approval_required"] is True
        assert gate["blocked_runtime_actions"]

    for allowed_now in (action for gate in gates for action in gate["allowed_now"]):
        assert "execution" not in allowed_now
        assert "dispatch" not in allowed_now
        assert "live" not in allowed_now


def test_phase1_inventory_migration_boundaries_remain_false() -> None:
    boundaries = _load_json(MIGRATION_GATE_PATH)["runtime_boundaries"]

    for key, value in boundaries.items():
        assert value is False, key


def test_phase1_inventory_proof_packet_names_validation_commands() -> None:
    proof_text = PROOF_PACKET_PATH.read_text(encoding="utf-8")
    packet = _load_json(MIGRATION_GATE_PATH)

    assert "read-only migration-gate evidence" in proof_text
    assert "does not add UI implementation" in proof_text
    for command in packet["validation_commands"]:
        assert command in proof_text or command.endswith(".json")
