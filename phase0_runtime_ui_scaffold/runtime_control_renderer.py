"""Preview-only renderer projection for phase-2 runtime-control UI state.

This module is intentionally a renderer contract only. It does not create UI,
call a browser, open sockets, invoke models, dispatch workers, mutate files, or
grant runtime authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from .runtime_control_consumer import (
    Phase2RuntimeControlConsumerError,
    Phase2RuntimeControlConsumerShapeError,
    build_phase2_runtime_control_consumer_projection,
)


class RuntimeControlRendererShapeError(ValueError):
    """Raised when renderer projection input cannot be rendered safely."""


def _assert_consumer_guardrails(projection: Mapping[str, Any]) -> None:
    if projection.get("artifact_type") != "phase2_runtime_control_ui_consumer_projection":
        raise RuntimeControlRendererShapeError(
            "Runtime-control renderer requires phase-2 consumer projection input"
        )
    if projection.get("projection_scope") != "read_only":
        raise RuntimeControlRendererShapeError("Renderer input must remain read-only")
    if projection.get("source_access_mode") != "read_only":
        raise RuntimeControlRendererShapeError("Renderer input source must be read-only")
    if projection.get("runtime_authority_blocked") is not True:
        raise RuntimeControlRendererShapeError("Renderer requires blocked runtime authority")
    if projection.get("runtime_execution_blocked") is not True:
        raise RuntimeControlRendererShapeError("Renderer requires blocked runtime execution")


def _render_surface(surface: str, projection: Mapping[str, Any]) -> dict[str, Any]:
    if projection.get("ui_control_mode") != "preview_only":
        raise RuntimeControlRendererShapeError(
            f"Surface {surface} must remain preview-only before renderer handoff"
        )
    if projection.get("control_state") != "blocked_preview":
        raise RuntimeControlRendererShapeError(
            f"Surface {surface} must remain blocked_preview before renderer handoff"
        )

    blocked_runtime_actions = sorted(set(projection.get("blocked_runtime_actions", [])))
    if not blocked_runtime_actions:
        raise RuntimeControlRendererShapeError(
            f"Surface {surface} must preserve blocked runtime actions"
        )

    return {
        "surface": surface,
        "render_mode": "preview_only",
        "control_state": projection.get("control_state"),
        "view_type": projection.get("view_type"),
        "status": projection.get("status"),
        "operator_role": projection.get("operator_role"),
        "tenant_id": projection.get("tenant_id"),
        "customer_context_id": projection.get("customer_context_id"),
        "environment": projection.get("environment"),
        "render_controls": [
            {
                "control_id": f"{surface}.preview",
                "label": "preview",
                "enabled": True,
                "authority_required": False,
            },
            {
                "control_id": f"{surface}.execute",
                "label": "execute",
                "enabled": False,
                "authority_required": True,
            },
        ],
        "blocked_runtime_actions": blocked_runtime_actions,
        "policy_refs": sorted(projection.get("policy_refs", [])),
        "evidence_refs": sorted(projection.get("evidence_refs", [])),
        "runbook_refs": sorted(projection.get("runbook_refs", [])),
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
    }


def build_runtime_control_renderer_projection(
    *,
    control_contract_path: str | Path = Path(
        "tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json"
    ),
    control_payload_path: str | Path = Path(
        "tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json"
    ),
    include_surface_summary: bool = True,
) -> dict[str, Any]:
    """Build a bounded renderer projection from the phase-2 control consumer."""

    consumer_projection = build_phase2_runtime_control_consumer_projection(
        control_contract_path=control_contract_path,
        control_payload_path=control_payload_path,
        include_surface_summary=include_surface_summary,
    )
    _assert_consumer_guardrails(consumer_projection)

    rendered_surfaces = {
        surface: _render_surface(surface, surface_projection)
        for surface, surface_projection in consumer_projection["surfaces"].items()
    }

    return {
        "artifact_type": "phase2_runtime_control_renderer_projection",
        "artifact_id": consumer_projection.get("artifact_id"),
        "phase": consumer_projection.get("phase"),
        "projection_source": "phase2_runtime_control_ui_consumer_projection",
        "projection_scope": consumer_projection.get("projection_scope"),
        "source_reference": consumer_projection.get("source_reference"),
        "source_access_mode": consumer_projection.get("source_access_mode"),
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "phase_gate": consumer_projection.get("phase_gate"),
        "surface_bindings": sorted(rendered_surfaces),
        "surfaces": rendered_surfaces,
        "renderer_metadata": {
            "renderer_mode": "static_preview_contract",
            "execution_controls_enabled": False,
            "authority_mode": "blocked",
            "ingested_from": "phase2_runtime_control_ui_consumer_projection",
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a preview-only runtime-control renderer projection."
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


def run_runtime_control_renderer_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        rendered = build_runtime_control_renderer_projection(
            control_contract_path=Path(args.contract_path),
            control_payload_path=Path(args.payload_path),
        )
    except (
        RuntimeControlRendererShapeError,
        Phase2RuntimeControlConsumerError,
        Phase2RuntimeControlConsumerShapeError,
        OSError,
        ValueError,
    ) as err:
        print(f"runtime control renderer preview failed: {err}", file=sys.stderr)
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
    return run_runtime_control_renderer_preview()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
