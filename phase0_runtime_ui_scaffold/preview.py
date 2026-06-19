"""Phase-0 runtime UI scaffold preview interface.

This module exposes a read-only rendering interface for the existing adapter
payload fixtures. It performs no I/O beyond local fixture loading and emits no
runtime authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .adapter import (
    EXPECTED_PHASE_GATE_NAME,
    AdapterPayloadError,
    PhaseGateError,
    build_phase0_readonly_projection,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAYLOAD_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "arc_bot_runtime_ui_scaffold_adapter_payload.json"
)


def render_phase0_readonly_projection(
    *,
    adapter_payload_path: str | Path = DEFAULT_PAYLOAD_PATH,
    phase_gate_name: str = EXPECTED_PHASE_GATE_NAME,
    include_snapshot_payloads: bool = True,
) -> dict[str, Any]:
    """Return a read-only surface projection for Phase-0 fixtures."""

    return build_phase0_readonly_projection(
        adapter_payload_path,
        enable_phase_gate=True,
        phase_gate_name=phase_gate_name,
        include_snapshot_payloads=include_snapshot_payloads,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render Phase-0 runtime UI scaffolding fixture surfaces."
    )
    parser.add_argument(
        "payload_path",
        nargs="?",
        default=str(DEFAULT_PAYLOAD_PATH),
        help=(
            "Path to the adapter payload fixture "
            "(defaults to tests/fixtures/arc_bot_runtime_ui_scaffold_adapter_payload.json)"
        ),
    )
    parser.add_argument(
        "--phase-gate-name",
        default=EXPECTED_PHASE_GATE_NAME,
        help="Expected phase gate name for this fixture.",
    )
    parser.add_argument(
        "--omit-snapshots",
        action="store_true",
        help="Do not include raw snapshot payloads in output.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON.",
    )
    return parser


def run_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        projection = render_phase0_readonly_projection(
            adapter_payload_path=Path(args.payload_path),
            phase_gate_name=args.phase_gate_name,
            include_snapshot_payloads=not args.omit_snapshots,
        )
    except (PhaseGateError, AdapterPayloadError, OSError, ValueError) as err:
        print(f"preview failed: {err}", file=sys.stderr)
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
    return run_preview()


if __name__ == "__main__":
    raise SystemExit(main())
