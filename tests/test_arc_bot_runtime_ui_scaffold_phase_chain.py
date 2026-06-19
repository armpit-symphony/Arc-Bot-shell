"""Full preview-chain CLI and projection smoke tests."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

from phase0_runtime_ui_scaffold.phase_chain import (
    build_phase0_runtime_ui_scaffold_chain,
    build_phase0_runtime_ui_scaffold_status_snapshot,
    run_phase_chain_preview,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CHAIN_PACKET_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase0_scope_lock_chain_packet.json"
)
STATUS_SNAPSHOT_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase0_scope_lock_status_snapshot.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _compact_phase_chain(phase: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, object] = {}
    for key in [
        "artifact_id",
        "artifact_type",
        "phase",
        "payload_id",
        "payload_type",
        "projection_scope",
        "source_reference",
        "source_access_mode",
        "runtime_authority_blocked",
        "runtime_execution_blocked",
        "surface_bindings",
        "projection_bindings",
        "spine_sources",
        "spine_record_counts",
        "phase_gate",
    ]:
        if key in phase:
            compact[key] = phase[key]
    return compact


def _compact_chain(chain: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "artifact_id": chain["artifact_id"],
        "artifact_type": chain["artifact_type"],
        "phase": chain["phase"],
        "projection_scope": chain["projection_scope"],
        "runtime_authority_blocked": chain["runtime_authority_blocked"],
        "runtime_execution_blocked": chain["runtime_execution_blocked"],
        "source_reference": chain["source_reference"],
        "source_access_mode": chain["source_access_mode"],
        "include_guardian_suite_seam": chain["include_guardian_suite_seam"],
        "phase_markers": chain["phase_markers"],
        "surface_bindings": chain["surface_bindings"],
    }
    compact["phases"] = {
        phase_name: _compact_phase_chain(phase_data)
        for phase_name, phase_data in chain["phases"].items()
    }
    return compact


def test_build_phase_chain_projection() -> None:
    chain = build_phase0_runtime_ui_scaffold_chain()

    assert chain["artifact_type"] == "phase0_runtime_ui_scaffold_phase_chain_projection"
    assert chain["phase"] == "phase-1"
    assert chain["projection_scope"] == "read_only"
    assert chain["source_access_mode"] == "read_only"
    assert chain["runtime_authority_blocked"] is True
    assert chain["runtime_execution_blocked"] is True
    assert "phase_markers" in chain
    assert chain["include_guardian_suite_seam"] is False
    assert "phase0_guardian_suite_seam" not in chain["phases"]

    phases = chain["phases"]
    assert set(phases.keys()) == {
        "phase1_read_feed_contract",
        "phase1_read_feed_runtime",
        "phase1_runtime_consumer",
        "phase2_control",
        "phase2_control_consumer",
    }
    assert phases["phase1_read_feed_contract"]["phase"] == "phase-1"
    assert phases["phase2_control_consumer"]["runtime_execution_blocked"] is True


def test_build_phase_chain_projection_with_guardian_suite_seam() -> None:
    chain = build_phase0_runtime_ui_scaffold_chain(include_guardian_suite_seam=True)
    guardian_projection = chain["phases"]["phase0_guardian_suite_seam"]

    assert guardian_projection["artifact_type"] == "guardian_suite_spine_projection"
    assert guardian_projection["phase"] == chain["phase"]
    assert guardian_projection["source_reference"] == chain["source_reference"]
    assert guardian_projection["phase_gate"]["enabled"] is True
    assert chain["include_guardian_suite_seam"] is True

    assert set(guardian_projection["surfaces"]) == set(chain["surface_bindings"])


def test_run_phase_chain_preview_cli_compact() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_phase_chain_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_type"] == "phase0_runtime_ui_scaffold_phase_chain_projection"
    assert parsed["phase_markers"]["execution_mode"] == "disabled"
    assert parsed["include_guardian_suite_seam"] is False
    assert "phase0_guardian_suite_seam" not in parsed["phases"]

    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_phase_chain_preview(["--with-guardian-suite-seam", "--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["include_guardian_suite_seam"] is True
    assert parsed["phases"]["phase0_guardian_suite_seam"]["artifact_type"] == "guardian_suite_spine_projection"

    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_phase_chain_preview(
            ["--emit-status-snapshot", "--with-guardian-suite-seam", "--compact"]
        )

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["snapshot_id"] == "arc_bot_runtime_ui_scaffold_phase0_scope_lock_status_snapshot_v1"
    assert "phase_chain" in parsed
    assert parsed["phase_chain"]["artifact_type"] == "phase0_runtime_ui_scaffold_phase_chain_projection"


def test_run_phase_chain_preview_cli_status_snapshot_export(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "phase_chain_status_snapshot.json"
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_phase_chain_preview(
            [
                "--emit-status-snapshot",
                "--with-guardian-suite-seam",
                "--compact",
                f"--status-snapshot-path={snapshot_path}",
            ]
        )

    assert status == 0
    cli_payload = json.loads(output.getvalue())
    file_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert cli_payload == file_payload
    assert "phase_chain" in file_payload
    assert (
        file_payload["phase_chain"]["artifact_type"]
        == "phase0_runtime_ui_scaffold_phase_chain_projection"
    )


def test_run_phase_chain_preview_cli_status_snapshot_without_guardian_suite_seam() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_phase_chain_preview(
            ["--emit-status-snapshot", "--no-guardian-suite-seam", "--compact"]
        )

    assert status == 0
    parsed = json.loads(output.getvalue())

    assert parsed["phase_chain"]["include_guardian_suite_seam"] is False
    assert "phase0_guardian_suite_seam" not in parsed["phase_chain"]["phases"]


def test_run_phase_chain_preview_cli_status_snapshot_path_requires_snapshot_mode(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "phase_chain_status_snapshot.json"
    output = io.StringIO()

    with patch("sys.stderr", output):
        status = run_phase_chain_preview(["--status-snapshot-path", str(snapshot_path)])

    assert status == 1
    assert "status-snapshot-path requires --emit-status-snapshot" in output.getvalue()
    assert not snapshot_path.exists()


def test_phase_chain_scope_lock_packet_matches_fixture() -> None:
    chain = _compact_chain(
        build_phase0_runtime_ui_scaffold_chain(
            include_guardian_suite_seam=True,
        )
    )
    expected = _load_json(CHAIN_PACKET_PATH)

    assert chain == expected


def test_phase_chain_scope_lock_status_snapshot_matches_fixture() -> None:
    status_snapshot = build_phase0_runtime_ui_scaffold_status_snapshot()
    expected_status_snapshot = _load_json(STATUS_SNAPSHOT_PATH)

    assert status_snapshot == expected_status_snapshot


def test_phase_chain_surfaces_remain_locked_across_all_phases() -> None:
    chain = build_phase0_runtime_ui_scaffold_chain()
    expected_surfaces = {"work_queue", "runtime_settings", "overview"}

    assert set(chain["surface_bindings"]) == expected_surfaces

    feed_contract = chain["phases"]["phase1_read_feed_contract"]
    assert set(feed_contract["surface_read_paths"].keys()) == expected_surfaces
    assert feed_contract["source_reference"] == "app.services.guardian.suite"
    assert feed_contract["source_access_mode"] == "read_only"
    assert feed_contract["projection_scope"] == "read_only"

    assert set(chain["phases"]["phase1_read_feed_runtime"]["surface_bindings"]) == expected_surfaces
    assert set(chain["phases"]["phase1_runtime_consumer"]["surface_bindings"]) == expected_surfaces
    assert set(chain["phases"]["phase2_control"]["surface_bindings"]) == expected_surfaces
    assert set(chain["phases"]["phase2_control_consumer"]["surface_bindings"]) == expected_surfaces

    assert chain["phases"]["phase1_runtime_consumer"]["runtime_authority_blocked"] is True
    assert chain["phases"]["phase2_control"]["runtime_authority_blocked"] is True
    assert chain["phases"]["phase2_control_consumer"]["runtime_execution_blocked"] is True


def test_phase_chain_outputs_keep_reference_and_blocks() -> None:
    chain = build_phase0_runtime_ui_scaffold_chain(include_guardian_suite_seam=True)

    assert chain["source_reference"] == "app.services.guardian.suite"
    assert chain["source_access_mode"] == "read_only"
    assert chain["runtime_authority_blocked"] is True
    assert chain["runtime_execution_blocked"] is True

    for phase_projection in chain["phases"].values():
        assert phase_projection["source_reference"] == "app.services.guardian.suite"
        assert phase_projection["source_access_mode"] == "read_only"
        if "runtime_authority_blocked" in phase_projection:
            assert phase_projection["runtime_authority_blocked"] is True
        if "runtime_execution_blocked" in phase_projection:
            assert phase_projection["runtime_execution_blocked"] is True
        surfaces = phase_projection.get("surfaces")
        if not isinstance(surfaces, dict):
            continue
        for surface_projection in surfaces.values():
            if isinstance(surface_projection, dict):
                if "runtime_authority_blocked" in surface_projection:
                    assert surface_projection["runtime_authority_blocked"] is True
                if "runtime_execution_blocked" in surface_projection:
                    assert surface_projection["runtime_execution_blocked"] is True
