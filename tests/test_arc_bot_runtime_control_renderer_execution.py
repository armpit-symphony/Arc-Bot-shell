"""Runtime-control renderer and execution-planning previews stay blocked."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

from phase0_runtime_ui_scaffold.runtime_control_execution import (
    build_runtime_control_execution_planning_projection,
    run_runtime_control_execution_planning_preview,
)
from phase0_runtime_ui_scaffold.runtime_control_renderer import (
    build_runtime_control_renderer_projection,
    run_runtime_control_renderer_preview,
)


def test_runtime_control_renderer_projection_is_preview_only() -> None:
    projection = build_runtime_control_renderer_projection()

    assert projection["artifact_type"] == "phase2_runtime_control_renderer_projection"
    assert projection["projection_scope"] == "read_only"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["renderer_metadata"]["execution_controls_enabled"] is False

    for surface in projection["surfaces"].values():
        assert surface["render_mode"] == "preview_only"
        assert surface["runtime_authority_blocked"] is True
        assert surface["runtime_execution_blocked"] is True
        execute_controls = [
            control for control in surface["render_controls"] if control["label"] == "execute"
        ]
        assert execute_controls
        assert all(control["enabled"] is False for control in execute_controls)


def test_runtime_control_execution_planning_projection_blocks_execution() -> None:
    projection = build_runtime_control_execution_planning_projection()

    assert projection["artifact_type"] == "phase3_runtime_control_execution_planning_projection"
    assert projection["phase"] == "phase-3-planning"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["execution_planning_metadata"]["execution_allowed"] is False

    for surface in projection["surfaces"].values():
        assert surface["planning_mode"] == "execution_blocked"
        assert surface["runtime_authority_blocked"] is True
        assert surface["runtime_execution_blocked"] is True
        assert any(
            control["future_gate_required"] is True
            for control in surface["planned_controls"]
        )
        assert all(
            control["execution_allowed"] is False
            for control in surface["planned_controls"]
        )


def test_runtime_control_renderer_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_runtime_control_renderer_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_type"] == "phase2_runtime_control_renderer_projection"
    assert parsed["renderer_metadata"]["execution_controls_enabled"] is False


def test_runtime_control_execution_planning_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_runtime_control_execution_planning_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_type"] == "phase3_runtime_control_execution_planning_projection"
    assert parsed["execution_planning_metadata"]["execution_allowed"] is False
