"""Phase-1 read-only runtime feed contract helpers.

These helpers remain contract-only and projection-safe. They validate read-feed
contracts and return normalized phase-1 projection maps without any external I/O
or runtime authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

EXPECTED_PHASE_GATE_NAME = "RUNTIME_UI_SCAFFOLD_PHASE1_FEED"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json"
)
DEFAULT_PAYLOAD_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json"
)

class ReadFeedContractError(ValueError):
    """Raised when a runtime read-feed contract is malformed for phase-1 scaffolding."""


class ReadFeedGateError(RuntimeError):
    """Raised when a phase-1 read-feed contract is not allowed by gate settings."""


class ReadFeedPayloadError(ReadFeedContractError):
    """Raised when a phase-1 read-feed payload is malformed for projection ingestion."""


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ReadFeedContractError(f"Expected JSON object at {path}")
    return data


def _assert_true(value: object, message: str) -> None:
    if value is not True:
        raise ReadFeedContractError(message)


def _assert_false(value: object, message: str) -> None:
    if value is not False:
        raise ReadFeedPayloadError(message)


def _validate_payload_envelope_fields(
    envelope: Mapping[str, Any],
    surface: str,
    required_fields: list[str],
) -> None:
    for field in required_fields:
        if field not in envelope:
            raise ReadFeedPayloadError(
                f"{surface} envelope is missing required field {field}"
            )


def _validate_surface_snapshot_runtime_flags(snapshot: Mapping[str, Any], surface: str) -> None:
    authority_fields = (
        "live_model_inference_allowed",
        "tool_execution_allowed",
        "customer_system_mutation_allowed",
        "external_message_send_allowed",
        "credential_storage_allowed",
        "provider_token_storage_allowed",
        "raw_runtime_payload_persistence_allowed",
        "runtime_route_change_without_approval_allowed",
        "live_program_execution_allowed",
    )
    for field in authority_fields:
        if field in snapshot and snapshot[field] is not False:
            raise ReadFeedPayloadError(
                f"{field} must remain false in {surface} runtime-feed snapshot (value: {snapshot[field]})"
            )


def _normalize_surface_projection(
    surface: str,
    surface_contract: Mapping[str, Any],
    surface_payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(surface_payload, Mapping):
        raise ReadFeedPayloadError(f"Surface payload for {surface} must be an object")

    snapshot = surface_payload.get("snapshot")
    if not isinstance(snapshot, Mapping):
        raise ReadFeedPayloadError(
            f"Surface payload for {surface} must include snapshot object"
        )

    envelope = snapshot.get("envelope")
    if not isinstance(envelope, Mapping):
        raise ReadFeedPayloadError(
            f"Surface payload snapshot for {surface} must include envelope object"
        )

    required_envelope_fields = list(surface_contract["required_envelope_fields"])
    _validate_payload_envelope_fields(envelope, surface, required_envelope_fields)

    blocked_runtime_actions = surface_payload.get("blocked_runtime_actions", [])
    if not isinstance(blocked_runtime_actions, list):
        raise ReadFeedPayloadError(
            f"Surface payload for {surface} must define blocked_runtime_actions list"
        )

    contract_blocked_actions = set(surface_contract["blocked_runtime_actions"])
    payload_blocked_actions = set(str(action) for action in blocked_runtime_actions)
    if not contract_blocked_actions.issubset(payload_blocked_actions):
        missing = sorted(contract_blocked_actions - payload_blocked_actions)
        raise ReadFeedPayloadError(
            f"Surface payload for {surface} missing contract-mandated blocked actions: {missing}"
        )

    spine_sources = surface_payload.get("spine_sources")
    if not isinstance(spine_sources, list) or not spine_sources:
        raise ReadFeedPayloadError(f"Surface payload for {surface} must define spine_sources list")

    for source in spine_sources:
        if source not in surface_contract["spine_sources"]:
            raise ReadFeedPayloadError(
                f"Surface payload for {surface} references unsupported spine source {source}"
            )

    _validate_surface_snapshot_runtime_flags(snapshot, surface)

    normalized_snapshot = dict(snapshot)
    normalized_snapshot["surface"] = surface

    return {
        "surface": surface,
        "projection_mode": "read_only",
        "snapshot": normalized_snapshot,
        "required_envelope_fields": sorted(required_envelope_fields),
        "contract_refs": surface_contract["contract_refs"],
        "blocked_runtime_actions": sorted(payload_blocked_actions),
        "spine_sources": sorted(str(source) for source in spine_sources),
        "notes": surface_payload.get("notes", ""),
    }


def build_phase1_read_feed_projection(path: str | Path) -> dict[str, Any]:
    """Build a normalized read-only feed projection for phase-1 scaffolding."""

    contract = _load_json(Path(path))

    if contract.get("phase") != "phase-1":
        raise ReadFeedContractError("Read feed contract must target phase-1")
    _assert_true(
        contract.get("projection_scope") == "read_only",
        "Phase-1 read-feed contracts must be read-only projection scope.",
    )
    _assert_true(
        contract.get("runtime_authority_enabled") is False,
        "Runtime authority must remain disabled in phase-1 read-feed contract.",
    )
    _assert_true(
        contract.get("source_access_mode") == "read_only",
        "Read feed contract source must be read-only.",
    )
    _assert_true(
        contract.get("projection_gate_required") is True,
        "Phase-1 read-feed projection requires gate.",
    )

    source_reference = contract.get("source_reference")
    if not isinstance(source_reference, str) or not source_reference:
        raise ReadFeedContractError("Read feed contract must include source_reference")

    spine_sources = contract.get("spine_sources")
    if not isinstance(spine_sources, list) or not spine_sources:
        raise ReadFeedContractError("Read feed contract must include spine_sources list")

    surface_read_paths = contract.get("surface_read_paths")
    if not isinstance(surface_read_paths, Mapping):
        raise ReadFeedContractError("Read feed contract must include surface_read_paths mapping")

    projection_by_surface: dict[str, Any] = {}
    for surface, surface_contract in surface_read_paths.items():
        if not isinstance(surface_contract, Mapping):
            raise ReadFeedContractError(f"Surface contract for {surface} must be an object")

        contract_refs = surface_contract.get("contract_refs")
        if not isinstance(contract_refs, list) or not contract_refs:
            raise ReadFeedContractError(
                f"Surface contract for {surface} must define contract_refs"
            )

        required_envelope_fields = surface_contract.get("required_envelope_fields")
        if not isinstance(required_envelope_fields, list) or not required_envelope_fields:
            raise ReadFeedContractError(
                f"Surface contract for {surface} must define required_envelope_fields"
            )

        blocked_runtime_actions = surface_contract.get("blocked_runtime_actions")
        if not isinstance(blocked_runtime_actions, list):
            raise ReadFeedContractError(
                f"Surface contract for {surface} must define blocked_runtime_actions"
            )

        surface_spine_sources = surface_contract.get("spine_sources")
        if not isinstance(surface_spine_sources, list) or not surface_spine_sources:
            raise ReadFeedContractError(
                f"Surface contract for {surface} must define spine_sources"
            )

        for source in surface_spine_sources:
            if source not in spine_sources:
                raise ReadFeedContractError(
                    f"Surface {surface} references unsupported spine source {source}"
                )

        projection_by_surface[surface] = {
            "contract_refs": sorted(str(ref) for ref in contract_refs),
            "required_envelope_fields": sorted(str(field) for field in required_envelope_fields),
            "blocked_runtime_actions": sorted(str(action) for action in blocked_runtime_actions),
            "spine_sources": sorted(str(source) for source in surface_spine_sources),
            "notes": surface_contract.get("notes", ""),
        }

    return {
        "artifact_id": contract.get("artifact_id"),
        "artifact_type": contract.get("artifact_type"),
        "phase": contract.get("phase"),
        "projection_scope": contract.get("projection_scope"),
        "source_reference": source_reference,
        "projection_gate_name": contract.get("projection_gate_name"),
        "projection_gate_required": contract.get("projection_gate_required"),
        "surface_read_paths": projection_by_surface,
        "metadata_policy": contract.get("metadata_policy", {}),
        "source_access_mode": contract.get("source_access_mode"),
        "spine_sources": sorted(str(source) for source in spine_sources),
    }


def render_phase1_read_feed_projection(
    *,
    feed_contract_path: str | Path = DEFAULT_CONTRACT_PATH,
    phase_gate_name: str = EXPECTED_PHASE_GATE_NAME,
    include_surface_contracts: bool = True,
    enable_phase_gate: bool = True,
) -> dict[str, Any]:
    """Build a renderable phase-1 read-only feed projection with gate metadata."""

    projection = build_phase1_read_feed_projection(feed_contract_path)

    contract_gate = projection.get("projection_gate_name")
    if contract_gate != phase_gate_name:
        raise ReadFeedGateError(
            f"Phase-1 read-feed contract gate mismatch: {contract_gate} != {phase_gate_name}"
        )

    if enable_phase_gate and projection.get("projection_gate_required") is not True:
        raise ReadFeedGateError(
            "Phase-1 read-feed projection requires an enabled projection gate"
        )

    if projection.get("source_access_mode") != "read_only":
        raise ReadFeedContractError("Phase-1 read-feed projection must remain read-only source access")

    if not enable_phase_gate:
        raise ReadFeedGateError("Phase-1 read-feed rendering requires enable_phase_gate=True")

    render_result: dict[str, Any] = {
        "projection": projection["projection_gate_name"],
        "phase": projection["phase"],
        "artifact_type": projection["artifact_type"],
        "artifact_id": projection["artifact_id"],
        "projection_scope": projection["projection_scope"],
        "source_reference": projection["source_reference"],
        "phase_gate": {
            "name": phase_gate_name,
            "required": bool(projection["projection_gate_required"]),
            "enabled": enable_phase_gate,
        },
        "metadata_policy": projection["metadata_policy"],
        "surface_bindings": sorted(projection["surface_read_paths"].keys()),
    }

    if include_surface_contracts:
        render_result["surface_read_paths"] = projection["surface_read_paths"]

    return render_result


def build_phase1_read_feed_runtime_projection(
    *,
    feed_contract_path: str | Path = DEFAULT_CONTRACT_PATH,
    feed_payload_path: str | Path = DEFAULT_PAYLOAD_PATH,
    enable_phase_gate: bool = True,
) -> dict[str, Any]:
    """Build a read-only surface projection from a fixture read-feed payload."""

    projection_contract = build_phase1_read_feed_projection(feed_contract_path)
    payload = _load_json(Path(feed_payload_path))

    if not enable_phase_gate:
        raise ReadFeedGateError(
            "Phase-1 read-feed runtime projection requires enable_phase_gate=True"
        )

    if projection_contract["projection_gate_required"] is not True:
        raise ReadFeedGateError(
            "Phase-1 read-feed runtime projection requires enabled projection gate"
        )

    if payload.get("phase") != projection_contract["phase"]:
        raise ReadFeedPayloadError(
            "Read-feed payload phase does not match projection contract phase"
        )

    if payload.get("projection_scope") != projection_contract["projection_scope"]:
        raise ReadFeedPayloadError(
            "Read-feed payload projection scope must match contract scope"
        )

    _assert_false(payload.get("runtime_authority_enabled"), "runtime_authority_enabled")

    source_reference = payload.get("source_reference")
    if source_reference != projection_contract["source_reference"]:
        raise ReadFeedPayloadError(
            f"Read-feed payload source_reference mismatch: {source_reference}"
        )

    if payload.get("source_access_mode") != projection_contract["source_access_mode"]:
        raise ReadFeedPayloadError(
            "Read-feed payload source access mode must remain read-only"
        )

    spine_source_records = payload.get("spine_source_records")
    if not isinstance(spine_source_records, Mapping):
        raise ReadFeedPayloadError("Read-feed payload must include spine_source_records")
    for source in projection_contract["spine_sources"]:
        if source not in spine_source_records:
            raise ReadFeedPayloadError(
                f"Read-feed payload missing required spine source {source}"
            )
        if not isinstance(spine_source_records[source], list):  # type: ignore[index]
            raise ReadFeedPayloadError(
                f"Spine source {source} in payload must be an array"
            )

    surface_payloads = payload.get("surface_payloads")
    if not isinstance(surface_payloads, Mapping):
        raise ReadFeedPayloadError("Read-feed payload must include surface_payloads")

    if set(surface_payloads.keys()) != set(projection_contract["surface_read_paths"].keys()):
        raise ReadFeedPayloadError(
            "Read-feed payload surface set does not match projection contract surfaces"
        )

    projected_surfaces: dict[str, Any] = {}
    for surface, surface_contract in projection_contract["surface_read_paths"].items():
        projected_surfaces[surface] = _normalize_surface_projection(
            surface,
            surface_contract,
            surface_payloads[surface],  # type: ignore[index]
        )

    return {
        "payload_id": payload.get("payload_id"),
        "payload_type": payload.get("payload_type"),
        "artifact_id": projection_contract["artifact_id"],
        "artifact_type": "phase1_read_feed_runtime_projection",
        "phase": projection_contract["phase"],
        "projection_scope": projection_contract["projection_scope"],
        "source_reference": projection_contract["source_reference"],
        "source_access_mode": projection_contract["source_access_mode"],
        "phase_gate": {
            "name": projection_contract["projection_gate_name"],
            "required": bool(projection_contract["projection_gate_required"]),
            "enabled": enable_phase_gate,
        },
        "ingested_at": payload.get("ingested_at"),
        "metadata_policy": projection_contract["metadata_policy"],
        "spine_sources": projection_contract["spine_sources"],
        "surface_bindings": sorted(projected_surfaces.keys()),
        "surfaces": projected_surfaces,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render Phase-1 runtime UI read-feed contract projection."
    )
    parser.add_argument(
        "contract_path",
        nargs="?",
        default=str(DEFAULT_CONTRACT_PATH),
        help=(
            "Path to the Phase-1 read-feed contract fixture "
            "(defaults to tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json)"
        ),
    )
    parser.add_argument(
        "--phase-gate-name",
        default=EXPECTED_PHASE_GATE_NAME,
        help="Expected phase gate name for this projection.",
    )
    parser.add_argument(
        "--omit-surface-contracts",
        action="store_true",
        help="Do not include per-surface contract refs in output.",
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


def run_read_feed_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        rendered = render_phase1_read_feed_projection(
            feed_contract_path=Path(args.contract_path),
            phase_gate_name=args.phase_gate_name,
            include_surface_contracts=not args.omit_surface_contracts,
            enable_phase_gate=True,
        )
    except (ReadFeedContractError, ReadFeedGateError, OSError, ValueError) as err:
        print(f"phase1 preview failed: {err}", file=sys.stderr)
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

    json.dump(rendered, sys.stdout, indent=None if args.compact else 2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_read_feed_preview()


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
