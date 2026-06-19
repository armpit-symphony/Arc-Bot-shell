"""Phase-2 runtime-control handoff for read-only UI state.

This module intentionally remains preview-only:
- no provider/model calls,
- no connector reads/writes,
- no file mutations,
- no runtime execution,
- no LIMA write pathways.

It translates a validated phase-1 runtime UI consumer projection into a
downstream control-seam payload intended for UI handoff components.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from .runtime_consumer import build_phase1_runtime_ui_consumer_projection


class Phase2RuntimeControlError(RuntimeError):
    """Raised when a phase-2 control seam projection is not allowed."""


class Phase2RuntimeControlShapeError(ValueError):
    """Raised when phase-2 control handoff projection is malformed."""


def _assert_projection_guardrails(projection: Mapping[str, Any]) -> None:
    if projection.get("projection_mode") == "execute":
        raise Phase2RuntimeControlShapeError("projection_mode must not be execute")

    if projection.get("phase") != "phase-1":
        raise Phase2RuntimeControlShapeError(
            f"Phase-2 handoff requires phase-1 input, received: {projection.get('phase')}"
        )

    if projection.get("projection_scope") != "read_only":
        raise Phase2RuntimeControlShapeError(
            "Phase-2 control-seam handoff requires read-only projection scope"
        )

    if projection.get("source_access_mode") != "read_only":
        raise Phase2RuntimeControlShapeError(
            "Phase-2 control-seam handoff requires read-only source access"
        )

    if projection.get("runtime_authority_blocked") is not True:
        raise Phase2RuntimeControlShapeError(
            "Phase-2 control-seam handoff requires runtime authority blocked"
        )


def _assert_read_only_view(surface_projection: Mapping[str, Any], surface: str) -> None:
    if surface_projection.get("projection_mode") != "read_only":
        raise Phase2RuntimeControlShapeError(
            f"Surface {surface} must be read-only for phase-2 control seam"
        )


def _build_surface_control_payload(
    surface: str,
    surface_projection: Mapping[str, Any],
) -> dict[str, Any]:
    _assert_read_only_view(surface_projection, surface)

    if surface_projection.get("view_type") is None:
        raise Phase2RuntimeControlShapeError(
            f"Surface {surface} projection is missing view_type field"
        )

    required_envelope_fields = (
        "tenant_id",
        "customer_context_id",
        "environment",
        "operator_role",
        "view_type",
        "status",
    )
    for required_field in required_envelope_fields:
        if surface_projection.get(required_field) is None:
            raise Phase2RuntimeControlShapeError(
                f"Surface {surface} is missing required envelope field {required_field}"
            )

    blocked_runtime_actions = set(surface_projection.get("blocked_runtime_actions", []))
    if not blocked_runtime_actions:
        raise Phase2RuntimeControlShapeError(
            f"Surface {surface} projection must preserve blocked runtime actions"
        )

    blocked_runtime_actions_all = sorted(blocked_runtime_actions)
    metadata_actions = sorted(set(surface_projection.get("metadata_actions", [])))
    contract_refs = sorted(set(surface_projection.get("contract_refs", [])))
    spine_sources = sorted(set(surface_projection.get("spine_sources", [])))

    return {
        "surface": surface,
        "downstream_mode": "read_only",
        "projection_mode": surface_projection.get("projection_mode"),
        "tenant_id": surface_projection.get("tenant_id"),
        "customer_context_id": surface_projection.get("customer_context_id"),
        "environment": surface_projection.get("environment"),
        "operator_role": surface_projection.get("operator_role"),
        "view_type": surface_projection.get("view_type"),
        "status": surface_projection.get("status"),
        "policy_refs": surface_projection.get("policy_refs", []),
        "evidence_refs": surface_projection.get("evidence_refs", []),
        "runbook_refs": surface_projection.get("runbook_refs", []),
        "contract_refs": contract_refs,
        "spine_sources": spine_sources,
        "metadata_actions": metadata_actions,
        "blocked_runtime_actions": blocked_runtime_actions_all,
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "handoff_posture": "ui_control_handoff_read_only",
    }


def build_phase2_runtime_control_projection(
    *,
    feed_contract_path: str | Path = Path(
        "tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json"
    ),
    feed_payload_path: str | Path = Path(
        "tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json"
    ),
    enable_phase_gate: bool = True,
    include_runtime_summary: bool = True,
) -> dict[str, Any]:
    """Build a static phase-2 control-seam handoff payload from phase-1 consumer data."""

    projection = build_phase1_runtime_ui_consumer_projection(
        feed_contract_path=feed_contract_path,
        feed_payload_path=feed_payload_path,
        enable_phase_gate=enable_phase_gate,
    )

    _assert_projection_guardrails(projection)

    phase_gate = projection.get("phase_gate", {})
    if phase_gate.get("required") is not True:
        raise Phase2RuntimeControlError("Phase-2 handoff requires enabled phase gate")
    if phase_gate.get("enabled") is not True:
        raise Phase2RuntimeControlError("Phase-2 handoff requires enabled phase gate")

    surfaced: dict[str, Any] = {}
    for surface, surface_projection in projection["surfaces"].items():
        surfaced[surface] = _build_surface_control_payload(
            surface,
            surface_projection,
        )

    if not surfaced:
        raise Phase2RuntimeControlShapeError("Projection must include at least one surface")

    output: dict[str, Any] = {
        "artifact_type": "phase2_runtime_control_handoff_projection",
        "artifact_id": projection.get("artifact_id"),
        "phase": projection.get("phase"),
        "projection_source": "phase1_runtime_ui_consumer_projection",
        "projection_scope": projection.get("projection_scope"),
        "source_reference": projection.get("source_reference"),
        "source_access_mode": projection.get("source_access_mode"),
        "phase_gate": phase_gate,
        "runtime_authority_blocked": projection.get("runtime_authority_blocked"),
        "surface_bindings": sorted(surfaced.keys()),
        "surfaces": surfaced,
        "handoff_metadata": {
            "handoff_mode": "downstream_ui_state",
            "authority_mode": "blocked",
            "ingested_from": "phase1_runtime_ui_consumer_projection",
            "projection_gate": phase_gate.get("name"),
        },
        "projection_bindings": projection.get("spine_sources"),
    }

    if include_runtime_summary:
        runtime_summary = projection.get("spine_source_records", {})
        output["spine_source_record_counts"] = {
            source: (len(records) if isinstance(records, list) else int(records) if isinstance(records, int) else 0)
            for source, records in runtime_summary.items()
        }

    return output


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a phase-2 control-seam read-only projection for UI handoff."
    )
    parser.add_argument(
        "contract_path",
        nargs="?",
        default="tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json",
        help=(
            "Path to the phase-1 read-feed contract fixture "
            "(defaults to tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json)"
        ),
    )
    parser.add_argument(
        "--payload-path",
        default="tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json",
        help=(
            "Path to the phase-1 read-feed payload fixture "
            "(defaults to tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json)"
        ),
    )
    parser.add_argument(
        "--no-runtime-summary",
        action="store_true",
        help="Do not include spine source record counts.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON.",
    )
    return parser


def run_phase2_runtime_control_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        rendered = build_phase2_runtime_control_projection(
            feed_contract_path=Path(args.contract_path),
            feed_payload_path=Path(args.payload_path),
            include_runtime_summary=not args.no_runtime_summary,
        )
    except (Phase2RuntimeControlError, Phase2RuntimeControlShapeError, OSError, ValueError) as err:
        print(f"phase2 runtime control preview failed: {err}", file=sys.stderr)
        return 1

    json.dump(
        rendered,
        sys.stdout,
        indent=None if args.compact else 2,
        sort_keys=True,
    )
    sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_phase2_runtime_control_preview()


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
