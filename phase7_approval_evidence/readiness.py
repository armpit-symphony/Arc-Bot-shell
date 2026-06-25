"""Phase-D approval/evidence dependency projection.

This projection records the Guardian/LIMA Office decisions received for
approval token lineage, replay protection, durable evidence ownership, and
read-only state projection. It also records the remaining owner answers while
keeping Arc Bot runtime authority blocked until implementation gates are
explicitly approved.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ArcApprovalEvidenceDependencyError(RuntimeError):
    """Raised when the dependency projection is incomplete or unsafe."""


LIMA_OFFICE_EXTERNAL_HANDOFF: dict[str, str] = {
    "source_repo": "Lima-Office",
    "source_branch": "arc-bot-ollama-qwen-readiness-handoff",
    "source_commit": "4e1ed0e54515d41933b8d7132d091b2915d9dff7",
    "source_doc": "Lima-Office/docs/interop/ARC_BOT_GUARDIAN_LIMA_EXTERNAL_ANSWERS.md",
    "received_date": "2026-06-21",
}


ANSWERED_EXTERNAL_DEPENDENCIES: tuple[dict[str, Any], ...] = (
    {
        "dependency_id": "approval_token_reference_format",
        "owner": "Guardian / LIMA Office",
        "answer_status": "answered",
        "canonical_field": "approval_token_id",
        "typed_ref_form": "approval.token:<approval_token_id>",
        "blocks": ["approval_token_lineage", "operator_approval_lifecycle"],
    },
    {
        "dependency_id": "approval_binding_fields",
        "owner": "Guardian / LIMA Office",
        "answer_status": "answered",
        "canonical_contract_family": "approval.binding",
        "field_set_summary": [
            "tenant_and_customer_refs",
            "chain_ids",
            "guardian_decision_refs",
            "task_worker_tool_refs",
            "scope_hashes",
            "nonce_and_expiry",
            "status_and_verification",
            "mismatch_reasons",
            "evidence_refs",
        ],
        "blocks": ["non_reusable_approval", "replay_prevention"],
    },
    {
        "dependency_id": "signature_replay_verification_owner",
        "owner": "Guardian / LIMA Office",
        "answer_status": "answered",
        "verifier_owner": "LIMA Office Guardian/Supervisor verifier plane",
        "arc_bot_boundary": "consume_result_refs_only",
        "blocks": ["signed_intent_acceptance", "runtime_authority_acceptance"],
    },
    {
        "dependency_id": "runtime_state_snapshot_canonical_fields",
        "owner": "LIMA Office",
        "answer_status": "answered_without_standalone_schema",
        "runtime_state_contract": "read_only_projection",
        "projection_sources": [
            "supervisor.health",
            "worker.heartbeat",
            "worker.lifecycle",
            "model.route",
            "Guardian",
            "evidence",
            "console",
        ],
        "blocks": ["lima_office_read_adapter_freeze", "supervisor_pull_contract"],
    },
    {
        "dependency_id": "durable_evidence_writer_boundary",
        "owner": "Guardian / LIMA Office",
        "answer_status": "owner_answered_implementation_blocked",
        "writer_owner": "LIMA Office Supervisor evidence plane",
        "implementation_status": "durable_implementation_blocked",
        "blocks": ["durable_evidence_packets", "audit_spine_publication"],
    },
    {
        "dependency_id": "operator_console_server_state_owner",
        "owner": "LIMA Office Supervisor and operator-console plane",
        "answer_status": "owner_answered_implementation_blocked",
        "canonical_contract_family": "console.view, console.alert, console.action, supervisor.health",
        "arc_bot_boundary": "read_only_refs_only",
        "blocks": ["operator_approval_lifecycle", "approval_queue_runtime_state"],
    },
    {
        "dependency_id": "guardian_owned_local_model_executor_boundary",
        "owner": "LIMA Office Guardian plane plus Supervisor model-route policy",
        "answer_status": "owner_answered_executor_not_approved",
        "canonical_contract_family": "model.route",
        "execution_enabled": False,
        "arc_bot_boundary": "route_metadata_only_no_local_inference",
        "blocks": ["local_model_execution_approval", "model_preview_authority"],
    },
)


REMAINING_EXTERNAL_OWNER_QUESTIONS: tuple[dict[str, Any], ...] = ()


RUNTIME_IMPLEMENTATION_BLOCKERS: tuple[str, ...] = (
    "durable_evidence_writer_implementation",
    "approval_token_issuance_contract",
    "approval_token_verification_contract",
    "verifier_result_ref_ingest_contract",
    "supervisor_projection_ingest_contract",
    "operator_console_server_state_implementation",
    "local_model_executor_runtime_contract",
)


def build_arc_approval_evidence_dependency_projection() -> dict[str, Any]:
    """Build a blocked-readiness packet for Phase-D dependencies."""

    projection: dict[str, Any] = {
        "artifact_type": "arc_phase_d_approval_evidence_dependency_projection",
        "artifact_id": "arc_phase_d_approval_evidence_dependency_v1",
        "phase": "phase-d-approval-evidence",
        "status": "external_answers_recorded_runtime_still_blocked",
        "projection_scope": "planning_read_only",
        "source_access_mode": "read_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "requires_external_owner_input": False,
        "requires_runtime_implementation_gate_approval": True,
        "lima_office_external_handoff": dict(LIMA_OFFICE_EXTERNAL_HANDOFF),
        "handoff_request_refs": [
            "docs/requests/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_REQUEST.md",
            "docs/interop/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_RESPONSE.json",
        ],
        "answered_external_dependencies": list(ANSWERED_EXTERNAL_DEPENDENCIES),
        "remaining_external_owner_questions": list(REMAINING_EXTERNAL_OWNER_QUESTIONS),
        "unresolved_external_dependencies": [],
        "runtime_implementation_blockers": list(RUNTIME_IMPLEMENTATION_BLOCKERS),
        "blocked_capabilities": [
            "approval_token_issuance",
            "approval_token_verification",
            "approval_replay_protection",
            "signature_verification",
            "runtime_authority_acceptance",
            "durable_evidence_writer",
            "audit_spine_publication",
            "operator_console_state_authority",
            "local_model_execution_approval",
            "connector_action_approval",
            "external_send_approval",
        ],
        "safe_current_outputs": [
            "metadata_only_approval_request_refs",
            "redacted_evidence_refs",
            "read_only_lima_office_adapter_projection",
            "blocked_queue_projection",
            "approval_required_queue_projection",
            "recorded_owner_answer_refs",
        ],
        "unblock_acceptance_criteria": [
            "approval token issuance and verification contracts implemented",
            "verifier result ref ingest contract implemented",
            "supervisor projection ingest contract implemented",
            "durable evidence writer implementation approved",
            "operator-console server-state runtime implemented by LIMA Office owner",
            "Guardian-owned local-model executor contract explicitly approved and implemented",
            "tests added before any execution-adjacent behavior",
        ],
    }

    _assert_projection_safe(projection)
    return projection


def _assert_projection_safe(projection: dict[str, Any]) -> None:
    if projection.get("runtime_authority_blocked") is not True:
        raise ArcApprovalEvidenceDependencyError("Phase-D dependency cannot grant authority")
    if projection.get("runtime_execution_blocked") is not True:
        raise ArcApprovalEvidenceDependencyError("Phase-D dependency cannot grant execution")
    if projection.get("requires_external_owner_input") is not False:
        raise ArcApprovalEvidenceDependencyError(
            "Phase-D dependency owner answers must be recorded"
        )
    if projection.get("requires_runtime_implementation_gate_approval") is not True:
        raise ArcApprovalEvidenceDependencyError(
            "Phase-D dependency must still require runtime implementation approval"
        )
    answers = projection.get("answered_external_dependencies", [])
    if not answers:
        raise ArcApprovalEvidenceDependencyError(
            "Phase-D dependency requires recorded external answers"
        )
    dependency_ids = {answer.get("dependency_id") for answer in answers}
    required = {
        "approval_token_reference_format",
        "approval_binding_fields",
        "signature_replay_verification_owner",
        "runtime_state_snapshot_canonical_fields",
        "durable_evidence_writer_boundary",
        "operator_console_server_state_owner",
        "guardian_owned_local_model_executor_boundary",
    }
    if not required.issubset(dependency_ids):
        raise ArcApprovalEvidenceDependencyError("Phase-D external answers are incomplete")
    if projection.get("unresolved_external_dependencies"):
        raise ArcApprovalEvidenceDependencyError("external owner dependencies should be recorded")
    if set(projection.get("runtime_implementation_blockers", [])) != set(
        RUNTIME_IMPLEMENTATION_BLOCKERS
    ):
        raise ArcApprovalEvidenceDependencyError("runtime implementation blockers are incomplete")


def run_arc_approval_evidence_dependency_preview(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render Phase-D approval/evidence dependency readiness."
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument("--snapshot-path", help="Write projection JSON to this file.")
    args = parser.parse_args(argv)

    try:
        projection = build_arc_approval_evidence_dependency_projection()
    except (ArcApprovalEvidenceDependencyError, OSError, ValueError) as err:
        print(f"approval evidence dependency preview failed: {err}", file=sys.stderr)
        return 1

    if args.snapshot_path:
        Path(args.snapshot_path).write_text(
            json.dumps(projection, sort_keys=True, indent=2 if not args.compact else None)
            + "\n",
            encoding="utf-8",
        )

    json.dump(projection, sys.stdout, indent=None if args.compact else 2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_arc_approval_evidence_dependency_preview()


if __name__ == "__main__":
    raise SystemExit(main())
