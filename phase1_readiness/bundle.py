"""Phase-1 locked readiness bundle preview."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from phase0_runtime_ui_scaffold import build_phase0_runtime_ui_scaffold_status_snapshot
from phase1_business_shell_inventory import build_phase1_business_inventory_projection
from phase1_client_configuration import build_phase1_client_configuration_projection
from phase1_runtime_authority_gating import build_phase1_runtime_authority_gating_projection

PHASE1_READINESS_BUNDLE_ID = "arc_bot_phase1_readiness_bundle_v1"
EXPECTED_PHASE = "phase-1"


class Phase1ReadinessBundleError(RuntimeError):
    """Raised when a phase-1 readiness bundle cannot be safely assembled."""


def _compact_projection(projection: dict[str, Any]) -> dict[str, Any]:
    """Collapse large read-only projections to deterministic bundle metadata."""
    compacted_projection = {
        "artifact_id": projection["artifact_id"],
        "artifact_type": projection["artifact_type"],
        "phase": projection.get("phase"),
        "projection_scope": projection["projection_scope"],
        "source_access_mode": projection["source_access_mode"],
        "runtime_authority_blocked": projection["runtime_authority_blocked"],
        "runtime_execution_blocked": projection.get("runtime_execution_blocked", True),
        "phase_gate": projection["phase_gate"],
    }

    if projection["artifact_type"] == "phase1_runtime_authority_gating_pack":
        compacted_projection["required_gates"] = projection["required_gates"]
        compacted_projection["unresolved_required_gates"] = projection[
            "unresolved_required_gates"
        ]
        compacted_projection["surface_bindings"] = projection["surface_bindings"]
        compacted_projection["intent_count"] = projection["intent_count"]

    return compacted_projection


def build_phase1_readiness_bundle(
    *,
    include_client_config: bool = True,
    include_business_inventory: bool = True,
    include_scope_lock_snapshot: bool = True,
    include_guardian_suite_seam: bool = True,
    include_runtime_authority_gating: bool = True,
) -> dict[str, Any]:
    """Build the phase-1 readiness bundle from docs-only planning projections."""

    if (
        not include_client_config
        and not include_business_inventory
        and not include_scope_lock_snapshot
        and not include_runtime_authority_gating
    ):
        raise Phase1ReadinessBundleError("Bundle must include at least one projection source")

    bundle: dict[str, Any] = {
        "artifact_type": "phase1_readiness_bundle_projection",
        "artifact_id": PHASE1_READINESS_BUNDLE_ID,
        "phase": EXPECTED_PHASE,
        "projection_scope": "planning_read_only",
        "source_access_mode": "read_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "phase_gate": {
            "name": "ARC_BOT_PHASE1_READINESS_BUNDLE",
            "required": True,
            "enabled": True,
            "flag": "arc_bot_phase1_readiness_bundle",
        },
        "projections": {},
    }

    if include_scope_lock_snapshot:
        scope_lock_snapshot = build_phase0_runtime_ui_scaffold_status_snapshot(
            include_guardian_suite_seam=include_guardian_suite_seam
        )
        if scope_lock_snapshot.get("phase_chain", {}).get("runtime_authority_blocked") is not True:
            raise Phase1ReadinessBundleError("Scope-lock snapshot must remain authority-blocked")
        if scope_lock_snapshot.get("phase_chain", {}).get("runtime_execution_blocked") is not True:
            raise Phase1ReadinessBundleError("Scope-lock snapshot must keep execution blocked")
        bundle["projections"]["phase0_scope_lock_status_snapshot"] = scope_lock_snapshot

    if include_client_config:
        client_projection = build_phase1_client_configuration_projection(enable_phase_gate=True)
        if client_projection["runtime_authority_blocked"] is not True:
            raise Phase1ReadinessBundleError("Client configuration projection must remain authority-blocked")
        if client_projection["runtime_execution_blocked"] is not True:
            raise Phase1ReadinessBundleError(
                "Client configuration projection must keep execution blocked"
            )
        bundle["projections"]["client_configuration"] = _compact_projection(client_projection)

    if include_business_inventory:
        inventory_projection = build_phase1_business_inventory_projection(enable_phase_gate=True)
        if inventory_projection["runtime_authority_blocked"] is not True:
            raise Phase1ReadinessBundleError(
                "Business inventory projection must remain authority-blocked"
            )
        if inventory_projection["runtime_execution_blocked"] is not True:
            raise Phase1ReadinessBundleError(
                "Business inventory projection must keep execution blocked"
            )
        bundle["projections"]["business_inventory"] = _compact_projection(inventory_projection)

    if include_runtime_authority_gating:
        authority_projection = build_phase1_runtime_authority_gating_projection(
            enable_phase_gate=True
        )
        if authority_projection["runtime_authority_blocked"] is not True:
            raise Phase1ReadinessBundleError(
                "Runtime authority gating projection must remain authority-blocked"
            )
        if authority_projection["runtime_execution_blocked"] is not True:
            raise Phase1ReadinessBundleError(
                "Runtime authority gating projection must keep execution blocked"
            )
        bundle["projections"]["runtime_authority_gating"] = _compact_projection(
            authority_projection
        )

    included = set(bundle["projections"].keys())
    if include_scope_lock_snapshot and not included:
        raise Phase1ReadinessBundleError("Scope-lock projection requested but not built")
    if include_client_config and "client_configuration" not in included:
        raise Phase1ReadinessBundleError("Client configuration projection requested but missing")
    if include_business_inventory and "business_inventory" not in included:
        raise Phase1ReadinessBundleError("Business inventory projection requested but missing")
    if include_runtime_authority_gating and "runtime_authority_gating" not in included:
        raise Phase1ReadinessBundleError(
            "Runtime authority-gating projection requested but missing"
        )

    return bundle


def run_phase1_readiness_bundle_preview(argv: list[str] | None = None) -> int:
    """CLI entrypoint for phase-1 readiness bundle rendering."""

    parser = argparse.ArgumentParser(
        description="Render a read-only phase-1 readiness bundle projection"
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON.",
    )
    parser.add_argument(
        "--snapshot-path",
        help="Write readiness projection JSON to this file.",
    )
    parser.add_argument(
        "--no-client-config",
        action="store_true",
        help="Exclude client configuration projection.",
    )
    parser.add_argument(
        "--no-business-inventory",
        action="store_true",
        help="Exclude business inventory projection.",
    )
    parser.add_argument(
        "--no-runtime-authority-gating",
        action="store_true",
        help="Exclude runtime authority gating projection.",
    )
    parser.add_argument(
        "--no-scope-lock",
        action="store_true",
        help="Exclude phase-0 scope-lock status snapshot.",
    )
    parser.add_argument(
        "--omit-guardian-suite-seam",
        action="store_true",
        help="Exclude guardian-suite seam details from the phase-0 scope-lock snapshot.",
    )

    args = parser.parse_args(argv)
    try:
        projection = build_phase1_readiness_bundle(
            include_client_config=not args.no_client_config,
            include_business_inventory=not args.no_business_inventory,
            include_scope_lock_snapshot=not args.no_scope_lock,
            include_guardian_suite_seam=not args.omit_guardian_suite_seam,
            include_runtime_authority_gating=not args.no_runtime_authority_gating,
        )
    except (Phase1ReadinessBundleError, OSError, ValueError) as err:
        print(f"phase-1 readiness bundle preview failed: {err}", file=sys.stderr)
        return 1

    if args.snapshot_path:
        Path(args.snapshot_path).write_text(
            json.dumps(
                projection,
                indent=None if args.compact else 2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    json.dump(
        projection,
        sys.stdout,
        indent=None if args.compact else 2,
        sort_keys=True,
    )
    if not args.compact:
        sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_phase1_readiness_bundle_preview()


if __name__ == "__main__":
    raise SystemExit(main())
