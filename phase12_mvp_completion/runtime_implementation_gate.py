"""Runtime implementation gate request projection.

This module renders the next owner-approval request after the external owner
answers are recorded. It is a planning artifact only and cannot grant runtime
authority, local model execution, supervisor attachment, connector behavior,
or durable evidence writes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from phase12_mvp_completion.completion import RUNTIME_DEPENDENCIES


class ArcRuntimeImplementationGateError(RuntimeError):
    """Raised when the runtime implementation gate request is unsafe."""


RUNTIME_IMPLEMENTATION_GATE_REQUEST_REF = (
    "docs/requests/ARC_BOT_RUNTIME_IMPLEMENTATION_GATE_REQUEST.md"
)
RUNTIME_IMPLEMENTATION_GATE_PACKET_REF = (
    "docs/proof_packets/ARC_BOT_RUNTIME_IMPLEMENTATION_GATE_REQUEST_PACKET.md"
)


RUNTIME_IMPLEMENTATION_APPROVAL_AREAS: tuple[dict[str, Any], ...] = (
    {
        "dependency_id": "live_supervisor_attachment",
        "owner_team": "LIMA Office Supervisor plane",
        "approval_needed": "live supervisor attachment contract and allowed transport",
        "required_evidence": [
            "supervisor identity/trust contract",
            "worker attach lifecycle",
            "read-only projection ingest acceptance",
            "disconnect/fail-closed behavior",
        ],
        "arc_bot_must_not_do_before_approval": [
            "open_supervisor_socket",
            "register_live_worker",
            "treat_local_state_as_supervisor_authority",
        ],
    },
    {
        "dependency_id": "worker_registration_lifecycle",
        "owner_team": "LIMA Office Supervisor and worker lifecycle owners",
        "approval_needed": "bounded Arc worker registration lifecycle",
        "required_evidence": [
            "worker identity fields",
            "tenant binding",
            "heartbeat cadence",
            "revocation/offline states",
        ],
        "arc_bot_must_not_do_before_approval": [
            "claim_registered_worker_status",
            "persist_runtime_worker_state",
        ],
    },
    {
        "dependency_id": "approval_token_issuance_or_verification",
        "owner_team": "LIMA Office Guardian/Supervisor verifier plane",
        "approval_needed": "durable approval token issuance and verification contract",
        "required_evidence": [
            "approval_token_id issuance semantics",
            "approval.binding verification semantics",
            "expiry/nonce/replay rejection",
            "mismatch reason refs",
        ],
        "arc_bot_must_not_do_before_approval": [
            "issue_approval_token",
            "verify_approval_token",
            "accept_approval_as_runtime_authority",
        ],
    },
    {
        "dependency_id": "verifier_result_ref_ingest",
        "owner_team": "LIMA Office Guardian/Supervisor verifier plane",
        "approval_needed": "verifier result-ref ingest contract",
        "required_evidence": [
            "allowed verifier result states",
            "result freshness rules",
            "binding to action/task/worker refs",
            "fail-closed missing-result behavior",
        ],
        "arc_bot_must_not_do_before_approval": [
            "trust_unverified_result_refs",
            "continue_on_missing_verifier_result",
        ],
    },
    {
        "dependency_id": "durable_evidence_writer_implementation",
        "owner_team": "LIMA Office Supervisor evidence plane",
        "approval_needed": "durable evidence writer and audit/Spine publication contract",
        "required_evidence": [
            "immutable evidence packet schema",
            "writer ownership and retention policy",
            "audit/Spine publication semantics",
            "failure and rollback handling",
        ],
        "arc_bot_must_not_do_before_approval": [
            "write_canonical_lima_evidence",
            "claim_evidence_durability",
            "publish_audit_spine_events",
        ],
    },
    {
        "dependency_id": "operator_console_server_state_implementation",
        "owner_team": "LIMA Office Supervisor and operator-console plane",
        "approval_needed": "operator-console server-state runtime implementation contract",
        "required_evidence": [
            "canonical server-state fields",
            "approval queue mutation rules",
            "operator decision lifecycle",
            "UI read-only/local display boundary",
        ],
        "arc_bot_must_not_do_before_approval": [
            "mutate_console_server_state",
            "own_approval_queue_authority",
            "use_display_state_as_authorization",
        ],
    },
    {
        "dependency_id": "local_model_executor_runtime_contract",
        "owner_team": "LIMA Office Guardian plane plus Supervisor model-route policy",
        "approval_needed": "Guardian-owned local-model executor contract",
        "required_evidence": [
            "executor syscall boundary",
            "model.route execution-enabled semantics",
            "redacted prompt/input/output refs",
            "network egress denial proof",
            "Ollama/Qwen failure and timeout policy",
        ],
        "arc_bot_must_not_do_before_approval": [
            "execute_local_inference",
            "call_ollama_qwen",
            "probe_model_endpoints",
            "treat_model_route_metadata_as_execution_authority",
        ],
    },
)


def build_arc_runtime_implementation_gate_request_projection() -> dict[str, Any]:
    """Build the next runtime-owner approval request without enabling runtime."""

    projection: dict[str, Any] = {
        "artifact_type": "arc_runtime_implementation_gate_request_projection",
        "artifact_id": "arc_runtime_implementation_gate_request_v1",
        "phase": "phase-12-runtime-implementation-gate-request",
        "status": "awaiting_runtime_implementation_gate_approval",
        "projection_scope": "planning_read_only",
        "source_access_mode": "repo_artifact_inspection_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "mvp_complete": False,
        "production_ready": False,
        "requires_external_owner_input": False,
        "requires_runtime_implementation_gate_approval": True,
        "request_ref": RUNTIME_IMPLEMENTATION_GATE_REQUEST_REF,
        "proof_packet_ref": RUNTIME_IMPLEMENTATION_GATE_PACKET_REF,
        "requested_runtime_dependencies": list(RUNTIME_DEPENDENCIES),
        "approval_areas": [dict(item) for item in RUNTIME_IMPLEMENTATION_APPROVAL_AREAS],
        "blocking_runtime_dependencies": list(RUNTIME_DEPENDENCIES),
        "safe_current_outputs": [
            "runtime_approval_request_packet",
            "owner_approval_checklist",
            "blocked_mvp_completion_projection",
        ],
        "must_not_start_until_approved": [
            "live_supervisor_attachment",
            "worker_registration_lifecycle",
            "approval_token_issuance_or_verification",
            "verifier_result_ref_ingest",
            "durable_evidence_write",
            "operator_console_state_authority",
            "local_model_invocation",
            "connector_read_or_write",
            "customer_system_mutation",
            "external_message_send",
            "production_deployment",
        ],
    }
    _assert_projection_safe(projection)
    return projection


def _assert_projection_safe(projection: dict[str, Any]) -> None:
    if projection.get("runtime_authority_blocked") is not True:
        raise ArcRuntimeImplementationGateError("runtime gate request cannot grant authority")
    if projection.get("runtime_execution_blocked") is not True:
        raise ArcRuntimeImplementationGateError("runtime gate request cannot grant execution")
    if projection.get("mvp_complete") is not False:
        raise ArcRuntimeImplementationGateError("runtime gate request cannot claim MVP completion")
    if projection.get("production_ready") is not False:
        raise ArcRuntimeImplementationGateError("runtime gate request cannot claim production readiness")
    if projection.get("requires_runtime_implementation_gate_approval") is not True:
        raise ArcRuntimeImplementationGateError("runtime gate approval must remain required")
    if set(projection.get("requested_runtime_dependencies", [])) != set(RUNTIME_DEPENDENCIES):
        raise ArcRuntimeImplementationGateError("runtime gate request dependencies are incomplete")
    approval_ids = {item.get("dependency_id") for item in projection.get("approval_areas", [])}
    if approval_ids != set(RUNTIME_DEPENDENCIES):
        raise ArcRuntimeImplementationGateError("runtime gate owner areas are incomplete")
    blocked = set(projection.get("must_not_start_until_approved", []))
    required_blocks = {
        "live_supervisor_attachment",
        "approval_token_issuance_or_verification",
        "durable_evidence_write",
        "local_model_invocation",
        "connector_read_or_write",
        "customer_system_mutation",
        "external_message_send",
        "production_deployment",
    }
    if not required_blocks.issubset(blocked):
        raise ArcRuntimeImplementationGateError("runtime gate request is missing blocked actions")


def run_arc_runtime_implementation_gate_request_preview(
    argv: list[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description="Render Arc Bot runtime implementation gate request metadata."
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument("--snapshot-path", help="Write projection JSON to this file.")
    args = parser.parse_args(argv)

    try:
        projection = build_arc_runtime_implementation_gate_request_projection()
    except (ArcRuntimeImplementationGateError, OSError, ValueError) as err:
        print(f"runtime implementation gate request failed: {err}", file=sys.stderr)
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
    return run_arc_runtime_implementation_gate_request_preview()


if __name__ == "__main__":
    raise SystemExit(main())
