"""Runtime projection ingestion from a fixture read-feed payload."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from phase0_runtime_ui_scaffold.read_feed import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_PAYLOAD_PATH,
    ReadFeedPayloadError,
    ReadFeedGateError,
    build_phase1_read_feed_runtime_projection,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_build_phase1_read_feed_runtime_projection_ingests_payload() -> None:
    projection = build_phase1_read_feed_runtime_projection()

    assert projection["artifact_type"] == "phase1_read_feed_runtime_projection"
    assert projection["phase"] == "phase-1"
    assert projection["source_reference"] == "app.services.guardian.suite"
    assert projection["source_access_mode"] == "read_only"
    assert projection["phase_gate"]["name"] == "RUNTIME_UI_SCAFFOLD_PHASE1_FEED"
    assert projection["phase_gate"]["enabled"] is True
    assert projection["phase_gate"]["required"] is True
    assert set(projection["surface_bindings"]) == {
        "work_queue",
        "runtime_settings",
        "overview",
    }

    work_queue_projection = projection["surfaces"]["work_queue"]
    runtime_settings_projection = projection["surfaces"]["runtime_settings"]
    overview_projection = projection["surfaces"]["overview"]

    for surface_projection in (work_queue_projection, runtime_settings_projection, overview_projection):
        assert surface_projection["projection_mode"] == "read_only"
        assert "snapshot" in surface_projection
        assert "contract_refs" in surface_projection
        assert "spine_sources" in surface_projection

    assert "dispatch_to_worker" in work_queue_projection["blocked_runtime_actions"]
    assert "perform_live_inference" in runtime_settings_projection["blocked_runtime_actions"]
    assert "adjust_model_route" in overview_projection["blocked_runtime_actions"]
    assert runtime_settings_projection["snapshot"]["surface"] == "runtime_settings"
    assert overview_projection["snapshot"]["surface"] == "overview"
    assert work_queue_projection["snapshot"]["surface"] == "work_queue"


def test_build_phase1_read_feed_runtime_projection_rejects_payload_runtime_authority() -> None:
    payload = _load_json(DEFAULT_PAYLOAD_PATH)
    bad_payload = copy.deepcopy(payload)
    bad_payload["runtime_authority_enabled"] = True

    temp_path = (
        REPO_ROOT
        / "tests"
        / "fixtures"
        / "arc_bot_runtime_ui_scaffold_phase1_read_feed_payload_breach.json"
    )
    try:
        temp_path.write_text(json.dumps(bad_payload, indent=2), encoding="utf-8")
        with pytest.raises(ReadFeedPayloadError):
            build_phase1_read_feed_runtime_projection(feed_payload_path=temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_build_phase1_read_feed_runtime_projection_rejects_missing_required_surface_payload() -> None:
    payload = _load_json(DEFAULT_PAYLOAD_PATH)
    bad_payload = copy.deepcopy(payload)
    bad_payload["surface_payloads"].pop("work_queue")

    temp_path = (
        REPO_ROOT
        / "tests"
        / "fixtures"
        / "arc_bot_runtime_ui_scaffold_phase1_read_feed_payload_missing_surface.json"
    )
    try:
        temp_path.write_text(json.dumps(bad_payload, indent=2), encoding="utf-8")
        with pytest.raises(ReadFeedPayloadError):
            build_phase1_read_feed_runtime_projection(feed_payload_path=temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_build_phase1_read_feed_runtime_projection_rejects_snapshot_runtime_authority() -> None:
    payload = _load_json(DEFAULT_PAYLOAD_PATH)
    bad_payload = copy.deepcopy(payload)
    bad_payload["surface_payloads"]["work_queue"]["snapshot"]["live_program_execution_allowed"] = True

    temp_path = (
        REPO_ROOT
        / "tests"
        / "fixtures"
        / "arc_bot_runtime_ui_scaffold_phase1_read_feed_payload_breach_runtime.json"
    )
    try:
        temp_path.write_text(json.dumps(bad_payload, indent=2), encoding="utf-8")
        with pytest.raises(ReadFeedPayloadError):
            build_phase1_read_feed_runtime_projection(feed_payload_path=temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_build_phase1_read_feed_runtime_projection_rejects_gate_disabled() -> None:
    with pytest.raises(ReadFeedGateError):
        build_phase1_read_feed_runtime_projection(enable_phase_gate=False)
