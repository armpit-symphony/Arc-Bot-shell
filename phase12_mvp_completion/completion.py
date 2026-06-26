"""Phase-12 MVP completion gate projection.

This module evaluates Arc Bot against the documented MVP completion criteria
using current repo artifacts only. It is an evidence/readiness projection, not
an MVP declaration. It must stay blocked while real runtime, approval,
supervisor, evidence-writer, local-model, connector, and operator-console
implementation gates remain unresolved.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ArcMvpCompletionGateError(RuntimeError):
    """Raised when the MVP completion gate projection is incomplete or unsafe."""


LIMA_OFFICE_EXTERNAL_HANDOFF: dict[str, str] = {
    "source_repo": "Lima-Office",
    "source_branch": "arc-bot-ollama-qwen-readiness-handoff",
    "source_commit": "4e1ed0e54515d41933b8d7132d091b2915d9dff7",
    "source_doc": "Lima-Office/docs/interop/ARC_BOT_GUARDIAN_LIMA_EXTERNAL_ANSWERS.md",
    "received_date": "2026-06-21",
}


ANSWERED_EXTERNAL_DEPENDENCIES: tuple[str, ...] = (
    "approval_token_reference_format",
    "approval_binding_fields",
    "signature_replay_verification_owner",
    "runtime_state_snapshot_projection_boundary",
    "durable_evidence_writer_owner",
    "operator_console_server_state_owner",
    "guardian_owned_local_model_executor_boundary",
)


UNRESOLVED_EXTERNAL_DEPENDENCIES: tuple[str, ...] = ()


MVP_COMPLETION_CRITERIA: tuple[dict[str, Any], ...] = (
    {
        "criterion_id": "local_arc_worker_attached_to_lima_office",
        "criterion": "Arc Bot runs locally on a PC attached to LIMA Office.",
        "status": "blocked_external_runtime_gate",
        "evidence_refs": [
            "docs/contracts/ARC_LIMA_OFFICE_READ_ADAPTER.md",
            "phase6_lima_office_integration/read_adapter.py",
        ],
        "missing_evidence": [
            "live supervisor attachment contract",
            "worker registration lifecycle",
            "supervisor projection ingest implementation",
        ],
    },
    {
        "criterion_id": "approved_local_model_preview_only",
        "criterion": "Arc Bot uses only a local model for approved preview work.",
        "status": "blocked_external_runtime_gate",
        "evidence_refs": [
            "docs/LIMA_OFFICE_TEAM_PHASE2_REQUEST.md",
            "phase2_local_model_readiness/readiness.py",
            "docs/interop/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_RESPONSE.json",
        ],
        "missing_evidence": [
            "Guardian-owned local-model executor contract approved for execution",
            "durable model-preview evidence writer",
            "model-preview verifier result refs",
        ],
    },
    {
        "criterion_id": "document_intake_and_guarded_drafts",
        "criterion": "Arc Bot can intake office documents and produce guarded previews/drafts.",
        "status": "planning_ready_runtime_blocked",
        "evidence_refs": [
            "phase3_document_intake/intake.py",
            "phase4_document_extraction/extraction.py",
            "phase5_office_workflows/workflows.py",
            "phase11_pilot_readiness/pilot.py",
        ],
        "missing_evidence": [
            "approved raw-document processing boundary",
            "operator-console workflow over server-side state",
        ],
    },
    {
        "criterion_id": "guardian_gates_every_consequential_action",
        "criterion": "Guardian gates every model call and every consequential action.",
        "status": "blocked_external_runtime_gate",
        "evidence_refs": [
            "arc_guardian_spine/base.py",
            "arc_guardian_spine/intent_envelope.py",
            "docs/contracts/ARC_APPROVAL_EVIDENCE_DEPENDENCY.md",
        ],
        "missing_evidence": [
            "Guardian/Supervisor verifier result-ref ingest",
            "approval token issuance/verification implementation",
            "runtime syscall gate implementation",
        ],
    },
    {
        "criterion_id": "spine_records_task_decision_approval_evidence",
        "criterion": "Spine records task, decision, approval, and evidence lineage.",
        "status": "blocked_external_runtime_gate",
        "evidence_refs": [
            "arc_guardian_spine/base.py",
            "phase7_approval_evidence/readiness.py",
        ],
        "missing_evidence": [
            "durable evidence writer implementation",
            "audit/Spine publication implementation",
            "approval lifecycle persistence",
        ],
    },
    {
        "criterion_id": "lima_office_reads_worker_status",
        "criterion": "LIMA Office can read Arc worker status and task/evidence state.",
        "status": "planning_ready_runtime_blocked",
        "evidence_refs": [
            "docs/contracts/ARC_LIMA_OFFICE_READ_ADAPTER.md",
            "phase6_lima_office_integration/read_adapter.py",
        ],
        "missing_evidence": [
            "read-only supervisor projection ingest implementation",
            "RuntimeStateSnapshot first-class schema if LIMA Office later requires one",
        ],
    },
    {
        "criterion_id": "operators_can_approve_deny_block",
        "criterion": "Operators can approve, deny, or block work.",
        "status": "blocked_external_runtime_gate",
        "evidence_refs": [
            "docs/contracts/ARC_APPROVAL_EVIDENCE_DEPENDENCY.md",
            "docs/contracts/ARC_BOT_OPERATOR_CONSOLE_STATE.md",
            "docs/interop/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_RESPONSE.json",
        ],
        "missing_evidence": [
            "operator-console MVP over LIMA Office server-side state",
            "approval token issuance/verification implementation",
            "approval replay protection",
        ],
    },
    {
        "criterion_id": "no_hidden_background_actions",
        "criterion": "No hidden background actions.",
        "status": "satisfied_by_static_contracts",
        "evidence_refs": [
            "AUTONOMY_BOUNDARIES.md",
            "CONTRACTS.md",
            "scripts/arc_worker_smoke.ps1",
        ],
        "missing_evidence": [],
    },
    {
        "criterion_id": "no_live_connector_writes",
        "criterion": "No live connector writes without a later approved phase.",
        "status": "satisfied_by_static_contracts",
        "evidence_refs": [
            "CONTRACTS.md",
            "phase5_office_workflows/workflows.py",
            "phase11_pilot_readiness/pilot.py",
        ],
        "missing_evidence": [],
    },
    {
        "criterion_id": "no_production_claims",
        "criterion": "No production claims until field deployment evidence exists.",
        "status": "satisfied_by_static_contracts",
        "evidence_refs": [
            "docs/deployment/ARC_FIELD_DEPLOYMENT_PACKAGE.md",
            "phase10_field_deployment/package.py",
            "docs/proof_packets/ARC_BOT_PHASE_G_FIELD_DEPLOYMENT_PACKAGE_PACKET.md",
        ],
        "missing_evidence": [],
    },
)


RUNTIME_DEPENDENCIES: tuple[str, ...] = (
    "live_supervisor_attachment",
    "worker_registration_lifecycle",
    "approval_token_issuance_or_verification",
    "verifier_result_ref_ingest",
    "durable_evidence_writer_implementation",
    "operator_console_server_state_implementation",
    "local_model_executor_runtime_contract",
)


def build_arc_mvp_completion_gate_projection() -> dict[str, Any]:
    """Build deterministic MVP completion-readiness metadata."""

    criteria = [dict(item) for item in MVP_COMPLETION_CRITERIA]
    blocking = [
        item
        for item in criteria
        if item["status"] in {"blocked_external_runtime_gate", "planning_ready_runtime_blocked"}
    ]
    satisfied = [
        item for item in criteria if item["status"] == "satisfied_by_static_contracts"
    ]

    projection: dict[str, Any] = {
        "artifact_type": "arc_mvp_completion_gate_projection",
        "artifact_id": "arc_mvp_completion_gate_v1",
        "phase": "phase-12-mvp-completion-gate",
        "status": "not_complete_blocked_by_runtime_dependencies",
        "projection_scope": "completion_readiness_read_only",
        "source_access_mode": "repo_artifact_inspection_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "mvp_complete": False,
        "production_ready": False,
        "requires_external_owner_input": False,
        "requires_runtime_implementation_gate_approval": True,
        "lima_office_external_handoff": dict(LIMA_OFFICE_EXTERNAL_HANDOFF),
        "criteria_total": len(criteria),
        "criteria_satisfied_by_static_contracts": len(satisfied),
        "criteria_blocked_or_runtime_pending": len(blocking),
        "completion_criteria": criteria,
        "answered_external_dependencies": list(ANSWERED_EXTERNAL_DEPENDENCIES),
        "blocking_external_dependencies": list(UNRESOLVED_EXTERNAL_DEPENDENCIES),
        "blocking_runtime_dependencies": list(RUNTIME_DEPENDENCIES),
        "safe_current_outputs": [
            "static_contracts",
            "read_only_projections",
            "sanitized_pilot_readiness",
            "field_deployment_planning_package",
            "smoke_and_guardrail_checks",
            "recorded_owner_answer_refs",
        ],
        "must_not_implement_until_unblocked": [
            "live_supervisor_attachment",
            "local_model_invocation",
            "approval_token_issuance_or_verification",
            "durable_evidence_write",
            "connector_read_or_write",
            "customer_system_mutation",
            "external_message_send",
            "production_deployment",
        ],
        "evidence_refs": [
            "docs/ROADMAP_ARC_BOT_COMPLETION.md#phase-12---mvp-completion-criteria",
            "docs/audits/ARC_BOT_COMPLETION_AUDIT_AND_PHASE_PLAN.md",
            "docs/requests/GUARDIAN_LIMA_OFFICE_PHASE_D_APPROVAL_EVIDENCE_REQUEST.md",
            "docs/requests/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_REQUEST.md",
            "docs/requests/ARC_BOT_RUNTIME_IMPLEMENTATION_GATE_REQUEST.md",
            "docs/interop/ARC_BOT_LIMA_OFFICE_EXTERNAL_ANSWERS.md",
            "docs/interop/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_RESPONSE.json",
        ],
    }
    _assert_projection_safe(projection)
    return projection


def _assert_projection_safe(projection: dict[str, Any]) -> None:
    if projection.get("mvp_complete") is not False:
        raise ArcMvpCompletionGateError("MVP completion gate cannot claim completion")
    if projection.get("production_ready") is not False:
        raise ArcMvpCompletionGateError("MVP completion gate cannot claim production readiness")
    if projection.get("runtime_authority_blocked") is not True:
        raise ArcMvpCompletionGateError("MVP completion gate cannot grant authority")
    if projection.get("runtime_execution_blocked") is not True:
        raise ArcMvpCompletionGateError("MVP completion gate cannot grant execution")
    if projection.get("requires_external_owner_input") is not False:
        raise ArcMvpCompletionGateError("MVP completion gate should have recorded owner answers")
    if projection.get("requires_runtime_implementation_gate_approval") is not True:
        raise ArcMvpCompletionGateError("MVP completion gate must require runtime implementation approval")
    if projection.get("criteria_total") != len(projection.get("completion_criteria", [])):
        raise ArcMvpCompletionGateError("criteria count mismatch")
    if projection.get("criteria_blocked_or_runtime_pending", 0) <= 0:
        raise ArcMvpCompletionGateError("completion must remain blocked while runtime gates are missing")
    if len(projection.get("answered_external_dependencies", [])) != 7:
        raise ArcMvpCompletionGateError("expected seven recorded external answers")
    if projection.get("blocking_external_dependencies"):
        raise ArcMvpCompletionGateError("unexpected remaining external dependencies")
    if len(projection.get("blocking_runtime_dependencies", [])) != len(RUNTIME_DEPENDENCIES):
        raise ArcMvpCompletionGateError("expected seven runtime-dependent blockers")


def run_arc_mvp_completion_gate_preview(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render Arc Bot MVP completion gate readiness metadata."
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument("--snapshot-path", help="Write projection JSON to this file.")
    args = parser.parse_args(argv)

    try:
        projection = build_arc_mvp_completion_gate_projection()
    except (ArcMvpCompletionGateError, OSError, ValueError) as err:
        print(f"MVP completion gate preview failed: {err}", file=sys.stderr)
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
    return run_arc_mvp_completion_gate_preview()


if __name__ == "__main__":
    raise SystemExit(main())
