"""Phase-1 readiness bundle proof packet coverage."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_phase1_readiness_bundle_packet_and_projection_references() -> None:
    packet = REPO_ROOT / "docs" / "proof_packets" / "ARC_BOT_PHASE1_READINESS_BUNDLE_PACKET.md"
    assert packet.exists(), packet

    packet_text = packet.read_text(encoding="utf-8")
    assert "Phase-1 readiness bundle" in packet_text
    assert "phase1_readiness.bundle" in packet_text
    assert "python -m phase1_readiness.bundle --compact" in packet_text
    assert (
        "tests/fixtures/arc_bot_phase1_readiness_bundle_projection.json"
        in packet_text
    )
    assert (
        "docs/proof_packets/ARC_BOT_PHASE1_CLIENT_CONFIGURATION_MIGRATION_GATE_PACKET.md"
        in packet_text
    )
    assert (
        "tests/fixtures/arc_bot_runtime_ui_scaffold_phase0_scope_lock_status_snapshot.json"
        in packet_text
    )

    roadmap = REPO_ROOT / "docs" / "ROADMAP_PHASE1_BUSINESS_MVP.md"
    roadmap_text = roadmap.read_text(encoding="utf-8")
    assert "ARC_BOT_PHASE1_READINESS_BUNDLE_PACKET" in roadmap_text
    assert "ARC_BOT_PHASE1_RUNTIME_AUTHORITY_GATING_PACKET" in roadmap_text
