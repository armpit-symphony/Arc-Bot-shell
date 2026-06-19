"""Phase-1 client configuration projection and preview gate checks."""

from __future__ import annotations

import io
import json
from pathlib import Path

from phase1_client_configuration import (
    DEFAULT_CLIENT_CONFIGURATION_PATH,
    ClientConfigurationPhaseGateError,
    ClientConfigurationSchemaError,
    build_phase1_client_configuration_projection,
    run_phase1_client_configuration_preview,
)


def test_phase1_client_configuration_projection_builds_readonly_projection() -> None:
    projection = build_phase1_client_configuration_projection(
        client_configuration_path=DEFAULT_CLIENT_CONFIGURATION_PATH,
        enable_phase_gate=True,
    )

    assert projection["artifact_type"] == "phase1_client_configuration_projection"
    assert projection["phase"] == "phase-1"
    assert projection["projection_scope"] == "planning_read_only"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["source_access_mode"] == "read_only"
    assert projection["phase_gate"]["enabled"] is True
    assert projection["phase_gate"]["name"] == "ARC_BOT_PHASE1_CLIENT_CONFIGURATION"
    assert projection["operator_roles_count"] >= 1
    assert projection["connector_profiles_count"] >= 1
    for action in projection["blocked_runtime_actions"]:
        assert action


def test_phase1_client_configuration_preview_cli_compact_and_projection_id() -> None:
    output = io.StringIO()
    import sys
    from unittest.mock import patch

    with patch("sys.stdout", output):
        status = run_phase1_client_configuration_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_type"] == "phase1_client_configuration_projection"
    assert parsed["artifact_id"] == "arc_bot_phase1_client_configuration_v1"
    assert parsed["projection_scope"] == "planning_read_only"


def test_phase1_client_configuration_preview_cli_can_export_snapshot(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "phase1_client_configuration_projection.json"
    output = io.StringIO()
    from unittest.mock import patch

    with patch("sys.stdout", output):
        status = run_phase1_client_configuration_preview(
            [
                "--compact",
                f"--snapshot-path={snapshot_path}",
                str(DEFAULT_CLIENT_CONFIGURATION_PATH),
            ]
        )

    assert status == 0
    cli_payload = json.loads(output.getvalue())
    file_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert cli_payload == file_payload


def test_phase1_client_configuration_preview_fails_without_gate() -> None:
    output = io.StringIO()
    from unittest.mock import patch

    with patch("sys.stdout", output):
        status = run_phase1_client_configuration_preview(["--compact", "--no-phase-gate"])

    assert status == 1


def test_phase1_client_configuration_projection_enforces_phase_gate_match(tmp_path: Path) -> None:
    bad = json.loads(Path(DEFAULT_CLIENT_CONFIGURATION_PATH).read_text(encoding="utf-8-sig"))
    bad["phase_gate"]["name"] = "BAD_GATE"

    bad_path = tmp_path / "arc_bot_phase1_client_configuration_bad_gate.json"
    bad_path.write_text(json.dumps(bad, indent=2, sort_keys=True), encoding="utf-8")

    try:
        build_phase1_client_configuration_projection(
            client_configuration_path=bad_path,
            enable_phase_gate=True,
        )
        raise AssertionError("expected ClientConfigurationPhaseGateError")
    except (ClientConfigurationPhaseGateError, ClientConfigurationSchemaError):
        pass
