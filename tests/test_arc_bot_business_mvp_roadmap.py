"""Phase-1 business MVP roadmap presence and boundary checks."""

from __future__ import annotations

from pathlib import Path


def test_business_mvp_roadmap_artifact_exists_and_constrained() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    roadmap_path = repo_root / "docs" / "ROADMAP_PHASE1_BUSINESS_MVP.md"
    packet_path = (
        repo_root
        / "docs"
        / "proof_packets"
        / "ARC_BOT_PHASE1_MVP_ROADMAP_PACKET.md"
    )

    assert roadmap_path.exists(), roadmap_path
    assert packet_path.exists(), packet_path

    text = roadmap_path.read_text(encoding="utf-8")
    assert "preview/render" in text
    assert "No execution" in text or "No execution implementation" in text
    assert "no-execution" in text.lower()
    assert "1 Supervisor Server and 1-8" in text or "1-8 workers" in text
    assert "connector live I/O" in text
    assert "customer-system mutation" in text

    packet_text = packet_path.read_text(encoding="utf-8")
    assert "planning evidence only" in packet_text
    assert "docs/ROADMAP_PHASE1_BUSINESS_MVP.md" in packet_text
    assert "ARC_BOT_PHASE1_READINESS_BUNDLE_PACKET" in packet_text
