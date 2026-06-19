"""Phase-1 runtime authority gating pack projection tests."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

from phase1_runtime_authority_gating import (
    DEFAULT_AUTHORITY_GATING_PACKET_PATH,
    Phase1AuthorityGatingError,
    Phase1AuthorityGatingSchemaError,
    build_phase1_runtime_authority_gating_projection,
    run_phase1_runtime_authority_gating_preview,
)


def test_authority_gating_projection_builds_planning_pack() -> None:
    projection = build_phase1_runtime_authority_gating_projection(
        packet_path=DEFAULT_AUTHORITY_GATING_PACKET_PATH,
        enable_phase_gate=True,
    )

    assert projection["artifact_type"] == "phase1_runtime_authority_gating_pack"
    assert projection["phase"] == "phase-1"
    assert projection["projection_scope"] == "planning_read_only"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["source_access_mode"] == "read_only"
    assert projection["phase_gate"]["name"] == "ARC_BOT_PHASE1_RUNTIME_AUTHORITY_GATING"
    assert projection["phase_gate"]["enabled"] is True
    assert projection["unresolved_required_gates"]
    assert set(projection["unresolved_required_gates"]) == {
        "approval_token_lineage",
        "connector_authority_approval",
        "evidence_and_rollback_gate",
        "guardian_runtime_authority_approval",
        "production_readiness_approval",
    }
    assert projection["intent_count"] >= 1
    assert "work_queue" in projection["surface_bindings"]


def test_authority_gating_projection_cli_can_export_snapshot(tmp_path: Path) -> None:
    output = io.StringIO()

    with patch("sys.stdout", output):
        status = run_phase1_runtime_authority_gating_preview(
            ["--compact", f"--snapshot-path={tmp_path / 'authority_gating.json'}"]
        )

    assert status == 0
    snapshot = json.loads((tmp_path / "authority_gating.json").read_text(encoding="utf-8"))
    cli_payload = json.loads(output.getvalue())
    assert cli_payload == snapshot


def test_authority_gating_projection_fails_without_gate() -> None:
    status = run_phase1_runtime_authority_gating_preview(["--no-phase-gate", "--compact"])
    assert status == 1


def test_authority_gating_projection_rejects_bad_phase_gate(tmp_path: Path) -> None:
    fixture = json.loads(
        DEFAULT_AUTHORITY_GATING_PACKET_PATH.read_text(encoding="utf-8")
    )
    fixture["phase_gate"]["name"] = "BAD_GATE"
    bad_path = tmp_path / "bad_runtime_authority_gating_packet.json"
    bad_path.write_text(json.dumps(fixture, indent=2), encoding="utf-8")

    try:
        build_phase1_runtime_authority_gating_projection(
            packet_path=bad_path,
            enable_phase_gate=True,
        )
        raise AssertionError("expected Phase1AuthorityGatingError")
    except (Phase1AuthorityGatingError, Phase1AuthorityGatingSchemaError):
        pass


def test_authority_gating_payload_links_required_gates_to_intents() -> None:
    fixture = json.loads(DEFAULT_AUTHORITY_GATING_PACKET_PATH.read_text(encoding="utf-8"))
    required_gate_ids = {
        "approval_token_lineage",
        "connector_authority_approval",
        "evidence_and_rollback_gate",
        "guardian_runtime_authority_approval",
        "production_readiness_approval",
    }

    used_gate_ids: set[str] = set()
    for intent in fixture["planned_user_intents"]:
        used_gate_ids.update(intent["required_future_gates"])

    assert required_gate_ids.issubset(used_gate_ids)


def test_authority_gating_payload_runtime_boundaries_are_false() -> None:
    fixture = json.loads(DEFAULT_AUTHORITY_GATING_PACKET_PATH.read_text(encoding="utf-8"))

    for key, value in fixture["runtime_boundaries"].items():
        assert value is False, key


def test_authority_gating_proof_packet_names_validation_commands() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    packet_text = (
        repo_root
        / "docs"
        / "proof_packets"
        / "ARC_BOT_PHASE1_RUNTIME_AUTHORITY_GATING_PACKET.md"
    ).read_text(encoding="utf-8")
    fixture = json.loads(DEFAULT_AUTHORITY_GATING_PACKET_PATH.read_text(encoding="utf-8"))

    for command in fixture["validation_commands"]:
        assert command in packet_text
