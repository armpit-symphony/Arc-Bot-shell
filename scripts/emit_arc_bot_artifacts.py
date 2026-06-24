"""Emit deterministic Arc Bot preview artifacts.

This helper prints a read-only projection pack. It does not refresh fixtures
unless an explicit output path is provided, and it never performs runtime
execution, model calls, connector actions, or network access.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from phase0_runtime_ui_scaffold.phase_chain import (
    build_phase0_runtime_ui_scaffold_status_snapshot,
)
from phase0_runtime_ui_scaffold.phase2_runtime_control import (
    build_phase2_runtime_control_projection,
)
from phase0_runtime_ui_scaffold.runtime_control_consumer import (
    build_phase2_runtime_control_consumer_projection,
)
from phase0_runtime_ui_scaffold.runtime_control_execution import (
    build_runtime_control_execution_planning_projection,
)
from phase0_runtime_ui_scaffold.runtime_control_renderer import (
    build_runtime_control_renderer_projection,
)
from phase1_readiness.bundle import build_phase1_readiness_bundle
from arc_guardian_spine.intent_envelope import build_arc_intent_envelope_projection
from phase6_lima_office_integration.read_adapter import (
    build_arc_lima_office_read_adapter_projection,
)
from phase7_approval_evidence.readiness import (
    build_arc_approval_evidence_dependency_projection,
)
from phase10_field_deployment.package import (
    build_arc_field_deployment_readiness_projection,
)
from phase11_pilot_readiness.pilot import build_arc_pilot_readiness_projection
from phase12_mvp_completion.completion import build_arc_mvp_completion_gate_projection


def build_arc_bot_artifact_pack(*, fixtures_dir: str | Path = "tests/fixtures") -> dict[str, Any]:
    fixtures_path = Path(fixtures_dir)
    contract_path = fixtures_path / "arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json"
    payload_path = fixtures_path / "arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json"

    return {
        "artifact_type": "arc_bot_projection_pack",
        "artifact_id": "arc_bot_phase_lock_projection_pack_v1",
        "projection_scope": "read_only",
        "source_access_mode": "read_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "artifacts": {
            "phase0_scope_lock_status_snapshot": build_phase0_runtime_ui_scaffold_status_snapshot(
                contract_path=contract_path,
                payload_path=payload_path,
                include_guardian_suite_seam=True,
            ),
            "phase1_readiness_bundle": build_phase1_readiness_bundle(),
            "phase_b_intent_envelope": build_arc_intent_envelope_projection(),
            "phase_c_lima_office_read_adapter": (
                build_arc_lima_office_read_adapter_projection()
            ),
            "phase_d_approval_evidence_dependency": (
                build_arc_approval_evidence_dependency_projection()
            ),
            "phase_g_field_deployment_package": (
                build_arc_field_deployment_readiness_projection()
            ),
            "phase_h_narrow_pilot_readiness": build_arc_pilot_readiness_projection(),
            "phase_i_mvp_completion_gate": build_arc_mvp_completion_gate_projection(),
            "phase2_runtime_control": build_phase2_runtime_control_projection(
                feed_contract_path=contract_path,
                feed_payload_path=payload_path,
            ),
            "phase2_runtime_control_consumer": build_phase2_runtime_control_consumer_projection(
                control_contract_path=contract_path,
                control_payload_path=payload_path,
            ),
            "phase2_runtime_control_renderer": build_runtime_control_renderer_projection(
                control_contract_path=contract_path,
                control_payload_path=payload_path,
            ),
            "phase3_runtime_control_execution_planning": (
                build_runtime_control_execution_planning_projection(
                    control_contract_path=contract_path,
                    control_payload_path=payload_path,
                )
            ),
        },
    }


def run_emit_arc_bot_artifacts(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit deterministic Arc Bot preview artifacts.")
    parser.add_argument(
        "--fixtures-dir",
        default="tests/fixtures",
        help="Fixture directory containing Arc Bot contract and payload fixtures.",
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument("--output-path", help="Optional path to write the projection pack.")
    args = parser.parse_args(argv)

    try:
        artifact_pack = build_arc_bot_artifact_pack(fixtures_dir=args.fixtures_dir)
    except (OSError, ValueError, RuntimeError) as err:
        print(f"emit arc bot artifacts failed: {err}", file=sys.stderr)
        return 1

    rendered = json.dumps(
        artifact_pack,
        sort_keys=True,
        indent=None if args.compact else 2,
    )
    if args.output_path:
        Path(args.output_path).write_text(rendered + "\n", encoding="utf-8")

    sys.stdout.write(rendered)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_emit_arc_bot_artifacts()


if __name__ == "__main__":
    raise SystemExit(main())
