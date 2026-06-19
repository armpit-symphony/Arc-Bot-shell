"""Phase-0 runtime UI scaffold end-to-end projection chain renderer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from .phase2_runtime_control import (
    Phase2RuntimeControlError,
    Phase2RuntimeControlShapeError,
    build_phase2_runtime_control_projection,
)
from .guardian_suite_seam import (
    GuardianSuiteGateError,
    GuardianSuitePayloadError,
    DEFAULT_PAYLOAD_PATH as GUARDIAN_SUITE_SEAM_PAYLOAD_PATH,
    build_guardian_suite_seam_projection,
)
from .read_feed import DEFAULT_CONTRACT_PATH, DEFAULT_PAYLOAD_PATH, build_phase1_read_feed_projection
from .read_feed import build_phase1_read_feed_runtime_projection
from .runtime_control_consumer import (
    Phase2RuntimeControlConsumerError,
    Phase2RuntimeControlConsumerShapeError,
    build_phase2_runtime_control_consumer_projection,
)
from .runtime_consumer import build_phase1_runtime_ui_consumer_projection


REPO_ROOT = Path(__file__).resolve().parents[1]


class PhaseChainError(RuntimeError):
    """Raised when the full phase-0 chain cannot be safely assembled."""


def _assert_chain_link(condition: bool, message: str) -> None:
    if not condition:
        raise PhaseChainError(message)


def build_phase0_runtime_ui_scaffold_chain(
    *,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
    payload_path: str | Path = DEFAULT_PAYLOAD_PATH,
    include_phase_markers: bool = True,
    include_guardian_suite_seam: bool = False,
    guardian_suite_payload_path: str | Path = GUARDIAN_SUITE_SEAM_PAYLOAD_PATH,
) -> dict[str, Any]:
    """Build full chain projections for preview-only runtime UI seams."""

    projection_contract = build_phase1_read_feed_projection(contract_path)
    runtime_projection = build_phase1_read_feed_runtime_projection(
        feed_contract_path=contract_path,
        feed_payload_path=payload_path,
    )
    consumer_projection = build_phase1_runtime_ui_consumer_projection(
        feed_contract_path=contract_path,
        feed_payload_path=payload_path,
    )
    control_projection = build_phase2_runtime_control_projection(
        feed_contract_path=contract_path,
        feed_payload_path=payload_path,
    )
    control_consumer_projection = build_phase2_runtime_control_consumer_projection(
        control_contract_path=contract_path,
        control_payload_path=payload_path,
    )
    guardian_suite_projection = (
        build_guardian_suite_seam_projection(payload_path=Path(guardian_suite_payload_path))
        if include_guardian_suite_seam
        else None
    )

    _assert_chain_link(
        projection_contract["phase"] == "phase-1",
        "Chain requires phase-1 projection contract.",
    )
    _assert_chain_link(
        runtime_projection["projection_scope"] == "read_only",
        "Chain requires read-only runtime projection.",
    )
    _assert_chain_link(
        runtime_projection["source_access_mode"] == "read_only",
        "Chain requires read-only source access.",
    )
    _assert_chain_link(
        projection_contract["projection_gate_required"] is True,
        "Chain requires projection gate.",
    )
    _assert_chain_link(
        control_projection["runtime_authority_blocked"] is True,
        "Chain requires blocked runtime authority.",
    )
    _assert_chain_link(
        control_consumer_projection["runtime_execution_blocked"] is True,
        "Chain requires execution to stay blocked.",
    )
    if guardian_suite_projection is not None:
        _assert_chain_link(
            guardian_suite_projection["phase"] == projection_contract["phase"],
            "Guardian suite seam and read-feed seam must share the same phase.",
        )
        _assert_chain_link(
            guardian_suite_projection["source_reference"]
            == projection_contract["source_reference"],
            "Guardian suite seam must source from app.services.guardian.suite.",
        )
        _assert_chain_link(
            guardian_suite_projection["source_access_mode"]
            == projection_contract["source_access_mode"],
            "Guardian suite seam must remain read-only source access.",
        )
        _assert_chain_link(
            set(guardian_suite_projection["surfaces"]).issubset(
                set(projection_contract["surface_read_paths"].keys())
            ),
            "Guardian suite seam surfaces must align with read-feed surfaces.",
        )
        _assert_chain_link(
            bool(guardian_suite_projection["phase_gate"]["enabled"]),
            "Guardian suite seam must keep its phase gate enabled.",
        )
    _assert_chain_link(
        set(runtime_projection["surface_bindings"]) == set(consumer_projection["surface_bindings"]),
        "Runtime and consumer surfaces must align.",
    )
    _assert_chain_link(
        set(control_projection["surface_bindings"]) == set(consumer_projection["surface_bindings"]),
        "Control and consumer surfaces must align.",
    )

    chain: dict[str, Any] = {
        "artifact_type": "phase0_runtime_ui_scaffold_phase_chain_projection",
        "artifact_id": projection_contract["artifact_id"],
        "phase": projection_contract["phase"],
        "source_reference": projection_contract["source_reference"],
        "source_access_mode": projection_contract["source_access_mode"],
        "projection_scope": projection_contract["projection_scope"],
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "source_contract_file": str(contract_path),
        "source_payload_file": str(payload_path),
        "include_guardian_suite_seam": include_guardian_suite_seam,
        "projection_gate": {
            "name": projection_contract["projection_gate_name"],
            "required": projection_contract["projection_gate_required"],
            "enabled": True,
        },
        "surface_bindings": sorted(projection_contract["surface_read_paths"]),
        "phases": {
            "phase1_read_feed_contract": projection_contract,
            "phase1_read_feed_runtime": runtime_projection,
            "phase1_runtime_consumer": consumer_projection,
            "phase2_control": control_projection,
            "phase2_control_consumer": control_consumer_projection,
        },
    }
    if guardian_suite_projection is not None:
        chain["phases"]["phase0_guardian_suite_seam"] = guardian_suite_projection

    if include_phase_markers:
        chain["phase_markers"] = {
            "phase1": {"name": "read_feed_and_runtime_projection"},
            "phase2": {"name": "runtime_control_seam"},
            "authority_mode": "blocked",
            "execution_mode": "disabled",
        }

    return chain


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render the full Phase-0 runtime UI scaffold preview chain."
    )
    parser.add_argument(
        "contract_path",
        nargs="?",
        default=str(DEFAULT_CONTRACT_PATH),
        help="Contract fixture path (defaults to phase-1 read-feed contract fixture).",
    )
    parser.add_argument(
        "--payload-path",
        default=str(DEFAULT_PAYLOAD_PATH),
        help="Phase-1 read-feed payload path.",
    )
    parser.add_argument(
        "--no-phase-markers",
        action="store_true",
        help="Do not include phase marker metadata.",
    )
    parser.add_argument(
        "--with-guardian-suite-seam",
        action="store_true",
        help="Include guardian suite seam projection in the preview output.",
    )
    parser.add_argument(
        "--guardian-suite-payload-path",
        default=str(GUARDIAN_SUITE_SEAM_PAYLOAD_PATH),
        help=(
            "Guardian suite payload fixture path "
            "(defaults to tests/fixtures/arc_bot_guardian_suite_spine_payload.json)"
        ),
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument(
        "--emit-status-snapshot",
        action="store_true",
        help="Render canonical status snapshot for fixture parity checks.",
    )
    parser.add_argument(
        "--status-snapshot-path",
        help="Write canonical snapshot JSON to this file.",
    )
    parser.add_argument(
        "--no-guardian-suite-seam",
        action="store_true",
        help="Omit guardian-suite seam from status snapshot output.",
    )
    return parser


def run_phase_chain_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.status_snapshot_path and not args.emit_status_snapshot:
        print(
            "status-snapshot-path requires --emit-status-snapshot",
            file=sys.stderr,
        )
        return 1

    include_guardian_suite_seam = (
        args.with_guardian_suite_seam and not args.no_guardian_suite_seam
    )

    try:
        if args.emit_status_snapshot:
            rendered = build_phase0_runtime_ui_scaffold_status_snapshot(
                contract_path=Path(args.contract_path),
                payload_path=Path(args.payload_path),
                guardian_suite_payload_path=Path(args.guardian_suite_payload_path),
                include_guardian_suite_seam=include_guardian_suite_seam,
            )
        else:
            rendered = build_phase0_runtime_ui_scaffold_chain(
                contract_path=Path(args.contract_path),
                payload_path=Path(args.payload_path),
                include_phase_markers=not args.no_phase_markers,
                include_guardian_suite_seam=include_guardian_suite_seam,
                guardian_suite_payload_path=Path(args.guardian_suite_payload_path),
            )
    except (
        OSError,
        ValueError,
        PhaseChainError,
        Phase2RuntimeControlError,
        Phase2RuntimeControlShapeError,
        Phase2RuntimeControlConsumerError,
        Phase2RuntimeControlConsumerShapeError,
        GuardianSuitePayloadError,
        GuardianSuiteGateError,
    ) as err:
        print(f"phase chain preview failed: {err}", file=sys.stderr)
        return 1
    if args.status_snapshot_path:
        Path(args.status_snapshot_path).write_text(
            json.dumps(rendered, sort_keys=True, indent=2 if not args.compact else None)
            + "\n",
            encoding="utf-8",
        )

    json.dump(
        rendered,
        sys.stdout,
        indent=None if args.compact else 2,
        sort_keys=True,
    )
    sys.stdout.write("\n")
    return 0


def _compact_chain(chain: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "artifact_id": chain["artifact_id"],
        "artifact_type": chain["artifact_type"],
        "phase": chain["phase"],
        "projection_scope": chain["projection_scope"],
        "runtime_authority_blocked": chain["runtime_authority_blocked"],
        "runtime_execution_blocked": chain["runtime_execution_blocked"],
        "source_reference": chain["source_reference"],
        "source_access_mode": chain["source_access_mode"],
        "include_guardian_suite_seam": chain["include_guardian_suite_seam"],
        "phase_markers": chain["phase_markers"],
        "surface_bindings": chain["surface_bindings"],
    }
    compact["phases"] = {
        phase_name: _compact_phase_chain_phase(phase_data)
        for phase_name, phase_data in chain["phases"].items()
    }
    return compact


def _compact_phase_chain_phase(phase: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, object] = {}
    for key in [
        "artifact_id",
        "artifact_type",
        "phase",
        "payload_id",
        "payload_type",
        "projection_scope",
        "source_reference",
        "source_access_mode",
        "runtime_authority_blocked",
        "runtime_execution_blocked",
        "surface_bindings",
        "projection_bindings",
        "spine_sources",
        "spine_record_counts",
        "phase_gate",
    ]:
        if key in phase:
            compact[key] = phase[key]
    return compact


def _compact_projection_for_status_snapshot(projection: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, object] = {
        "artifact_id": projection["artifact_id"],
        "artifact_type": projection["artifact_type"],
        "phase": projection["phase"],
        "projection_scope": projection["projection_scope"],
        "source_reference": projection["source_reference"],
        "source_access_mode": projection["source_access_mode"],
    }

    for key in [
        "projection_source",
        "projection_source_file",
        "runtime_authority_blocked",
        "runtime_execution_blocked",
        "projection_bindings",
        "surface_bindings",
        "spine_sources",
        "spine_source_records",
        "spine_source_record_counts",
        "surface_summary",
        "phase_gate",
        "handoff_metadata",
        "consumer_metadata",
    ]:
        if key in projection:
            value = projection[key]
            if key == "projection_source_file" and isinstance(value, str):
                try:
                    value = str((REPO_ROOT / value).relative_to(REPO_ROOT)).replace("\\", "/")
                except ValueError:
                    value = value.replace("\\", "/")
            if key in {"projection_bindings", "surface_bindings", "spine_sources"} and isinstance(
                value, list
            ):
                compact[key] = sorted(value)
            else:
                compact[key] = value

    if "surface_read_paths" in projection:
        surface_read_paths = projection["surface_read_paths"]
        if isinstance(surface_read_paths, Mapping):
            compact["surface_read_paths"] = sorted(surface_read_paths.keys())

    if surfaces := projection.get("surfaces"):
        compact_surfaces: dict[str, object] = {}
        for surface_name in sorted(surfaces):
            surface_projection = surfaces[surface_name]
            compact_surface = {
                "projection_mode": surface_projection["projection_mode"],
            }
            if "runtime_authority_blocked" in surface_projection:
                compact_surface["runtime_authority_blocked"] = surface_projection[
                    "runtime_authority_blocked"
                ]
            if "runtime_execution_blocked" in surface_projection:
                compact_surface["runtime_execution_blocked"] = surface_projection[
                    "runtime_execution_blocked"
                ]
            if "status" in surface_projection:
                compact_surface["status"] = surface_projection["status"]
            compact_surfaces[surface_name] = compact_surface
        compact["surfaces"] = compact_surfaces

    return compact


def build_phase0_runtime_ui_scaffold_status_snapshot(
    *,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
    payload_path: str | Path = DEFAULT_PAYLOAD_PATH,
    guardian_suite_payload_path: str | Path = GUARDIAN_SUITE_SEAM_PAYLOAD_PATH,
    include_guardian_suite_seam: bool = True,
) -> dict[str, Any]:
    """Build canonical snapshot for phase-lock validation checks."""

    chain = _compact_chain(
        build_phase0_runtime_ui_scaffold_chain(
            contract_path=contract_path,
            payload_path=payload_path,
            include_guardian_suite_seam=include_guardian_suite_seam,
            guardian_suite_payload_path=guardian_suite_payload_path,
        )
    )

    phase1_projection_contract = build_phase1_read_feed_projection(contract_path)
    phase1_runtime_projection = build_phase1_read_feed_runtime_projection(
        feed_contract_path=contract_path,
        feed_payload_path=payload_path,
    )
    phase1_consumer_projection = build_phase1_runtime_ui_consumer_projection(
        feed_contract_path=contract_path,
        feed_payload_path=payload_path,
    )
    phase2_control_projection = build_phase2_runtime_control_projection(
        feed_contract_path=contract_path,
        feed_payload_path=payload_path,
    )
    phase2_control_consumer_projection = build_phase2_runtime_control_consumer_projection(
        control_contract_path=contract_path,
        control_payload_path=payload_path,
    )

    return {
        "snapshot_id": "arc_bot_runtime_ui_scaffold_phase0_scope_lock_status_snapshot_v1",
        "artifact_version": chain["phase"],
        "projection_source_reference": chain["source_reference"],
        "source_access_mode": "read_only",
        "phase_chain": chain,
        "phase1": {
            "read_feed_contract": _compact_projection_for_status_snapshot(
                phase1_projection_contract
            ),
            "read_feed_runtime": _compact_projection_for_status_snapshot(
                phase1_runtime_projection
            ),
            "runtime_consumer": _compact_projection_for_status_snapshot(
                phase1_consumer_projection
            ),
        },
        "phase2": {
            "runtime_control": _compact_projection_for_status_snapshot(
                phase2_control_projection
            ),
            "runtime_control_consumer": _compact_projection_for_status_snapshot(
                phase2_control_consumer_projection
            ),
        },
    }


def main() -> int:
    return run_phase_chain_preview()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
