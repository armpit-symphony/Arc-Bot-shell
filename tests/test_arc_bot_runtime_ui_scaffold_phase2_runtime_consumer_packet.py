"""Proof packet checks for the Phase-2 runtime consumer handoff."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from phase0_runtime_ui_scaffold.read_feed import build_phase1_read_feed_projection
from phase0_runtime_ui_scaffold.runtime_consumer import (
    build_phase1_runtime_ui_consumer_projection,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase2_runtime_consumer_packet.json"
)
FEED_CONTRACT_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json"
)
PHASE1_PACKET_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase1_read_feed_packet.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_arc_bot_runtime_ui_scaffold_phase2_runtime_consumer_packet_files_exist() -> None:
    packet = _load_json(PACKET_PATH)
    phase1_packet = _load_json(PHASE1_PACKET_PATH)

    assert packet["packet_id"] == "arc_bot_runtime_ui_scaffold_phase2_runtime_consumer_packet"
    assert packet["proof_gap_id"] == "PHASE-2-RUNTIME-CONSUMER-HANDOFF"
    assert packet["consumer_repo"] == "Arc-Bot-shell"
    assert packet["proof_branch"] == "arc-bot-runtime-ui-scaffold-phase2-runtime-consumer-handoff"
    assert packet["projection_gate_name"] == "RUNTIME_UI_SCAFFOLD_PHASE1_FEED"
    assert packet["requires_phase_gate"] is True

    for relative_path in packet["proof_packet_files"]:
        assert (REPO_ROOT / relative_path).exists(), relative_path
    for relative_path in packet["supporting_evidence_files"]:
        assert (REPO_ROOT / relative_path).exists(), relative_path

    assert phase1_packet["required_confirmations"]["phase1_runtime_consumer_interface_added"] is True


def test_phase2_runtime_consumer_projection_matches_packet_surface_bindings() -> None:
    packet = _load_json(PACKET_PATH)
    phase1_projection = build_phase1_read_feed_projection(FEED_CONTRACT_PATH)
    projection = build_phase1_runtime_ui_consumer_projection()

    assert projection["source_reference"] == packet["source_reference"]
    assert projection["source_access_mode"] == packet["source_access_mode"]
    assert projection["runtime_authority_blocked"] is True
    assert set(packet["spine_sources"]) == set(projection["spine_sources"])
    assert set(packet["surface_bindings"]) == set(projection["surface_bindings"])
    assert set(phase1_projection["surface_read_paths"].keys()) == set(
        projection["surface_bindings"]
    )

    for surface in projection["surface_bindings"]:
        surface_projection = projection["surfaces"][surface]
        assert surface_projection["snapshot_surface"] == surface
        assert surface_projection["projection_mode"] == "read_only"
        assert set(surface_projection["blocked_runtime_actions"])
        assert set(surface_projection["contract_refs"])
        assert packet["runtime_authority_blocked"] is True


def test_phase2_runtime_consumer_packet_required_confirmations_true() -> None:
    packet = _load_json(PACKET_PATH)

    for key in (
        "proof_packet_files_exist",
        "runtime_consumer_projection_added",
        "runtime_consumer_preview_cli_added",
        "projection_surfaces_preserve_binding",
        "projection_surface_bindings_exact",
        "runtime_authority_blocks_still_present",
        "runtime_preview_summary_included",
        "no_runtime_wiring_added",
        "no_runtime_source_change",
    ):
        assert packet["required_confirmations"][key] is True
