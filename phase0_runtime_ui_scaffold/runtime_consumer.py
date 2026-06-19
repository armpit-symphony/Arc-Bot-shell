"""Phase-1 runtime UI consumer seam for read-only projections.

This module intentionally keeps runtime behavior out of scope.
It transforms a validated phase-1 read-feed projection into a
consumer-oriented surface summary with explicit read-only invariants.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from .read_feed import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_PAYLOAD_PATH,
    ReadFeedGateError,
    ReadFeedPayloadError,
    build_phase1_read_feed_runtime_projection,
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReadFeedPayloadError(f"Expected JSON object at {path}")
    return payload


def _assert_read_only_projection(
    projection: Mapping[str, Any], surface: str | None = None
) -> None:
    if projection.get("projection_mode") != "read_only":
        raise ReadFeedPayloadError(
            "Runtime UI consumer seam only supports read-only surface projection"
            + (f" for {surface}" if surface else "")
        )


def _build_surface_projection(
    surface: str, surface_projection: Mapping[str, Any]
) -> dict[str, Any]:
    snapshot = surface_projection.get("snapshot")
    if not isinstance(snapshot, Mapping):
        raise ReadFeedPayloadError(f"Missing snapshot for surface {surface}")

    envelope = snapshot.get("envelope")
    if not isinstance(envelope, Mapping):
        raise ReadFeedPayloadError(f"Missing envelope for surface {surface}")

    _assert_read_only_projection(surface_projection, surface)

    blocked_runtime_actions = list(dict.fromkeys(surface_projection.get("blocked_runtime_actions", [])))
    contract_refs = list(dict.fromkeys(surface_projection.get("contract_refs", [])))

    return {
        "surface": surface,
        "projection_mode": surface_projection.get("projection_mode"),
        "view_type": envelope.get("view_type"),
        "status": envelope.get("status"),
        "tenant_id": envelope.get("tenant_id"),
        "customer_context_id": envelope.get("customer_context_id"),
        "environment": envelope.get("environment"),
        "operator_role": envelope.get("operator_role"),
        "policy_refs": envelope.get("policy_refs", []),
        "evidence_refs": envelope.get("evidence_refs", []),
        "runbook_refs": envelope.get("runbook_refs", []),
        "blocked_runtime_actions": sorted(set(blocked_runtime_actions)),
        "contract_refs": sorted(set(contract_refs)),
        "spine_sources": sorted(set(surface_projection.get("spine_sources", []))),
        "metadata_actions": sorted(set(snapshot.get("metadata_actions", []))),
        "snapshot_surface": snapshot.get("surface"),
        "snapshot_view_mode": envelope.get("view_mode"),
    }


def build_phase1_runtime_ui_consumer_projection(
    *,
    feed_contract_path: str | Path = DEFAULT_CONTRACT_PATH,
    feed_payload_path: str | Path = DEFAULT_PAYLOAD_PATH,
    enable_phase_gate: bool = True,
    include_runtime_summary: bool = True,
) -> dict[str, Any]:
    """Build a read-only runtime UI consumer projection from a feed payload."""

    runtime_projection = build_phase1_read_feed_runtime_projection(
        feed_contract_path=feed_contract_path,
        feed_payload_path=feed_payload_path,
        enable_phase_gate=enable_phase_gate,
    )

    payload = _load_json(Path(feed_payload_path))
    spine_source_records = payload.get("spine_source_records")
    if not isinstance(spine_source_records, Mapping):
        raise ReadFeedPayloadError("Read-feed payload must include spine_source_records")

    projected_surfaces: dict[str, Any] = {}
    for surface, projection_data in runtime_projection["surfaces"].items():
        projected_surfaces[surface] = _build_surface_projection(surface, projection_data)

    if not projected_surfaces:
        raise ReadFeedPayloadError("Read-feed payload must include at least one surface")

    return {
        "artifact_type": "phase1_runtime_ui_consumer_projection",
        "artifact_id": runtime_projection["artifact_id"],
        "phase": runtime_projection["phase"],
        "payload_id": runtime_projection["payload_id"],
        "projection_source_file": str(Path(feed_contract_path)),
        "projection_scope": runtime_projection["projection_scope"],
        "source_reference": runtime_projection["source_reference"],
        "source_access_mode": runtime_projection["source_access_mode"],
        "phase_gate": runtime_projection["phase_gate"],
        "ingested_at": runtime_projection["ingested_at"],
        "runtime_authority_blocked": True,
        "surface_bindings": sorted(projected_surfaces.keys()),
        "surfaces": projected_surfaces,
        "spine_sources": runtime_projection["spine_sources"],
        "spine_source_records": {
            source: len(records) if include_runtime_summary else None
            for source, records in spine_source_records.items()
            if source in runtime_projection["spine_sources"]
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render Phase-1 runtime UI consumer projection from read-feed payload."
    )
    parser.add_argument(
        "contract_path",
        nargs="?",
        default=str(DEFAULT_CONTRACT_PATH),
        help=(
            "Path to the phase-1 read-feed contract "
            "(defaults to tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json)"
        ),
    )
    parser.add_argument(
        "--payload-path",
        default=str(DEFAULT_PAYLOAD_PATH),
        help=(
            "Path to a phase-1 read-feed payload "
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


def run_runtime_consumer_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        projection = build_phase1_runtime_ui_consumer_projection(
            feed_contract_path=Path(args.contract_path),
            feed_payload_path=Path(args.payload_path),
            include_runtime_summary=not args.no_runtime_summary,
        )
    except (ReadFeedGateError, ReadFeedPayloadError, OSError, ValueError) as err:
        print(f"runtime consumer preview failed: {err}", file=sys.stderr)
        return 1

    json.dump(
        projection,
        sys.stdout,
        indent=None if args.compact else 2,
        sort_keys=True,
    )
    sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_runtime_consumer_preview()


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
