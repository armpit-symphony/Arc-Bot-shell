"""Phase-1 readiness bundle projection tests."""

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from phase1_readiness import (
    PHASE1_READINESS_BUNDLE_ID,
    build_phase1_readiness_bundle,
    run_phase1_readiness_bundle_preview,
)
from phase1_readiness.bundle import Phase1ReadinessBundleError


READINESS_BUNDLE_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "arc_bot_phase1_readiness_bundle_projection.json"
)


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_phase1_readiness_bundle_builds_locked_projection() -> None:
    bundle = build_phase1_readiness_bundle()

    assert bundle["artifact_type"] == "phase1_readiness_bundle_projection"
    assert bundle["artifact_id"] == PHASE1_READINESS_BUNDLE_ID
    assert bundle["phase"] == "phase-1"
    assert bundle["projection_scope"] == "planning_read_only"
    assert bundle["source_access_mode"] == "read_only"
    assert bundle["runtime_authority_blocked"] is True
    assert bundle["runtime_execution_blocked"] is True

    phase_gate = bundle["phase_gate"]
    assert phase_gate["name"] == "ARC_BOT_PHASE1_READINESS_BUNDLE"
    assert phase_gate["required"] is True
    assert phase_gate["enabled"] is True

    projections = bundle["projections"]
    assert "client_configuration" in projections
    assert "business_inventory" in projections
    assert "phase0_scope_lock_status_snapshot" in projections

    ui_projection = projections["phase0_scope_lock_status_snapshot"]
    assert ui_projection["phase_chain"]["runtime_authority_blocked"] is True
    assert ui_projection["phase_chain"]["runtime_execution_blocked"] is True

    for key in ("client_configuration", "business_inventory"):
        projection = projections[key]
        assert projection["runtime_authority_blocked"] is True
        assert projection["runtime_execution_blocked"] is True
        assert projection["phase"] == "phase-1"


def test_phase1_readiness_bundle_matches_fixture_projection() -> None:
    assert READINESS_BUNDLE_FIXTURE_PATH.exists()

    bundle = build_phase1_readiness_bundle()
    expected = _load_json(READINESS_BUNDLE_FIXTURE_PATH)

    assert bundle == expected


def test_phase1_readiness_bundle_cli_preview_can_export(tmp_path: Path) -> None:
    output = io.StringIO()
    snapshot_path = tmp_path / "phase1_readiness_bundle.json"

    with patch("sys.stdout", output):
        status = run_phase1_readiness_bundle_preview(["--compact", f"--snapshot-path={snapshot_path}"])

    assert status == 0
    parsed_cli = json.loads(output.getvalue())
    parsed_file = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert parsed_cli == parsed_file
    assert parsed_cli["artifact_id"] == PHASE1_READINESS_BUNDLE_ID


def test_phase1_readiness_bundle_preview_without_client_config() -> None:
    bundle = build_phase1_readiness_bundle(
        include_client_config=False,
        include_business_inventory=True,
        include_scope_lock_snapshot=False,
    )

    assert "client_configuration" not in bundle["projections"]
    assert "business_inventory" in bundle["projections"]
    assert "phase0_scope_lock_status_snapshot" not in bundle["projections"]


def test_phase1_readiness_bundle_requires_at_least_one_projection() -> None:
    with pytest.raises(Phase1ReadinessBundleError):
        build_phase1_readiness_bundle(
            include_client_config=False,
            include_business_inventory=False,
            include_scope_lock_snapshot=False,
        )
