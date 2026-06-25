"""Remaining implementation-gate response inspection.

This module validates the shape of a LIMA Office / Guardian owner response.
It is intentionally read-only and cannot grant Arc Bot runtime authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ArcRemainingGateResponseError(RuntimeError):
    """Raised when the remaining gate response projection is unsafe."""


REMAINING_GATE_RESPONSE_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "operator_console_server_state_owner": (
        "owner",
        "canonical_contract_family",
        "authoritative_fields",
        "arc_bot_may_consume",
        "arc_bot_must_not_do",
    ),
    "guardian_owned_local_model_executor_boundary": (
        "owner",
        "canonical_contract_family",
        "required_guardian_inputs",
        "required_verifier_evidence_outputs",
        "arc_bot_may_consume",
        "arc_bot_must_not_do",
    ),
}


REMAINING_GATE_RESPONSE_SCHEMA_REF = (
    "docs/contracts/schemas/arc_remaining_implementation_gate_response.schema.json"
)
REMAINING_GATE_RESPONSE_TEMPLATE_REF = (
    "docs/examples/arc_lima/remaining_implementation_gate_response.template.json"
)
RECORDED_REMAINING_GATE_RESPONSE_REF = (
    "docs/interop/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_RESPONSE.json"
)


def load_recorded_remaining_gate_response(
    response_path: str | Path = RECORDED_REMAINING_GATE_RESPONSE_REF,
) -> dict[str, Any]:
    """Load the recorded LIMA Office answer packet for shape inspection."""

    parsed = json.loads(Path(response_path).read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("remaining gate response JSON must be an object")
    return parsed


def build_recorded_remaining_implementation_gate_response_projection() -> dict[str, Any]:
    """Inspect the recorded owner response without granting runtime authority."""

    return build_remaining_implementation_gate_response_projection(
        load_recorded_remaining_gate_response()
    )


def build_remaining_implementation_gate_response_projection(
    response: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Inspect an owner response without granting runtime authority."""

    response = response or {}
    missing: dict[str, list[str]] = {}
    present: dict[str, list[str]] = {}
    for dependency_id, required_fields in REMAINING_GATE_RESPONSE_REQUIRED_FIELDS.items():
        dependency_response = response.get(dependency_id, {})
        if not isinstance(dependency_response, dict):
            dependency_response = {}
        present[dependency_id] = [
            field
            for field in required_fields
            if _has_non_empty_value(dependency_response.get(field))
        ]
        missing[dependency_id] = [
            field
            for field in required_fields
            if field not in present[dependency_id]
        ]

    complete = all(not fields for fields in missing.values())
    projection: dict[str, Any] = {
        "artifact_type": "arc_remaining_implementation_gate_response_projection",
        "artifact_id": "arc_remaining_implementation_gate_response_v1",
        "phase": "phase-d-remaining-implementation-gate-response",
        "status": (
            "response_shape_complete_runtime_still_blocked"
            if complete
            else "awaiting_or_incomplete_external_owner_response"
        ),
        "projection_scope": "planning_read_only",
        "source_access_mode": "read_only",
        "inspection_mode": "local_json_inspection_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "response_shape_complete": complete,
        "required_response_fields": {
            key: list(value)
            for key, value in REMAINING_GATE_RESPONSE_REQUIRED_FIELDS.items()
        },
        "response_schema_ref": REMAINING_GATE_RESPONSE_SCHEMA_REF,
        "response_template_ref": REMAINING_GATE_RESPONSE_TEMPLATE_REF,
        "recorded_response_ref": RECORDED_REMAINING_GATE_RESPONSE_REF,
        "present_response_fields": present,
        "missing_response_fields": missing,
        "unresolved_external_dependencies": [
            dependency_id for dependency_id, fields in missing.items() if fields
        ],
        "safe_current_outputs": [
            "response_shape_validation",
            "missing_field_report",
            "blocked_runtime_readiness_projection",
        ],
        "must_not_implement_from_response_alone": [
            "live_supervisor_attachment",
            "local_model_invocation",
            "approval_token_issuance_or_verification",
            "durable_evidence_write",
            "operator_console_state_authority",
            "production_deployment",
        ],
    }
    _assert_projection_safe(projection)
    return projection


def _has_non_empty_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _assert_projection_safe(projection: dict[str, Any]) -> None:
    if projection.get("runtime_authority_blocked") is not True:
        raise ArcRemainingGateResponseError("remaining gate response cannot grant authority")
    if projection.get("runtime_execution_blocked") is not True:
        raise ArcRemainingGateResponseError("remaining gate response cannot grant execution")
    required = set(REMAINING_GATE_RESPONSE_REQUIRED_FIELDS)
    if set(projection.get("required_response_fields", {})) != required:
        raise ArcRemainingGateResponseError("remaining gate response fields are incomplete")
    blocked = set(projection.get("must_not_implement_from_response_alone", []))
    if "local_model_invocation" not in blocked:
        raise ArcRemainingGateResponseError("remaining gate response cannot enable model calls")


def run_remaining_implementation_gate_response_preview(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a remaining implementation-gate response JSON file."
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument("--response-path", help="Local JSON response to inspect.")
    parser.add_argument("--snapshot-path", help="Write projection JSON to this file.")
    args = parser.parse_args(argv)

    try:
        response: dict[str, Any] | None = None
        if args.response_path:
            response = load_recorded_remaining_gate_response(args.response_path)
        projection = build_remaining_implementation_gate_response_projection(response)
    except (ArcRemainingGateResponseError, OSError, ValueError, json.JSONDecodeError) as err:
        print(f"remaining gate response preview failed: {err}", file=sys.stderr)
        return 1

    rendered = json.dumps(
        projection,
        sort_keys=True,
        indent=None if args.compact else 2,
    )
    if args.snapshot_path:
        Path(args.snapshot_path).write_text(rendered + "\n", encoding="utf-8")

    sys.stdout.write(rendered)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_remaining_implementation_gate_response_preview()


if __name__ == "__main__":
    raise SystemExit(main())
