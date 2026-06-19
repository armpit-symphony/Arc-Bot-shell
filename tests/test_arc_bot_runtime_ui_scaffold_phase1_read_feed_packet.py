"""Proof packet checks for the Phase-1 runtime UI read-feed seam."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from phase0_runtime_ui_scaffold.read_feed import build_phase1_read_feed_projection


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase1_read_feed_packet.json"
)
FEED_CONTRACT_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json"
)
PREVIEW_CONTRACT_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_preview_contract.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_arc_bot_runtime_ui_scaffold_phase1_read_feed_packet_files_exist() -> None:
    packet = _load_json(PACKET_PATH)

    assert packet["packet_id"] == "arc_bot_runtime_ui_scaffold_phase1_read_feed_packet"
    assert packet["proof_gap_id"] == "PHASE-1-RUNTIME-UI-SCAFFOLD-READ-FEED"
    assert packet["api_status"] == "CANDIDATE_ONLY"
    assert packet["consumer_repo"] == "Arc-Bot-shell"
    assert packet["proof_branch"] == "arc-bot-runtime-ui-scaffold-phase1-read-feed-seam"
    assert packet["source_commit_before_branch"] == (
        "37af88ce94ade29cb2d3f97489e62ee423788d4d"
    )
    assert packet["projection_gate_name"] == "RUNTIME_UI_SCAFFOLD_PHASE1_FEED"
    assert packet["requires_phase_gate"] is True

    for relative_path in packet["proof_packet_files"]:
        assert (REPO_ROOT / relative_path).exists(), relative_path
    for relative_path in packet["supporting_evidence_files"]:
        assert (REPO_ROOT / relative_path).exists(), relative_path


def test_phase1_read_feed_packet_aligns_to_preview_contract() -> None:
    packet = _load_json(PACKET_PATH)
    feed_contract = _load_json(FEED_CONTRACT_PATH)
    preview_contract = _load_json(PREVIEW_CONTRACT_PATH)
    projection = build_phase1_read_feed_projection(FEED_CONTRACT_PATH)

    assert packet["projection_source_file"] == FEED_CONTRACT_PATH.relative_to(REPO_ROOT).as_posix()
    assert set(packet["surface_bindings"]) == set(preview_contract["surfaces"].keys())
    assert set(packet["surface_bindings"]) == set(preview_contract["surfaces"].keys())
    assert set(packet["spine_sources"]) == {
        "guardian_spine_tasks",
        "guardian_spine_events",
        "guardian_spine_approvals",
        "guardian_spine_projects",
    }
    assert projection["source_reference"] == packet["source_reference"]
    assert projection["source_reference"] == "app.services.guardian.suite"
    assert projection["projection_scope"] == "read_only"
    assert projection["surface_read_paths"].keys() == preview_contract["surfaces"].keys()
    assert projection["metadata_policy"] == packet["metadata_policy"]
    assert projection["metadata_policy"]["require_policy_refs"] is True
    assert projection["metadata_policy"]["require_evidence_refs"] is True
    assert projection["metadata_policy"]["require_runbook_refs"] is True

    for surface, surface_projection in projection["surface_read_paths"].items():
        assert surface in packet["surface_bindings"]
        assert set(surface_projection["required_envelope_fields"]).issuperset(
            {"tenant_id", "customer_context_id", "environment", "operator_role"}
        )
        if surface == "work_queue":
            assert "dispatch_to_worker" in surface_projection["blocked_runtime_actions"]
        elif surface == "runtime_settings":
            assert "perform_live_inference" in surface_projection["blocked_runtime_actions"]
        elif surface == "overview":
            assert "adjust_model_route" in surface_projection["blocked_runtime_actions"]

        assert set(surface_projection["spine_sources"]).issubset(set(packet["spine_sources"]))

        expected_refs = set(feed_contract["surface_read_paths"][surface]["contract_refs"])
        assert set(surface_projection["contract_refs"]) == expected_refs
