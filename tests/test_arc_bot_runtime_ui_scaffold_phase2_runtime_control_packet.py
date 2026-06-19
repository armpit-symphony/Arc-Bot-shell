"""Proof packet checks for the Phase-2 runtime-control handoff seam."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from phase0_runtime_ui_scaffold.phase2_runtime_control import (
    build_phase2_runtime_control_projection,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase2_runtime_control_packet.json"
)
PHASE2_CONSUMER_PACKET_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase2_runtime_consumer_packet.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_arc_bot_runtime_ui_scaffold_phase2_runtime_control_packet_files_exist() -> None:
    packet = _load_json(PACKET_PATH)
    consumer_packet = _load_json(PHASE2_CONSUMER_PACKET_PATH)

    assert packet["packet_id"] == "arc_bot_runtime_ui_scaffold_phase2_runtime_control_packet"
    assert packet["proof_gap_id"] == "PHASE-2-RUNTIME-CONTROL-HANDOFF"
    assert packet["consumer_repo"] == "Arc-Bot-shell"
    assert packet["proof_branch"] == "arc-bot-runtime-ui-scaffold-phase2-runtime-control-handoff"
    assert packet["projection_gate_name"] == "RUNTIME_UI_SCAFFOLD_PHASE1_FEED"
    assert packet["requires_phase_gate"] is True
    assert packet["runtime_authority_blocked"] is True
    assert packet["runtime_execution_blocked"] is True

    for relative_path in packet["proof_packet_files"]:
        assert (REPO_ROOT / relative_path).exists(), relative_path
    for relative_path in packet["supporting_evidence_files"]:
        assert (REPO_ROOT / relative_path).exists(), relative_path

    assert consumer_packet["packet_id"] == "arc_bot_runtime_ui_scaffold_phase2_runtime_consumer_packet"
    assert consumer_packet["requires_phase_gate"] is True
    assert consumer_packet["runtime_authority_blocked"] is True
    assert (
        consumer_packet["required_confirmations"]["runtime_consumer_projection_added"]
        is True
    )


def test_phase2_runtime_control_projection_matches_packet() -> None:
    packet = _load_json(PACKET_PATH)
    projection = build_phase2_runtime_control_projection()

    assert projection["artifact_type"] == "phase2_runtime_control_handoff_projection"
    assert projection["artifact_id"] == packet.get("artifact_id")
    assert projection["phase"] == packet["phase"]
    assert projection["projection_source"] == "phase1_runtime_ui_consumer_projection"
    assert projection["projection_scope"] == "read_only"
    assert projection["source_reference"] == packet["source_reference"]
    assert projection["source_access_mode"] == packet["source_access_mode"]
    assert projection["runtime_authority_blocked"] is True
    assert set(packet["surface_bindings"]) == set(projection["surface_bindings"])
    assert set(packet["projection_bindings"]) == set(projection["projection_bindings"])
    assert set(projection["spine_source_record_counts"].keys()) == set(
        packet["spine_sources"]
    )

    for surface_projection in projection["surfaces"].values():
        assert surface_projection["projection_mode"] == "read_only"
        assert surface_projection["runtime_authority_blocked"] is True
        assert surface_projection["runtime_execution_blocked"] is True

    for surface in projection["surface_bindings"]:
        assert surface in projection["surfaces"]
        assert surface in packet["surface_bindings"]
        assert packet["surface_control_posture"] == "ui_state_handoff_read_only"

    assert projection["handoff_metadata"]["handoff_mode"] == "downstream_ui_state"
