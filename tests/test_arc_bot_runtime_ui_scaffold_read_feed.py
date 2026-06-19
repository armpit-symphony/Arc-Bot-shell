"""Static checks for the Phase-1 runtime read-feed seam contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from phase0_runtime_ui_scaffold.read_feed import (
    ReadFeedContractError,
    build_phase1_read_feed_projection,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FEED_CONTRACT_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json"
)
PREVIEW_CONTRACT_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "arc_bot_runtime_ui_scaffold_preview_contract.json"
)


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_arc_bot_runtime_ui_scaffold_phase1_read_feed_contract_exists() -> None:
    assert FEED_CONTRACT_PATH.exists()


def test_arc_bot_runtime_ui_scaffold_phase1_read_feed_projection_is_read_only() -> None:
    projection = build_phase1_read_feed_projection(FEED_CONTRACT_PATH)
    preview_contract = _load_json(PREVIEW_CONTRACT_PATH)

    assert projection["phase"] == "phase-1"
    assert projection["projection_scope"] == "read_only"
    assert projection["source_reference"] == "app.services.guardian.suite"
    assert set(projection["surface_read_paths"].keys()) == set(preview_contract["surfaces"].keys())

    for surface, surface_projection in projection["surface_read_paths"].items():
        assert "contract_refs" in surface_projection
        assert "required_envelope_fields" in surface_projection
        assert isinstance(surface_projection["contract_refs"], list)
        assert isinstance(surface_projection["required_envelope_fields"], list)
        assert isinstance(surface_projection["blocked_runtime_actions"], list)
        assert surface_projection["spine_sources"], "surface must map to at least one spine source"
        if not isinstance(projection.get("metadata_policy"), dict):
            raise AssertionError("metadata_policy must be present in projection")
        for required_field in ("require_policy_refs", "require_evidence_refs", "require_runbook_refs"):
            assert projection["metadata_policy"][required_field] is True
        assert set(preview_contract["shared_envelope_fields"]).issubset(
            set(surface_projection["required_envelope_fields"])
        )

        for required_field in preview_contract["shared_envelope_fields"]:
            assert required_field in surface_projection["required_envelope_fields"]

        if surface == "work_queue":
            assert "dispatch_to_worker" in surface_projection["blocked_runtime_actions"]
        if surface == "runtime_settings":
            assert "perform_live_inference" in surface_projection["blocked_runtime_actions"]


def test_arc_bot_runtime_ui_scaffold_phase1_read_feed_rejects_runtime_authority_contract() -> None:
    payload = _load_json(FEED_CONTRACT_PATH)
    payload["runtime_authority_enabled"] = True

    temp_path = (
        REPO_ROOT / "tests" / "fixtures" / "arc_bot_runtime_ui_scaffold_phase1_read_feed_contract_breach.json"
    )
    try:
        temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        with pytest.raises(ReadFeedContractError):
            build_phase1_read_feed_projection(temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
