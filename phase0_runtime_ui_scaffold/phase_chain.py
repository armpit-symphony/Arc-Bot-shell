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
from .read_feed import DEFAULT_CONTRACT_PATH, DEFAULT_PAYLOAD_PATH, build_phase1_read_feed_projection
from .read_feed import build_phase1_read_feed_runtime_projection
from .runtime_control_consumer import (
    Phase2RuntimeControlConsumerError,
    Phase2RuntimeControlConsumerShapeError,
    build_phase2_runtime_control_consumer_projection,
)
from .runtime_consumer import (
    build_phase1_runtime_ui_consumer_projection,
)


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
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    return parser


def run_phase_chain_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        rendered = build_phase0_runtime_ui_scaffold_chain(
            contract_path=Path(args.contract_path),
            payload_path=Path(args.payload_path),
            include_phase_markers=not args.no_phase_markers,
        )
    except (
        OSError,
        ValueError,
        PhaseChainError,
        Phase2RuntimeControlError,
        Phase2RuntimeControlShapeError,
        Phase2RuntimeControlConsumerError,
        Phase2RuntimeControlConsumerShapeError,
    ) as err:
        print(f"phase chain preview failed: {err}", file=sys.stderr)
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
    return run_phase_chain_preview()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
