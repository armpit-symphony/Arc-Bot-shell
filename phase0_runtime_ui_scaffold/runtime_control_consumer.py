"""Phase-2 runtime-control consumer handoff for downstream UI state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from .phase2_runtime_control import (
    Phase2RuntimeControlError,
    Phase2RuntimeControlShapeError,
    build_phase2_runtime_control_projection,
)


class Phase2RuntimeControlConsumerError(RuntimeError):
    """Raised when a phase-2 runtime-control consumer projection is not allowed."""


class Phase2RuntimeControlConsumerShapeError(ValueError):
    """Raised when phase-2 runtime-control consumer output is malformed."""


def _assert_control_projection_guardrails(projection: Mapping[str, Any]) -> None:
    if projection.get("artifact_type") != "phase2_runtime_control_handoff_projection":
        raise Phase2RuntimeControlConsumerShapeError(
            "Unexpected artifact_type for runtime-control consumer input"
        )

    if projection.get("projection_scope") != "read_only":
        raise Phase2RuntimeControlConsumerShapeError(
            "Runtime-control consumer requires read-only projection scope"
        )

    if projection.get("source_access_mode") != "read_only":
        raise Phase2RuntimeControlConsumerShapeError(
            "Runtime-control consumer requires read-only source access"
        )

    if projection.get("runtime_authority_blocked") is not True:
        raise Phase2RuntimeControlConsumerShapeError(
            "Runtime-control consumer requires runtime authority blocked"
        )

    for surface_projection in projection.get("surfaces", {}).values():
        if surface_projection.get("projection_mode") != "read_only":
            raise Phase2RuntimeControlConsumerShapeError(
                "Runtime-control consumer only supports read-only surface projections"
            )


def _build_surface_consumer_state(surface: str, projection: Mapping[str, Any]) -> dict[str, Any]:
    blocked_runtime_actions = set(projection.get("blocked_runtime_actions", []))
    if not blocked_runtime_actions:
        raise Phase2RuntimeControlConsumerShapeError(
            f"Surface {surface} must preserve blocked_runtime_actions for UI control seam"
        )

    metadata_actions = set(projection.get("metadata_actions", []))

    if projection.get("downstream_mode") != "read_only":
        raise Phase2RuntimeControlConsumerShapeError(
            f"Surface {surface} must remain downstream read-only mode"
        )
    if projection.get("handoff_posture") != "ui_control_handoff_read_only":
        raise Phase2RuntimeControlConsumerShapeError(
            f"Surface {surface} must remain ui_control_handoff_read_only"
        )

    return {
        "surface": surface,
        "downstream_mode": "read_only",
        "ui_control_mode": "preview_only",
        "projection_mode": projection.get("projection_mode"),
        "tenant_id": projection.get("tenant_id"),
        "customer_context_id": projection.get("customer_context_id"),
        "environment": projection.get("environment"),
        "operator_role": projection.get("operator_role"),
        "view_type": projection.get("view_type"),
        "status": projection.get("status"),
        "policy_refs": sorted(projection.get("policy_refs", [])),
        "evidence_refs": sorted(projection.get("evidence_refs", [])),
        "runbook_refs": sorted(projection.get("runbook_refs", [])),
        "contract_refs": sorted(set(projection.get("contract_refs", []))),
        "spine_sources": sorted(set(projection.get("spine_sources", []))),
        "metadata_actions": sorted(metadata_actions),
        "blocked_runtime_actions": sorted(blocked_runtime_actions),
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "control_state": "blocked_preview",
        "handoff_posture": "ui_state_handoff_read_only",
    }


def build_phase2_runtime_control_consumer_projection(
    *,
    control_contract_path: str | Path = Path(
        "tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json"
    ),
    control_payload_path: str | Path = Path(
        "tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json"
    ),
    enable_phase_gate: bool = True,
    include_surface_summary: bool = True,
) -> dict[str, Any]:
    """Build a bounded downstream consumer projection from the phase-2 handoff seam."""

    control_projection = build_phase2_runtime_control_projection(
        feed_contract_path=control_contract_path,
        feed_payload_path=control_payload_path,
        enable_phase_gate=enable_phase_gate,
    )

    _assert_control_projection_guardrails(control_projection)

    phase_gate = control_projection.get("phase_gate", {})
    if phase_gate.get("required") is not True:
        raise Phase2RuntimeControlConsumerError(
            "Runtime-control consumer requires enabled projection gate"
        )
    if phase_gate.get("enabled") is not True:
        raise Phase2RuntimeControlConsumerError(
            "Runtime-control consumer requires enabled projection gate"
        )

    surfaces = {}
    for surface, surface_projection in control_projection["surfaces"].items():
        surfaces[surface] = _build_surface_consumer_state(surface, surface_projection)

    if not surfaces:
        raise Phase2RuntimeControlConsumerShapeError(
            "Runtime-control consumer requires at least one surface"
        )

    output: dict[str, Any] = {
        "artifact_type": "phase2_runtime_control_ui_consumer_projection",
        "artifact_id": control_projection.get("artifact_id"),
        "phase": control_projection.get("phase"),
        "projection_source": "phase2_runtime_control_handoff_projection",
        "projection_scope": control_projection.get("projection_scope"),
        "source_reference": control_projection.get("source_reference"),
        "source_access_mode": control_projection.get("source_access_mode"),
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "phase_gate": phase_gate,
        "projection_bindings": control_projection.get("projection_bindings"),
        "surface_bindings": sorted(surfaces.keys()),
        "surfaces": surfaces,
        "consumer_metadata": {
            "consumer_mode": "read_only",
            "handoff_mode": "ui_state",
            "authority_mode": "blocked",
            "ingested_from": control_projection["projection_source"],
            "projection_gate": phase_gate.get("name"),
            "execution_allowed": False,
        },
    }

    if include_surface_summary:
        output["surface_summary"] = {
            "blocked_runtime_actions": sorted(
                set(
                    action
                    for surface_projection in surfaces.values()
                    for action in surface_projection["blocked_runtime_actions"]
                )
            ),
            "spine_sources": sorted(set(control_projection.get("projection_bindings", []))),
        }

    return output


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a downstream UI consumer projection from phase-2 control handoff."
    )
    parser.add_argument(
        "contract_path",
        nargs="?",
        default=str(
            Path("tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json")
        ),
        help=(
            "Path to the phase-1 read-feed contract fixture "
            "(defaults to tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json)"
        ),
    )
    parser.add_argument(
        "--payload-path",
        default=str(
            Path("tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json")
        ),
        help=(
            "Path to the phase-1 read-feed payload fixture "
            "(defaults to tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json)"
        ),
    )
    parser.add_argument(
        "--no-surface-summary",
        action="store_true",
        help="Do not include aggregated surface summary.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON.",
    )
    parser.add_argument(
        "--snapshot-path",
        help="Write rendered projection JSON to this file.",
    )
    return parser


def run_runtime_control_consumer_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        rendered = build_phase2_runtime_control_consumer_projection(
            control_contract_path=args.contract_path,
            control_payload_path=args.payload_path,
            include_surface_summary=not args.no_surface_summary,
        )
    except (
        Phase2RuntimeControlConsumerError,
        Phase2RuntimeControlConsumerShapeError,
        Phase2RuntimeControlError,
        Phase2RuntimeControlShapeError,
        OSError,
        ValueError,
    ) as err:
        print(f"runtime control consumer preview failed: {err}", file=sys.stderr)
        return 1
    if args.snapshot_path:
        Path(args.snapshot_path).write_text(
            json.dumps(
                rendered,
                sort_keys=True,
                indent=2 if not args.compact else None,
            )
            + "\n",
            encoding="utf-8",
        )

    json.dump(
        rendered,
        sys.stdout,
        indent=None if args.compact else 2,
        sort_keys=True,
    )
    sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_runtime_control_consumer_preview()


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
