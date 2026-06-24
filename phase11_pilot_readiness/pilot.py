"""Phase-H/Phase-11 narrow pilot readiness projection.

This module defines the first safe pilot package for Arc Bot: insurance intake
summary plus missing-information checklist. The package is intentionally
sanitized and planning-only. It does not read files, invoke models, attach to a
live supervisor, call connectors, send messages, persist evidence, or mutate
customer systems.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from phase5_office_workflows.workflows import (
    OfficeWorkflowRequest,
    build_office_workflow_preview,
)


class ArcPilotReadinessError(RuntimeError):
    """Raised when the pilot readiness projection is incomplete or unsafe."""


PILOT_WORKFLOW_IDS: tuple[str, ...] = (
    "insurance_claim_packet_triage",
    "missing_information_checklist",
)

PILOT_DOCS: tuple[str, ...] = (
    "docs/pilots/INSURANCE_INTAKE_NARROW_PILOT.md",
    "docs/pilots/INSURANCE_INTAKE_SAMPLE_DATA_POLICY.md",
)

PILOT_BLOCKED_CAPABILITIES: tuple[str, ...] = (
    "raw_customer_document_processing",
    "local_model_invocation",
    "cloud_model_fallback",
    "connector_read_or_write",
    "customer_record_update",
    "external_message_send",
    "form_submission",
    "durable_evidence_write",
    "approval_token_issuance_or_verification",
    "production_pilot_claim",
)


def build_arc_pilot_readiness_projection() -> dict[str, Any]:
    """Build deterministic readiness metadata for the first narrow pilot."""

    workflow_previews = [
        build_office_workflow_preview(
            OfficeWorkflowRequest(
                workflow_id=workflow_id,
                document_id="sanitized-insurance-intake-sample-001",
                source_ref="sample://arc-bot/sanitized-insurance-intake-metadata",
                extraction_ref="artifact://arc-bot/phase4/sanitized-extraction-preview",
                role_profile_id="compliance_review_assistant",
                sensitivity_class="sanitized_sample",
            )
        )
        for workflow_id in PILOT_WORKFLOW_IDS
    ]

    projection: dict[str, Any] = {
        "artifact_type": "arc_narrow_pilot_readiness_projection",
        "artifact_id": "arc_narrow_pilot_readiness_v1",
        "phase": "phase-h-narrow-pilot-readiness",
        "status": "planning_ready_runtime_blocked",
        "projection_scope": "planning_read_only",
        "source_access_mode": "sanitized_metadata_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "production_ready": False,
        "pilot_execution_allowed": False,
        "requires_external_owner_input": True,
        "external_dependency_ref": (
            "docs/requests/GUARDIAN_LIMA_OFFICE_PHASE_D_APPROVAL_EVIDENCE_REQUEST.md"
        ),
        "pilot_name": "insurance_intake_summary_and_missing_information_checklist",
        "pilot_scope": {
            "tenant_mode": "single_tenant",
            "supervisor_servers": 1,
            "worker_min": 1,
            "worker_max": 8,
            "sample_data_mode": "sanitized_local_samples_only",
            "live_customer_data_allowed": False,
        },
        "pilot_docs": list(PILOT_DOCS),
        "workflow_ids": list(PILOT_WORKFLOW_IDS),
        "workflow_previews": workflow_previews,
        "operator_review_gates": [
            "operator reviews every generated draft",
            "operator confirms evidence refs before any future approval",
            "operator blocks missing or stale approval lineage",
            "operator records corrections as notes only in this phase",
        ],
        "blocked_runtime_capabilities": list(PILOT_BLOCKED_CAPABILITIES),
        "pilot_metrics_planned": [
            "draft_usefulness_rating",
            "missing_information_precision",
            "operator_correction_count",
            "blocked_action_count",
            "evidence_gap_count",
            "approval_friction_notes",
        ],
        "exit_criteria": [
            "sanitized sample workflow previews render",
            "every pilot output remains draft_preview_only",
            "every consequential action remains blocked or approval-required",
            "no raw customer content enters repo state",
            "no live connector or model path is used",
            "Phase-D dependencies remain explicit blockers for live pilot work",
        ],
        "evidence_refs": [
            "proof:arc-bot:phase-h-narrow-pilot-readiness",
            "workflow:insurance_claim_packet_triage",
            "workflow:missing_information_checklist",
        ],
        "policy_refs": [
            "CONTRACTS.md#arc-narrow-pilot-readiness",
            "AUTONOMY_BOUNDARIES.md",
            "SECURITY_MODEL.md",
        ],
    }
    _assert_projection_safe(projection)
    return projection


def _assert_projection_safe(projection: dict[str, Any]) -> None:
    required_false = (
        "production_ready",
        "pilot_execution_allowed",
    )
    for key in required_false:
        if projection.get(key) is not False:
            raise ArcPilotReadinessError(f"{key} must remain false")
    if projection.get("runtime_authority_blocked") is not True:
        raise ArcPilotReadinessError("pilot readiness cannot grant authority")
    if projection.get("runtime_execution_blocked") is not True:
        raise ArcPilotReadinessError("pilot readiness cannot grant execution")

    scope = projection.get("pilot_scope", {})
    if scope.get("tenant_mode") != "single_tenant":
        raise ArcPilotReadinessError("pilot scope must be single-tenant")
    if scope.get("supervisor_servers") != 1:
        raise ArcPilotReadinessError("pilot scope must use one supervisor")
    if scope.get("worker_min") != 1 or scope.get("worker_max") != 8:
        raise ArcPilotReadinessError("pilot scope must preserve 1-8 workers")
    if scope.get("live_customer_data_allowed") is not False:
        raise ArcPilotReadinessError("live customer data must stay blocked")

    workflow_previews = projection.get("workflow_previews", [])
    if len(workflow_previews) != len(PILOT_WORKFLOW_IDS):
        raise ArcPilotReadinessError("pilot workflow previews are incomplete")
    for preview in workflow_previews:
        if preview.get("runtime_execution_blocked") is not True:
            raise ArcPilotReadinessError("workflow preview cannot grant execution")
        if preview.get("model_invocation_performed") is not False:
            raise ArcPilotReadinessError("workflow preview cannot invoke models")
        if preview.get("connector_action_performed") is not False:
            raise ArcPilotReadinessError("workflow preview cannot call connectors")
        if preview.get("customer_system_mutation_performed") is not False:
            raise ArcPilotReadinessError("workflow preview cannot mutate customer systems")
        if preview.get("external_message_send_performed") is not False:
            raise ArcPilotReadinessError("workflow preview cannot send messages")


def run_arc_pilot_readiness_preview(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render Arc Bot narrow pilot readiness metadata."
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument("--snapshot-path", help="Write projection JSON to this file.")
    args = parser.parse_args(argv)

    try:
        projection = build_arc_pilot_readiness_projection()
    except (ArcPilotReadinessError, OSError, ValueError) as err:
        print(f"pilot readiness preview failed: {err}", file=sys.stderr)
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
    return run_arc_pilot_readiness_preview()


if __name__ == "__main__":
    raise SystemExit(main())
