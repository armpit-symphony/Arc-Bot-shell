"""Runtime UI consumer projection seam for phase-1 read-feed payloads."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest

from phase0_runtime_ui_scaffold.runtime_consumer import (
    build_phase1_runtime_ui_consumer_projection,
    run_runtime_consumer_preview,
)
from phase0_runtime_ui_scaffold.read_feed import ReadFeedGateError


def test_build_phase1_runtime_ui_consumer_projection_happy_path() -> None:
    projection = build_phase1_runtime_ui_consumer_projection()

    assert projection["artifact_type"] == "phase1_runtime_ui_consumer_projection"
    assert projection["phase"] == "phase-1"
    assert projection["projection_scope"] == "read_only"
    assert projection["source_reference"] == "app.services.guardian.suite"
    assert projection["source_access_mode"] == "read_only"
    assert projection["runtime_authority_blocked"] is True
    assert projection["phase_gate"]["name"] == "RUNTIME_UI_SCAFFOLD_PHASE1_FEED"
    assert projection["phase_gate"]["enabled"] is True
    assert projection["phase_gate"]["required"] is True
    assert set(projection["spine_sources"]) == {
        "guardian_spine_tasks",
        "guardian_spine_events",
        "guardian_spine_approvals",
        "guardian_spine_projects",
    }
    assert set(projection["surface_bindings"]) == {
        "work_queue",
        "runtime_settings",
        "overview",
    }

    for surface_projection in projection["surfaces"].values():
        assert surface_projection["projection_mode"] == "read_only"
        assert surface_projection["snapshot_surface"] in {
            "work_queue",
            "runtime_settings",
            "overview",
        }
        assert surface_projection["view_type"] in {
            "work_queue",
            "runtime_settings",
            "overview",
        }
        assert surface_projection["status"] in {"review_required", "rendered"}
        assert set(surface_projection["blocked_runtime_actions"])
        assert set(surface_projection["contract_refs"])
        assert set(surface_projection["spine_sources"]).issubset(
            set(projection["spine_sources"])
        )

    assert projection["spine_source_records"]["guardian_spine_tasks"] == 2
    assert projection["spine_source_records"]["guardian_spine_events"] == 1
    assert projection["spine_source_records"]["guardian_spine_approvals"] == 1
    assert projection["spine_source_records"]["guardian_spine_projects"] == 1


def test_build_phase1_runtime_ui_consumer_projection_rejects_disabled_gate() -> None:
    with pytest.raises(ReadFeedGateError):
        build_phase1_runtime_ui_consumer_projection(enable_phase_gate=False)


def test_run_runtime_consumer_preview_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_runtime_consumer_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_type"] == "phase1_runtime_ui_consumer_projection"
    assert parsed["runtime_authority_blocked"] is True


def test_run_runtime_consumer_preview_cli_bad_payload_path() -> None:
    status = run_runtime_consumer_preview(
        [
            "--payload-path",
            "does_not_exist.json",
            "--compact",
        ]
    )

    assert status == 1
