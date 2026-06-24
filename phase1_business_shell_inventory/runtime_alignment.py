"""Read-only Phase-1 business/runtime alignment projection.

The projection compares the business shell inventory posture to the runtime
authority gate posture. It does not execute work, persist state, call models, or
connect to LIMA Office.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from phase1_business_shell_inventory.inventory import (
    build_phase1_business_inventory_projection,
)
from phase1_runtime_authority_gating.gating import (
    build_phase1_runtime_authority_gating_projection,
)


class Phase1RuntimeAlignmentError(RuntimeError):
    """Raised when Phase-1 alignment cannot remain fail-closed."""


def _load_role_ids(inventory_path: str | Path) -> list[str]:
    payload = json.loads(Path(inventory_path).read_text(encoding="utf-8-sig"))
    roles = payload.get("business_role_templates", [])
    if not isinstance(roles, list):
        raise Phase1RuntimeAlignmentError("business_role_templates must be a list")
    role_ids = sorted(
        role.get("role_id")
        for role in roles
        if isinstance(role, dict) and isinstance(role.get("role_id"), str)
    )
    if not role_ids:
        raise Phase1RuntimeAlignmentError("business role bindings must not be empty")
    return role_ids


def build_phase1_business_runtime_alignment_projection(
    *,
    inventory_path: str | Path = Path("tests/fixtures/arc_bot_phase1_business_inventory.json"),
    authority_packet_path: str | Path = Path(
        "tests/fixtures/arc_bot_phase1_runtime_authority_gating_packet.json"
    ),
    enable_phase_gate: bool = True,
) -> dict[str, Any]:
    """Build read-only alignment metadata for business inventory and runtime gates."""

    inventory = build_phase1_business_inventory_projection(
        inventory_path=inventory_path,
        enable_phase_gate=enable_phase_gate,
    )
    authority = build_phase1_runtime_authority_gating_projection(
        packet_path=authority_packet_path,
        enable_phase_gate=enable_phase_gate,
    )

    if inventory.get("runtime_authority_blocked") is not True:
        raise Phase1RuntimeAlignmentError("Business inventory must remain authority-blocked")
    if authority.get("runtime_authority_blocked") is not True:
        raise Phase1RuntimeAlignmentError("Runtime authority gating must remain blocked")
    if authority.get("runtime_execution_blocked") is not True:
        raise Phase1RuntimeAlignmentError("Runtime execution must remain blocked")

    inventory_roles = _load_role_ids(inventory_path)

    return {
        "artifact_type": "phase1_business_runtime_alignment_projection",
        "artifact_id": "arc_bot_phase1_business_runtime_alignment_v1",
        "phase": "phase-1",
        "projection_scope": "planning_read_only",
        "source_access_mode": "read_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "phase_gate": {
            "name": "ARC_BOT_PHASE1_BUSINESS_RUNTIME_ALIGNMENT",
            "required": True,
            "enabled": bool(enable_phase_gate),
        },
        "business_inventory_ref": inventory.get("artifact_id"),
        "runtime_authority_gating_ref": authority.get("artifact_id"),
        "role_bindings": inventory_roles,
        "surface_bindings": sorted(authority.get("surface_bindings", [])),
        "unresolved_required_gates": sorted(authority.get("unresolved_required_gates", [])),
        "alignment_posture": "blocked_until_guardian_lima_office_runtime_gate",
    }


def run_phase1_business_runtime_alignment_preview(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render read-only Phase-1 business/runtime alignment metadata."
    )
    parser.add_argument(
        "--inventory-path",
        default="tests/fixtures/arc_bot_phase1_business_inventory.json",
        help="Business inventory fixture path.",
    )
    parser.add_argument(
        "--authority-packet-path",
        default="tests/fixtures/arc_bot_phase1_runtime_authority_gating_packet.json",
        help="Runtime authority gating packet fixture path.",
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument("--snapshot-path", help="Write projection JSON to this file.")
    args = parser.parse_args(argv)

    try:
        projection = build_phase1_business_runtime_alignment_projection(
            inventory_path=Path(args.inventory_path),
            authority_packet_path=Path(args.authority_packet_path),
        )
    except (Phase1RuntimeAlignmentError, OSError, ValueError) as err:
        print(f"phase-1 business runtime alignment preview failed: {err}", file=sys.stderr)
        return 1

    if args.snapshot_path:
        Path(args.snapshot_path).write_text(
            json.dumps(projection, sort_keys=True, indent=2 if not args.compact else None)
            + "\n",
            encoding="utf-8",
        )

    json.dump(projection, sys.stdout, indent=None if args.compact else 2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_phase1_business_runtime_alignment_preview()


if __name__ == "__main__":
    raise SystemExit(main())
