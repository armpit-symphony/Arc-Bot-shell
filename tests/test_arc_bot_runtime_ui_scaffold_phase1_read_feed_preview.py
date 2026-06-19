"""Tests for the Phase-1 read-feed preview rendering interface."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest

from phase0_runtime_ui_scaffold.read_feed import (
    DEFAULT_CONTRACT_PATH,
    EXPECTED_PHASE_GATE_NAME,
    ReadFeedGateError,
    build_phase1_read_feed_projection,
    render_phase1_read_feed_projection,
    run_read_feed_preview,
)


def test_render_phase1_read_feed_projection_defaults() -> None:
    rendered = render_phase1_read_feed_projection()

    projection = build_phase1_read_feed_projection(DEFAULT_CONTRACT_PATH)
    assert rendered["projection"] == EXPECTED_PHASE_GATE_NAME
    assert rendered["phase"] == "phase-1"
    assert rendered["projection_scope"] == "read_only"
    assert rendered["phase_gate"]["required"] is True
    assert rendered["phase_gate"]["enabled"] is True
    assert rendered["artifact_id"] == projection["artifact_id"]
    assert rendered["artifact_type"] == projection["artifact_type"]
    assert rendered["source_reference"] == projection["source_reference"]
    assert set(rendered["surface_bindings"]) == set(projection["surface_read_paths"].keys())
    assert "surface_read_paths" in rendered


def test_render_phase1_read_feed_projection_can_omit_surface_contracts() -> None:
    rendered = render_phase1_read_feed_projection(include_surface_contracts=False)

    assert rendered["projection"] == EXPECTED_PHASE_GATE_NAME
    assert "surface_read_paths" not in rendered
    assert set(rendered["surface_bindings"]) == {
        "work_queue",
        "runtime_settings",
        "overview",
    }


def test_render_phase1_preview_rejects_gate_mismatch() -> None:
    with pytest.raises(ReadFeedGateError):
        render_phase1_read_feed_projection(phase_gate_name="BAD_GATE")


def test_run_read_feed_preview_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_read_feed_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["projection"] == EXPECTED_PHASE_GATE_NAME
    assert parsed["phase_gate"]["name"] == EXPECTED_PHASE_GATE_NAME


def test_run_read_feed_preview_cli_omit_surface_contracts() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_read_feed_preview(["--omit-surface-contracts", "--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert "surface_read_paths" not in parsed


def test_run_read_feed_preview_cli_handles_bad_contract_path() -> None:
    status = run_read_feed_preview(["does_not_exist.json", "--compact"])
    assert status == 1
