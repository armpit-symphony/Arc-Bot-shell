"""Phase-1 business shell inventory projection.

This module remains read-only and contract-first. It projects a single inventory
fixture into an operator-facing planning artifact while preserving fail-closed
posture for missing or malformed planning metadata.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY_PATH = REPO_ROOT / "tests" / "fixtures" / "arc_bot_phase1_business_inventory.json"

EXPECTED_PHASE_GATE_NAME = "ARC_BOT_PHASE1_BUSINESS_INVENTORY"
EXPECTED_PHASE = "phase-1"
EXPECTED_SURFACES = {
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
ALLOWED_SURFACE_STATUSES = {
    "blocked",
    "degraded",
    "display_state_only",
    "metadata_only",
    "ready",
    "review_required",
}


class InventoryPhaseGateError(RuntimeError):
    """Raised when phase-1 business inventory gate conditions are not met."""


class InventorySchemaError(ValueError):
    """Raised when inventory fixture does not match fail-closed contract."""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise InventorySchemaError(f"Expected JSON object at {path}")
    return payload


def _assert_required_phase_gate(payload: dict[str, Any], *, expected_name: str) -> None:
    gate = payload.get("phase_gate")
    if not isinstance(gate, dict):
        raise InventorySchemaError("phase_gate missing or not an object")
    if gate.get("name") != expected_name:
        raise InventoryPhaseGateError(
            f"Unexpected phase gate name {gate.get('name')} != {expected_name}"
        )
    if gate.get("required") is not True:
        raise InventorySchemaError("phase_gate.required must be true")


def _assert_surface_contract(surface: str, definition: dict[str, Any]) -> None:
    required = {
        "title",
        "current_state_mode",
        "runtime_authority_blocked",
        "required_status_modes",
        "blocked_runtime_actions",
        "future_seams",
        "metadata_actions",
    }
    missing = sorted(required.difference(definition))
    if missing:
        raise InventorySchemaError(f"Surface {surface} missing fields: {', '.join(missing)}")

    if definition["current_state_mode"] not in ALLOWED_SURFACE_STATUSES:
        raise InventorySchemaError(
            f"Surface {surface} has unsupported current_state_mode: "
            f"{definition['current_state_mode']}"
        )

    if definition["runtime_authority_blocked"] is not True:
        raise InventorySchemaError(
            f"Surface {surface} must set runtime_authority_blocked=true"
        )

    if not isinstance(definition["required_status_modes"], list):
        raise InventorySchemaError(f"Surface {surface} required_status_modes must be list")

    if not definition.get("blocked_runtime_actions"):
        raise InventorySchemaError(f"Surface {surface} must include at least one blocked action")


def _validate_inventory(payload: dict[str, Any]) -> None:
    if payload.get("artifact_version") != EXPECTED_PHASE:
        raise InventorySchemaError(f"artifact_version must be {EXPECTED_PHASE}")

    if payload.get("artifact_type") != "phase1_business_shell_inventory_contract":
        raise InventorySchemaError("artifact_type must be phase1_business_shell_inventory_contract")

    if payload.get("source_access_mode") != "docs_only":
        raise InventorySchemaError("source_access_mode must be docs_only")

    if not isinstance(payload.get("artifact_id"), str) or not payload["artifact_id"]:
        raise InventorySchemaError("artifact_id is required")

    if not payload.get("source_reference"):
        raise InventorySchemaError("source_reference is required")

    if not isinstance(payload.get("business_role_templates"), list):
        raise InventorySchemaError("business_role_templates must be a list")
    if len(payload["business_role_templates"]) < 1:
        raise InventorySchemaError("at least one business_role_template is required")

    for role in payload["business_role_templates"]:
        if not isinstance(role, dict):
            raise InventorySchemaError("each business role must be an object")
        required_role_fields = {
            "role_id",
            "name",
            "allowed_task_categories",
            "forbidden_task_categories",
            "risk_tier",
        }
        missing = sorted(required_role_fields.difference(role))
        if missing:
            raise InventorySchemaError(f"role missing fields: {', '.join(missing)}")
        if not role["risk_tier"]:
            raise InventorySchemaError(f"role {role.get('role_id', '?')} risk_tier required")

    task_model = payload.get("task_model")
    if not isinstance(task_model, dict):
        raise InventorySchemaError("task_model must be an object")
    for key in {"statuses", "execution_modes", "risk_tiers", "approval_labels"}:
        values = task_model.get(key)
        if not isinstance(values, list) or not values:
            raise InventorySchemaError(f"task_model.{key} must be a non-empty list")

    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, dict):
        raise InventorySchemaError("surfaces must be an object")

    if set(surfaces) != EXPECTED_SURFACES:
        missing = EXPECTED_SURFACES.difference(surfaces)
        extra = set(surfaces).difference(EXPECTED_SURFACES)
        details = []
        if missing:
            details.append(f"missing={sorted(missing)}")
        if extra:
            details.append(f"unexpected={sorted(extra)}")
        raise InventorySchemaError("surface set mismatch: " + ", ".join(details))

    for surface, definition in surfaces.items():
        if not isinstance(definition, dict):
            raise InventorySchemaError(f"surface definition must be object: {surface}")
        _assert_surface_contract(surface, definition)


def build_phase1_business_inventory_projection(
    *,
    inventory_path: str | Path = DEFAULT_INVENTORY_PATH,
    enable_phase_gate: bool = False,
    phase_gate_name: str = EXPECTED_PHASE_GATE_NAME,
) -> dict[str, Any]:
    """Build the Phase-1 planning projection from fixture-backed inventory.

    The returned projection is deterministic and read-only.
    """

    if not enable_phase_gate:
        raise InventoryPhaseGateError(
            "Phase-1 business inventory rendering requires enable_phase_gate=True"
        )

    payload = _load_json(Path(inventory_path))
    _assert_required_phase_gate(payload, expected_name=phase_gate_name)
    _validate_inventory(payload)

    projection_surfaces: dict[str, Any] = {}
    for surface_id in sorted(payload["surfaces"]):
        source = payload["surfaces"][surface_id]
        projection_surfaces[surface_id] = {
            "projection_mode": "read_only",
            "status": source["current_state_mode"],
            "runtime_authority_blocked": True,
            "runtime_execution_blocked": True,
            "blocked_runtime_actions": sorted(set(source["blocked_runtime_actions"])),
            "required_status_modes": sorted(set(source["required_status_modes"])),
            "metadata_actions": sorted(set(source.get("metadata_actions", []))),
            "future_seams": source["future_seams"],
        }

    task_model = payload["task_model"]

    return {
        "artifact_id": payload["artifact_id"],
        "artifact_type": "phase1_business_shell_inventory_projection",
        "phase": EXPECTED_PHASE,
        "projection_scope": "planning_read_only",
        "source_reference": payload["source_reference"],
        "source_access_mode": payload["source_access_mode"],
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "phase_gate": {
            "enabled": True,
            "name": phase_gate_name,
            "required": True,
            "flag": payload["phase_gate"]["flag"],
        },
        "task_model": {
            "statuses": task_model["statuses"],
            "execution_modes": task_model["execution_modes"],
            "risk_tiers": task_model["risk_tiers"],
            "approval_labels": task_model["approval_labels"],
        },
        "surface_bindings": sorted(payload["surfaces"].keys()),
        "roles_count": len(payload["business_role_templates"]),
        "surfaces": projection_surfaces,
    }


def run_phase1_inventory_preview(argv: list[str] | None = None) -> int:
    """CLI entrypoint for inventory projection preview/export."""

    parser = argparse.ArgumentParser(description="Render phase-1 business inventory projection")
    parser.add_argument(
        "inventory_path",
        nargs="?",
        default=str(DEFAULT_INVENTORY_PATH),
        help="path to phase1 inventory contract JSON fixture",
    )
    parser.add_argument("--compact", action="store_true", help="compact output")
    parser.add_argument(
        "--snapshot-path",
        default=None,
        help="write the projection snapshot to a file",
    )
    parser.add_argument(
        "--no-phase-gate",
        action="store_true",
        help="disable phase gate (used for tests only)",
    )

    args = parser.parse_args(argv)

    try:
        projection = build_phase1_business_inventory_projection(
            inventory_path=args.inventory_path,
            enable_phase_gate=not args.no_phase_gate,
        )
    except (InventoryPhaseGateError, InventorySchemaError) as err:
        print(f"phase1 business inventory preview failed: {err}", file=sys.stderr)
        return 1

    if args.snapshot_path is not None:
        Path(args.snapshot_path).write_text(
            json.dumps(projection, indent=None if args.compact else 2, sort_keys=True)
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
        print()
    return 0


def _compact_projection(projection: dict[str, Any]) -> dict[str, Any]:
    """Create a compact form for CLI-focused assertions."""

    return {
        "artifact_type": projection["artifact_type"],
        "artifact_id": projection["artifact_id"],
        "phase": projection["phase"],
        "projection_scope": projection["projection_scope"],
        "runtime_authority_blocked": projection["runtime_authority_blocked"],
        "runtime_execution_blocked": projection["runtime_execution_blocked"],
        "source_reference": projection["source_reference"],
        "surface_bindings": projection["surface_bindings"],
    }


def main() -> int:
    return run_phase1_inventory_preview()


if __name__ == "__main__":
    raise SystemExit(main())
