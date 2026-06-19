"""Proof packet checks for the Phase-2 runtime-control consumer handoff seam."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from phase0_runtime_ui_scaffold.runtime_control_consumer import (
    build_phase2_runtime_control_consumer_projection,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase2_runtime_control_consumer_packet.json"
)
PHASE2_CONTROL_PACKET_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase2_runtime_control_packet.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_arc_bot_runtime_ui_scaffold_phase2_runtime_control_consumer_packet_files_exist() -> None:
    packet = _load_json(PACKET_PATH)
    phase2_packet = _load_json(PHASE2_CONTROL_PACKET_PATH)

    assert packet["packet_id"] == "arc_bot_runtime_ui_scaffold_phase2_runtime_control_consumer_packet"
    assert packet["proof_gap_id"] == "PHASE-2-RUNTIME-CONTROL-CONSUMER"
    assert packet["consumer_repo"] == "Arc-Bot-shell"
    assert packet["proof_branch"] == "arc-bot-runtime-ui-scaffold-phase2-runtime-control-consumer"
    assert packet["projection_gate_name"] == "RUNTIME_UI_SCAFFOLD_PHASE1_FEED"
    assert packet["requires_phase_gate"] is True
    assert packet["runtime_authority_blocked"] is True
    assert packet["runtime_execution_blocked"] is True
    assert phase2_packet["projection_gate_name"] == "RUNTIME_UI_SCAFFOLD_PHASE1_FEED"

    for relative_path in packet["proof_packet_files"]:
        assert (REPO_ROOT / relative_path).exists(), relative_path
    for relative_path in packet["supporting_evidence_files"]:
        assert (REPO_ROOT / relative_path).exists(), relative_path


def test_phase2_runtime_control_consumer_projection_matches_packet() -> None:
    packet = _load_json(PACKET_PATH)
    projection = build_phase2_runtime_control_consumer_projection()

    assert projection["artifact_type"] == "phase2_runtime_control_ui_consumer_projection"
    assert projection["artifact_id"] == packet["artifact_id"]
    assert projection["phase"] == packet["phase"]
    assert projection["source_reference"] == packet["source_reference"]
    assert projection["source_access_mode"] == packet["source_access_mode"]
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["projection_source"] == "phase2_runtime_control_handoff_projection"
    assert set(projection["surface_bindings"]) == set(packet["surface_bindings"])
    assert projection["consumer_metadata"]["consumer_mode"] == "read_only"

    for surface_projection in projection["surfaces"].values():
        assert surface_projection["downstream_mode"] == "read_only"
        assert surface_projection["ui_control_mode"] == "preview_only"
        assert surface_projection["runtime_authority_blocked"] is True
        assert surface_projection["runtime_execution_blocked"] is True
        assert surface_projection["control_state"] == "blocked_preview"
