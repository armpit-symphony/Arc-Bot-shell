"""Read-only Arc-to-LIMA Office state adapter projection.

This module exports Arc worker status and queue metadata in a LIMA
Office-readable shape. It does not import LIMA runtime modules, open sockets,
persist state, dispatch workers, issue approvals, call models, or call
connectors.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from arc_guardian_spine import ArcActionRequest, ArcLocalModelSeat, evaluate_arc_action
from arc_guardian_spine.intent_envelope import build_arc_intent_envelope_projection


class ArcLimaOfficeReadAdapterError(RuntimeError):
    """Raised when the read adapter would violate the no-execution contract."""


def _default_action_requests() -> tuple[ArcActionRequest, ...]:
    return (
        ArcActionRequest(
            action_id="arc-action-lima-office-intake-preview-001",
            action_kind="document_intake_preview",
        ),
        ArcActionRequest(
            action_id="arc-action-lima-office-extract-approval-001",
            action_kind="document_extract_preview",
            requested_tool_pack="local_model_preview",
        ),
        ArcActionRequest(
            action_id="arc-action-lima-office-external-send-001",
            action_kind="external_send",
        ),
    )


def _queue_entry(request: ArcActionRequest) -> dict[str, Any]:
    decision = evaluate_arc_action(request)
    return {
        "action_id": request.action_id,
        "action_kind": request.action_kind,
        "task_ref": request.task_ref,
        "tenant_id": request.tenant_id,
        "worker_id": request.worker_id,
        "operator_id": request.operator_id,
        "decision": decision.decision,
        "reason_code": decision.reason_code,
        "guardian_decision_ref": decision.decision_id,
        "policy_refs": list(decision.policy_refs),
        "evidence_refs": list(decision.evidence_refs),
        "runbook_refs": list(decision.runbook_refs),
        "runtime_authority_blocked": decision.runtime_authority_blocked,
        "runtime_execution_blocked": decision.runtime_execution_blocked,
        "local_model_execution_blocked": decision.local_model_execution_blocked,
    }


def _assert_projection_safe(projection: dict[str, Any]) -> None:
    if projection.get("runtime_authority_blocked") is not True:
        raise ArcLimaOfficeReadAdapterError("Read adapter cannot grant runtime authority")
    if projection.get("runtime_execution_blocked") is not True:
        raise ArcLimaOfficeReadAdapterError("Read adapter cannot grant runtime execution")
    if projection.get("source_access_mode") != "read_only":
        raise ArcLimaOfficeReadAdapterError("Read adapter source access must be read-only")
    if projection.get("connector_actions_allowed") is not False:
        raise ArcLimaOfficeReadAdapterError("Read adapter cannot allow connector actions")
    if projection.get("customer_system_mutation_allowed") is not False:
        raise ArcLimaOfficeReadAdapterError("Read adapter cannot allow customer mutation")
    if projection.get("external_send_allowed") is not False:
        raise ArcLimaOfficeReadAdapterError("Read adapter cannot allow external sends")
    if projection.get("local_model_execution_allowed") is not False:
        raise ArcLimaOfficeReadAdapterError("Read adapter cannot allow model execution")


def build_arc_lima_office_read_adapter_projection(
    *,
    action_requests: tuple[ArcActionRequest, ...] | None = None,
    local_model_seat: ArcLocalModelSeat | None = None,
) -> dict[str, Any]:
    """Build a deterministic LIMA Office-readable state packet."""

    requests = _default_action_requests() if action_requests is None else action_requests
    if not requests:
        raise ArcLimaOfficeReadAdapterError("Read adapter requires at least one action request")

    queue_entries = [_queue_entry(request) for request in requests]
    blocked_queue = [entry for entry in queue_entries if entry["decision"] == "deny"]
    approval_required_queue = [
        entry for entry in queue_entries if entry["decision"] == "approval_required"
    ]
    preview_queue = [entry for entry in queue_entries if entry["decision"] == "allow_preview"]
    evidence_refs = sorted(
        {
            evidence_ref
            for entry in queue_entries
            for evidence_ref in entry["evidence_refs"]
        }
    )
    policy_refs = sorted(
        {
            policy_ref
            for entry in queue_entries
            for policy_ref in entry["policy_refs"]
        }
    )

    model_seat = local_model_seat or ArcLocalModelSeat()
    envelope_projection = build_arc_intent_envelope_projection(requests[0])

    projection: dict[str, Any] = {
        "artifact_type": "arc_lima_office_read_adapter_projection",
        "artifact_id": "arc_lima_office_read_adapter_v1",
        "phase": "phase-6-read-adapter-contract",
        "projection_scope": "read_only",
        "source_access_mode": "read_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "connector_actions_allowed": False,
        "customer_system_mutation_allowed": False,
        "external_send_allowed": False,
        "local_model_execution_allowed": False,
        "lima_office_target": {
            "target_contract": "RuntimeStateSnapshot",
            "target_mode": "read_only_pull",
            "live_lima_imports_used": False,
            "supervisor_owns_authoritative_state": True,
        },
        "deployment_topology": {
            "supervisor_servers": 1,
            "worker_min": 1,
            "worker_max": 8,
            "tenant_mode": "single_tenant",
        },
        "worker_status": {
            "worker_id": requests[0].worker_id,
            "tenant_id": requests[0].tenant_id,
            "heartbeat_posture": "projection_only_not_live",
            "lima_office_attachment_posture": "metadata_only",
            "local_model_seat": asdict(model_seat),
        },
        "queues": {
            "preview_queue": preview_queue,
            "blocked_queue": blocked_queue,
            "approval_required_queue": approval_required_queue,
        },
        "preview_artifacts": [
            {
                "artifact_type": envelope_projection["artifact_type"],
                "artifact_id": envelope_projection["artifact_id"],
                "runtime_authority_blocked": envelope_projection[
                    "runtime_authority_blocked"
                ],
                "runtime_execution_blocked": envelope_projection[
                    "runtime_execution_blocked"
                ],
            }
        ],
        "evidence_refs": evidence_refs,
        "policy_refs": policy_refs,
        "handoff_requirements": {
            "guardian_decision_required_for_execution": True,
            "approval_token_lineage_required": True,
            "evidence_lineage_required": True,
            "signature_verification_required": True,
            "execution_allowed": False,
        },
    }

    _assert_projection_safe(projection)
    return projection


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a read-only Arc-to-LIMA Office state adapter projection."
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument("--snapshot-path", help="Write projection JSON to this file.")
    return parser


def run_arc_lima_office_read_adapter_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        projection = build_arc_lima_office_read_adapter_projection()
    except (ArcLimaOfficeReadAdapterError, OSError, ValueError) as err:
        print(f"arc lima office read adapter preview failed: {err}", file=sys.stderr)
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
    return run_arc_lima_office_read_adapter_preview()


if __name__ == "__main__":
    raise SystemExit(main())
