"""Phase-0 runtime UI scaffold adapter rendering helpers.

This module is intentionally read-only and phase-gated.
It loads fixture payloads and snapshot fixtures and projects only
display-only state for surfaces that are explicitly allowed in Phase-0.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SURFACES = {"work_queue", "runtime_settings"}
EXPECTED_PHASE_GATE_NAME = "RUNTIME_UI_Scaffold"
EXPECTED_PHASE_GATE_FLAG = "runtime_ui_scaffold_only_preview"
EXPECTED_ADAPTER_MODE = "fixture_backed_read_only_projection"
PHASE0_MODE = "phase-0"

RUNTIME_AUTHORITY_FALSE_FIELDS = (
    "live_model_inference_allowed",
    "tool_execution_allowed",
    "credential_storage_allowed",
    "provider_token_storage_allowed",
    "raw_runtime_payload_persistence_allowed",
    "runtime_route_change_without_approval_allowed",
)

WORK_QUEUE_RUNTIME_AUTHORITY_FIELDS = (
    "live_program_execution_allowed",
    "customer_system_mutation_allowed",
    "external_message_send_allowed",
)


class PhaseGateError(RuntimeError):
    """Raised when the requested Phase-0 read-only gate is not enabled."""


class AdapterPayloadError(ValueError):
    """Raised when a scaffold payload or snapshot violates Phase-0 constraints."""


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AdapterPayloadError(f"Expected JSON object at {path}")
    return data


def _assert_no_runtime_authority(snapshot: dict[str, Any], surface: str) -> None:
    for field in RUNTIME_AUTHORITY_FALSE_FIELDS:
        if field in snapshot and snapshot[field] is not False:
            raise AdapterPayloadError(
                f"Runtime authority must be blocked for {surface}: {field} is not False"
            )

    for field in WORK_QUEUE_RUNTIME_AUTHORITY_FIELDS:
        if field in snapshot and snapshot[field] is not False:
            raise AdapterPayloadError(
                f"Work Queue runtime authority must be blocked: {field} is not False"
            )


def _build_surface_projection(
    surface_entry: Mapping[str, Any],
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    surface = surface_entry["surface"]
    assert isinstance(surface, str)

    metadata_actions = set(snapshot.get("metadata_actions", []))
    blocked_runtime_actions = set(surface_entry.get("blocked_runtime_actions", []))
    snapshot_blocked_actions = set(snapshot.get("blocked_actions", []))
    required_envelope_modes = set(surface_entry.get("required_envelope_status_modes", []))

    if required_envelope_modes and snapshot["envelope"]["status"] not in required_envelope_modes:
        raise AdapterPayloadError(
            f"Unexpected envelope status for {surface}: "
            f"{snapshot['envelope']['status']}"
        )

    return {
        "surface": surface,
        "snapshot_source_file": surface_entry["snapshot_file"],
        "view_type": snapshot["envelope"]["view_type"],
        "status": snapshot["envelope"]["status"],
        "tenant_id": snapshot["envelope"]["tenant_id"],
        "customer_context_id": snapshot["envelope"]["customer_context_id"],
        "environment": snapshot["envelope"]["environment"],
        "operator_role": snapshot["envelope"]["operator_role"],
        "projection_mode": "read_only",
        "runtime_authority_enforced": False,
        "read_only_projection_only": bool(surface_entry["read_only_projection_only"]),
        "allowed_metadata_actions": sorted(metadata_actions | set(surface_entry.get("allowed_metadata_actions", []))),
        "blocked_runtime_actions": sorted(blocked_runtime_actions | snapshot_blocked_actions),
        "policy_refs": snapshot["envelope"]["policy_refs"],
        "evidence_refs": snapshot["envelope"]["evidence_refs"],
        "runbook_refs": snapshot["envelope"]["runbook_refs"],
        "phase_gate_required": True,
        "required_envelope_status_modes": sorted(required_envelope_modes),
    }


def build_phase0_readonly_projection(
    adapter_payload_path: str | Path,
    *,
    enable_phase_gate: bool = False,
    phase_gate_name: str = EXPECTED_PHASE_GATE_NAME,
    include_snapshot_payloads: bool = True,
) -> dict[str, Any]:
    """
    Build a read-only projection for Phase-0 scope surfaces.

    This function is deliberately static-only:
    - no external calls,
    - no mutations,
    - no runtime authority,
    - no connector/model/provider execution.
    """

    if not enable_phase_gate:
        raise PhaseGateError(
            "Phase-0 runtime UI scaffold rendering requires enable_phase_gate=True"
        )

    if phase_gate_name != EXPECTED_PHASE_GATE_NAME:
        raise PhaseGateError(
            f"Unexpected phase gate name: {phase_gate_name} != {EXPECTED_PHASE_GATE_NAME}"
        )

    payload = _load_json(Path(adapter_payload_path))

    if payload.get("adapter_mode") != EXPECTED_ADAPTER_MODE:
        raise AdapterPayloadError("Payload must use fixture-backed read-only adapter mode")
    if payload.get("adapter_phase") != PHASE0_MODE:
        raise AdapterPayloadError("Payload must target phase-0")
    if payload.get("phase_gate_flag") != EXPECTED_PHASE_GATE_FLAG:
        raise AdapterPayloadError("Payload does not advertise phase-0-only preview gate")
    if payload.get("phase_gate_required") is not True:
        raise AdapterPayloadError("Payload must require phase gate")

    surface_payloads = payload.get("surface_payloads", [])
    if set(item["surface"] for item in surface_payloads) != EXPECTED_SURFACES:
        raise AdapterPayloadError("Payload surface bindings are not exactly expected surfaces")

    projection_by_surface: dict[str, dict[str, Any]] = {}

    for surface_entry in surface_payloads:
        surface = surface_entry["surface"]
        snapshot_path = REPO_ROOT / str(surface_entry["snapshot_file"])
        snapshot = _load_json(snapshot_path)

        if snapshot.get("surface") != surface:
            raise AdapterPayloadError(
                f"Snapshot surface mismatch: expected {surface}, found {snapshot.get('surface')}"
            )
        if surface not in EXPECTED_SURFACES:
            raise AdapterPayloadError(f"Unexpected surface in payload: {surface}")
        if snapshot.get("display_state_only") is not True:
            raise AdapterPayloadError(f"{surface} must be display_state_only=True")

        _assert_no_runtime_authority(snapshot, surface)

        projection_by_surface[surface] = _build_surface_projection(surface_entry, snapshot)

        if projection_by_surface[surface]["projection_mode"] != "read_only":
            raise AdapterPayloadError(f"{surface} projection mode is not read-only")

        if not surface_entry.get("runtime_authority_enforced_false", False):
            raise AdapterPayloadError(
                f"{surface} must explicitly enforce no runtime authority"
            )
        if surface_entry.get("requires_phase_gate") is not True:
            raise AdapterPayloadError(
                f"{surface} requires a phase gate in Phase-0"
            )
        if surface_entry.get("read_only_projection_only") is not True:
            raise AdapterPayloadError(
                f"{surface} must be a read-only projection surface"
            )

    adapter_result: dict[str, Any] = {
        "payload_id": payload["payload_id"],
        "adapter_name": payload["adapter_name"],
        "adapter_phase": payload["adapter_phase"],
        "adapter_mode": payload["adapter_mode"],
        "phase_gate": {
            "name": phase_gate_name,
            "enabled": True,
            "required": payload["phase_gate_required"],
            "flag": payload["phase_gate_flag"],
        },
        "surface_bindings": sorted(payload["surface_payloads"], key=lambda entry: entry["surface"]),
        "surfaces": projection_by_surface,
        "phase_gate_enabled": True,
    }

    if include_snapshot_payloads:
        adapter_result["snapshots"] = deepcopy(
            {surface: _load_json(REPO_ROOT / str(entry["snapshot_file"])) for surface, entry in (
                (entry["surface"], entry) for entry in surface_payloads
            )}
        )

    return adapter_result
