"""Phase-1 business shell inventory contract tests."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

from phase1_business_shell_inventory import (
    DEFAULT_INVENTORY_PATH,
    InventoryPhaseGateError,
    InventorySchemaError,
    build_phase1_business_inventory_projection,
    run_phase1_inventory_preview,
)


def test_phase1_business_inventory_projection_builds_readonly_projection() -> None:
    projection = build_phase1_business_inventory_projection(
        inventory_path=DEFAULT_INVENTORY_PATH,
        enable_phase_gate=True,
    )

    assert projection["artifact_type"] == "phase1_business_shell_inventory_projection"
    assert projection["phase"] == "phase-1"
    assert projection["projection_scope"] == "planning_read_only"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["source_access_mode"] == "docs_only"
    assert projection["source_reference"] == "docs/OPERATOR_CONSOLE_FOUNDATION.md"
    assert projection["phase_gate"]["enabled"] is True
    assert projection["phase_gate"]["name"] == "ARC_BOT_PHASE1_BUSINESS_INVENTORY"
    assert projection["roles_count"] == 3

    surface_bindings = projection["surface_bindings"]
    assert set(surface_bindings) == {
        "connectors",
        "evidence",
        "governance",
        "guardian",
        "model_local_readiness",
        "overview",
        "approvals",
        "runbooks",
        "runtime_settings",
        "tasks",
        "work_queue",
        "workers",
    }

    for surface_id, surface_projection in projection["surfaces"].items():
        assert surface_projection["projection_mode"] == "read_only"
        assert surface_projection["runtime_authority_blocked"] is True
        assert surface_projection["runtime_execution_blocked"] is True
        assert isinstance(surface_projection["blocked_runtime_actions"], list)
        assert isinstance(surface_projection["required_status_modes"], list)
        assert isinstance(surface_projection["metadata_actions"], list)


def test_phase1_business_inventory_preview_cli_compact_and_projection_id() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_phase1_inventory_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_type"] == "phase1_business_shell_inventory_projection"
    assert parsed["artifact_id"] == "arc_bot_phase1_business_shell_inventory_v1"
    assert "surface_bindings" in parsed


def test_phase1_business_inventory_preview_cli_can_export_snapshot(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "phase1_inventory_projection.json"
    output = io.StringIO()

    with patch("sys.stdout", output):
        status = run_phase1_inventory_preview(
            ["--compact", f"--snapshot-path={snapshot_path}", str(DEFAULT_INVENTORY_PATH)]
        )

    assert status == 0
    cli_payload = json.loads(output.getvalue())
    file_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert cli_payload == file_payload


def test_phase1_business_inventory_preview_fails_without_gate() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_phase1_inventory_preview(["--compact", "--no-phase-gate"])

    assert status == 1


def test_phase1_business_inventory_phase_gate_enforcement(tmp_path: Path) -> None:
    bad = json.loads(
        Path(DEFAULT_INVENTORY_PATH).read_text(encoding="utf-8-sig")
    )
    bad["phase_gate"]["name"] = "BAD_GATE"

    bad_path = tmp_path / "arc_bot_phase1_business_inventory_bad_gate.json"
    bad_path.write_text(json.dumps(bad, indent=2, sort_keys=True), encoding="utf-8")

    try:
        build_phase1_business_inventory_projection(
            inventory_path=bad_path,
            enable_phase_gate=True,
        )
        raise AssertionError("expected InventoryPhaseGateError")
    except (InventoryPhaseGateError, InventorySchemaError):
        pass
