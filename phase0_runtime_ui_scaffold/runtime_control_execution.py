"""Phase-3 execution-planning projection for runtime-control UI state.

This is a planning artifact only. It models which controls would require future
Guardian/LIMA Office authority and keeps every executable action blocked.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from .runtime_control_renderer import (
    RuntimeControlRendererShapeError,
    build_runtime_control_renderer_projection,
)


class RuntimeControlExecutionPlanningError(ValueError):
    """Raised when execution planning would imply runtime authority."""


def _assert_renderer_guardrails(projection: Mapping[str, Any]) -> None:
    if projection.get("artifact_type") != "phase2_runtime_control_renderer_projection":
        raise RuntimeControlExecutionPlanningError(
            "Execution planning requires runtime-control renderer projection input"
        )
    if projection.get("runtime_authority_blocked") is not True:
        raise RuntimeControlExecutionPlanningError("Runtime authority must remain blocked")
    if projection.get("runtime_execution_blocked") is not True:
        raise RuntimeControlExecutionPlanningError("Runtime execution must remain blocked")
    metadata = projection.get("renderer_metadata", {})
    if metadata.get("execution_controls_enabled") is not False:
        raise RuntimeControlExecutionPlanningError(
            "Renderer execution controls must remain disabled"
        )


def _plan_surface(surface: str, projection: Mapping[str, Any]) -> dict[str, Any]:
    controls = projection.get("render_controls", [])
    planned_controls: list[dict[str, Any]] = []
    for control in controls:
        control_id = str(control.get("control_id", ""))
        is_execute_control = control_id.endswith(".execute")
        planned_controls.append(
            {
                "control_id": control_id,
                "planned_state": "blocked" if is_execute_control else "preview_only",
                "future_gate_required": bool(is_execute_control),
                "execution_allowed": False,
                "required_future_authority": (
                    "guardian_runtime_authority_approval"
                    if is_execute_control
                    else "none"
                ),
            }
        )

    if not planned_controls:
        raise RuntimeControlExecutionPlanningError(
            f"Surface {surface} has no controls to plan"
        )

    return {
        "surface": surface,
        "planning_mode": "execution_blocked",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "blocked_runtime_actions": sorted(set(projection.get("blocked_runtime_actions", []))),
        "planned_controls": planned_controls,
    }


def build_runtime_control_execution_planning_projection(
    *,
    control_contract_path: str | Path = Path(
        "tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json"
    ),
    control_payload_path: str | Path = Path(
        "tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json"
    ),
) -> dict[str, Any]:
    """Build a phase-3 planning projection with execution still blocked."""

    renderer_projection = build_runtime_control_renderer_projection(
        control_contract_path=control_contract_path,
        control_payload_path=control_payload_path,
    )
    _assert_renderer_guardrails(renderer_projection)

    planned_surfaces = {
        surface: _plan_surface(surface, surface_projection)
        for surface, surface_projection in renderer_projection["surfaces"].items()
    }

    return {
        "artifact_type": "phase3_runtime_control_execution_planning_projection",
        "artifact_id": renderer_projection.get("artifact_id"),
        "phase": "phase-3-planning",
        "projection_source": "phase2_runtime_control_renderer_projection",
        "projection_scope": renderer_projection.get("projection_scope"),
        "source_reference": renderer_projection.get("source_reference"),
        "source_access_mode": renderer_projection.get("source_access_mode"),
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "surface_bindings": sorted(planned_surfaces),
        "surfaces": planned_surfaces,
        "execution_planning_metadata": {
            "execution_plan_mode": "blocked_projection",
            "execution_allowed": False,
            "future_authority_owner": "LIMA Office / Guardian",
            "required_future_gates": [
                "guardian_runtime_authority_approval",
                "approval_token_lineage",
                "evidence_and_rollback_gate",
            ],
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render phase-3 execution planning with execution blocked."
    )
    parser.add_argument(
        "contract_path",
        nargs="?",
        default="tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json",
        help="Path to the phase-1 read-feed contract fixture.",
    )
    parser.add_argument(
        "--payload-path",
        default="tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json",
        help="Path to the phase-1 read-feed payload fixture.",
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument("--snapshot-path", help="Write rendered projection JSON to this file.")
    return parser


def run_runtime_control_execution_planning_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        rendered = build_runtime_control_execution_planning_projection(
            control_contract_path=Path(args.contract_path),
            control_payload_path=Path(args.payload_path),
        )
    except (
        RuntimeControlExecutionPlanningError,
        RuntimeControlRendererShapeError,
        OSError,
        ValueError,
    ) as err:
        print(f"runtime control execution planning preview failed: {err}", file=sys.stderr)
        return 1

    if args.snapshot_path:
        Path(args.snapshot_path).write_text(
            json.dumps(rendered, sort_keys=True, indent=2 if not args.compact else None)
            + "\n",
            encoding="utf-8",
        )

    json.dump(rendered, sys.stdout, indent=None if args.compact else 2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_runtime_control_execution_planning_preview()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
