"""Phase-1 runtime authority gating pack projection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUTHORITY_GATING_PACKET_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "arc_bot_phase1_runtime_authority_gating_packet.json"
)

EXPECTED_PHASE = "phase-1"
EXPECTED_PHASE_GATE_NAME = "ARC_BOT_PHASE1_RUNTIME_AUTHORITY_GATING"
REQUIRED_GATE_IDS = {
    "approval_token_lineage",
    "connector_authority_approval",
    "evidence_and_rollback_gate",
    "guardian_runtime_authority_approval",
    "production_readiness_approval",
}


class Phase1AuthorityGatingError(RuntimeError):
    """Raised when runtime authority gating pack rendering is blocked."""


class Phase1AuthorityGatingSchemaError(ValueError):
    """Raised when the phase-1 authority gating fixture is malformed."""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Phase1AuthorityGatingSchemaError(f"Expected JSON object at {path}")
    return payload


def _assert_required_phase_gate(payload: dict[str, Any], *, expected_name: str) -> None:
    gate = payload.get("phase_gate")
    if not isinstance(gate, dict):
        raise Phase1AuthorityGatingSchemaError("phase_gate missing or invalid")
    if gate.get("name") != expected_name:
        raise Phase1AuthorityGatingError(
            f"Unexpected phase gate name {gate.get('name')} != {expected_name}"
        )
    if gate.get("required") is not True:
        raise Phase1AuthorityGatingSchemaError("phase_gate.required must be true")
    if gate.get("flag") != "arc_bot_runtime_authority_gating_pack":
        raise Phase1AuthorityGatingSchemaError(
            "phase_gate.flag must be arc_bot_runtime_authority_gating_pack"
        )


def _assert_supported_gate_id(gate_id: str) -> None:
    if gate_id not in REQUIRED_GATE_IDS:
        raise Phase1AuthorityGatingSchemaError(f"Unsupported gate_id {gate_id}")


def _normalize_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    intent_id = mapping.get("intent_id")
    if not isinstance(intent_id, str) or not intent_id:
        raise Phase1AuthorityGatingSchemaError("Each mapping must include intent_id")
    if not isinstance(mapping.get("surface"), str) or not mapping["surface"]:
        raise Phase1AuthorityGatingSchemaError(f"{intent_id} missing surface")
    gates = mapping.get("required_future_gates")
    if not isinstance(gates, list) or not gates:
        raise Phase1AuthorityGatingSchemaError(
            f"{intent_id} must list at least one required_future_gate"
        )
    normalized_gates = []
    for gate in gates:
        if not isinstance(gate, str):
            raise Phase1AuthorityGatingSchemaError(f"{intent_id} has non-string gate")
        _assert_supported_gate_id(gate)
        normalized_gates.append(gate)

    notes = mapping.get("notes")
    if not isinstance(notes, str):
        raise Phase1AuthorityGatingSchemaError(f"{intent_id} notes must be text")

    return {
        "intent_id": intent_id,
        "surface": mapping["surface"],
        "intent_category": str(mapping.get("intent_category", "")),
        "required_future_gates": sorted(set(normalized_gates)),
        "notes": notes,
    }


def _validate_payload(payload: dict[str, Any]) -> None:
    required_fields = {
        "artifact_id",
        "artifact_type",
        "artifact_version",
        "source_access_mode",
        "phase_gate",
        "runtime_authority_state",
        "required_future_gates",
        "planned_user_intents",
        "runtime_boundaries",
        "validation_commands",
    }
    missing = required_fields.difference(payload)
    if missing:
        raise Phase1AuthorityGatingSchemaError(
            f"Missing required fields: {', '.join(sorted(missing))}"
        )

    if payload.get("artifact_type") != "phase1_runtime_authority_gating_pack":
        raise Phase1AuthorityGatingSchemaError("artifact_type must be phase1_runtime_authority_gating_pack")
    if payload.get("artifact_version") != EXPECTED_PHASE:
        raise Phase1AuthorityGatingSchemaError(f"artifact_version must be {EXPECTED_PHASE}")
    if payload.get("source_access_mode") != "read_only":
        raise Phase1AuthorityGatingSchemaError("source_access_mode must be read_only")

    runtime_state = payload.get("runtime_authority_state")
    if not isinstance(runtime_state, dict):
        raise Phase1AuthorityGatingSchemaError("runtime_authority_state must be object")
    for key in ("runtime_authority_blocked", "runtime_execution_blocked"):
        if runtime_state.get(key) is not True:
            raise Phase1AuthorityGatingSchemaError(f"{key} must be true")

    gate_defs = payload["required_future_gates"]
    if not isinstance(gate_defs, list) or not gate_defs:
        raise Phase1AuthorityGatingSchemaError("required_future_gates must be a non-empty list")

    seen_gate_ids = set()
    for gate in gate_defs:
        if not isinstance(gate, dict):
            raise Phase1AuthorityGatingSchemaError("each required gate must be object")
        gate_id = gate.get("gate_id")
        if not isinstance(gate_id, str):
            raise Phase1AuthorityGatingSchemaError("gate_id must be text")
        _assert_supported_gate_id(gate_id)
        if gate_id in seen_gate_ids:
            raise Phase1AuthorityGatingSchemaError(f"Duplicate gate_id: {gate_id}")
        seen_gate_ids.add(gate_id)
        for key in ("required", "resolved"):
            if not isinstance(gate.get(key), bool):
                raise Phase1AuthorityGatingSchemaError(
                    f"{gate_id}.{key} must be boolean"
                )
        if gate.get("required") is not True:
            raise Phase1AuthorityGatingSchemaError(f"{gate_id}.required must be true")
        if gate.get("resolved") is not False:
            raise Phase1AuthorityGatingSchemaError(
                f"{gate_id}.resolved must remain false in planning packets"
            )

    if seen_gate_ids != REQUIRED_GATE_IDS:
        missing = REQUIRED_GATE_IDS.difference(seen_gate_ids)
        extra = seen_gate_ids.difference(REQUIRED_GATE_IDS)
        if missing:
            raise Phase1AuthorityGatingSchemaError(
                f"Missing required gates: {', '.join(sorted(missing))}"
            )
        if extra:
            raise Phase1AuthorityGatingSchemaError(
                f"Unexpected extra gates: {', '.join(sorted(extra))}"
            )

    mappings = payload["planned_user_intents"]
    if not isinstance(mappings, list) or not mappings:
        raise Phase1AuthorityGatingSchemaError("planned_user_intents must be a non-empty list")
    normalized = [ _normalize_mapping(mapping) for mapping in mappings ]
    if len(normalized) != len(set(item["intent_id"] for item in normalized)):
        raise Phase1AuthorityGatingSchemaError("planned_user_intents must have unique intent_id values")


def build_phase1_runtime_authority_gating_projection(
    *,
    packet_path: str | Path = DEFAULT_AUTHORITY_GATING_PACKET_PATH,
    enable_phase_gate: bool = False,
    phase_gate_name: str = EXPECTED_PHASE_GATE_NAME,
) -> dict[str, Any]:
    """Build a normalized read-only projection from planning-only authority-gating packet."""

    if not enable_phase_gate:
        raise Phase1AuthorityGatingError(
            "Phase-1 runtime authority gating projection requires enable_phase_gate=True"
        )

    payload = _load_json(Path(packet_path))
    _assert_required_phase_gate(payload, expected_name=phase_gate_name)
    _validate_payload(payload)

    mappings = [
        {
            "intent_id": item["intent_id"],
            "surface": item["surface"],
            "required_future_gates": sorted(set(item["required_future_gates"])),
        }
        for item in payload["planned_user_intents"]
    ]

    surface_bindings: dict[str, list[str]] = {}
    for item in mappings:
        surface_bindings.setdefault(item["surface"], []).append(item["intent_id"])
    for surface in surface_bindings:
        surface_bindings[surface] = sorted(surface_bindings[surface])

    unresolved_gates = [
        gate["gate_id"]
        for gate in payload["required_future_gates"]
        if gate.get("resolved") is False
    ]

    return {
        "artifact_id": payload["artifact_id"],
        "artifact_type": payload["artifact_type"],
        "phase": EXPECTED_PHASE,
        "projection_scope": "planning_read_only",
        "source_access_mode": payload["source_access_mode"],
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "phase_gate": {
            "name": phase_gate_name,
            "required": True,
            "enabled": True,
            "flag": payload["phase_gate"]["flag"],
        },
        "runtime_authority_state": payload["runtime_authority_state"],
        "required_gates": sorted(
            (
                {
                    "gate_id": item["gate_id"],
                    "resolved": item["resolved"],
                }
                for item in payload["required_future_gates"]
            ),
            key=lambda gate: gate["gate_id"],
        ),
        "unresolved_required_gates": sorted(unresolved_gates),
        "surface_bindings": sorted(surface_bindings),
        "intent_count": len(mappings),
        "planned_intents_by_surface": dict(sorted(surface_bindings.items())),
        "planned_user_intents": [
            {
                "intent_id": item["intent_id"],
                "surface": item["surface"],
                "required_future_gates": item["required_future_gates"],
            }
            for item in mappings
        ],
    }


def run_phase1_runtime_authority_gating_preview(argv: list[str] | None = None) -> int:
    """CLI entrypoint for the phase-1 authority-gating projection."""

    parser = argparse.ArgumentParser(
        description="Render phase-1 runtime authority gating projection"
    )
    parser.add_argument(
        "packet_path",
        nargs="?",
        default=str(DEFAULT_AUTHORITY_GATING_PACKET_PATH),
        help="path to phase-1 runtime authority-gating packet fixture",
    )
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    parser.add_argument(
        "--snapshot-path",
        default=None,
        help="write projection snapshot to a file",
    )
    parser.add_argument(
        "--no-phase-gate",
        action="store_true",
        help="disable phase gate check (tests only)",
    )

    args = parser.parse_args(argv)

    try:
        projection = build_phase1_runtime_authority_gating_projection(
            packet_path=args.packet_path,
            enable_phase_gate=not args.no_phase_gate,
        )
    except (
        Phase1AuthorityGatingError,
        Phase1AuthorityGatingSchemaError,
        OSError,
        ValueError,
    ) as err:
        print(f"runtime authority gating preview failed: {err}", file=sys.stderr)
        return 1

    if args.snapshot_path is not None:
        Path(args.snapshot_path).write_text(
            json.dumps(projection, sort_keys=True, indent=None if args.compact else 2) + "\n",
            encoding="utf-8",
        )

    json.dump(projection, sys.stdout, sort_keys=True, indent=None if args.compact else 2)
    if not args.compact:
        sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_phase1_runtime_authority_gating_preview()


if __name__ == "__main__":
    raise SystemExit(main())
