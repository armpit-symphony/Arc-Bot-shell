"""Phase-5 office workflow template catalog.

The catalog defines deterministic workflow templates and draft-preview shapes
for guarded office document work. It does not read files, call models, use
provider SDKs, open sockets, invoke connectors, submit forms, send messages,
save final outputs, update customer records, or persist raw customer content.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from arc_guardian_spine.base import (
    ArcActionRequest,
    ArcSpineEvent,
    build_arc_evidence_refs,
    evaluate_arc_action,
)


PHASE5_WORKFLOW_IDS = (
    "intake_note_summary",
    "insurance_claim_packet_triage",
    "policy_document_summary",
    "missing_information_checklist",
    "customer_service_draft_reply",
    "internal_follow_up_task_draft",
)
PHASE5_ROLE_PROFILE_IDS = (
    "document_processing_bot",
    "customer_support_draft_bot",
    "billing_intake_assistant",
    "compliance_review_assistant",
)
PHASE5_APPROVAL_REQUIRED_ACTIONS = (
    "save_final_output",
    "send_external_message",
    "update_customer_record",
    "submit_form",
    "connector_write",
)
WORKFLOW_TEMPLATE_SCHEMA_REF = (
    "schema://arc-bot/phase5-office-workflow-template"
)
WORKFLOW_FIXTURE_REF = (
    "fixture://tests/fixtures/arc_bot_phase5_office_workflow_templates.json"
)


class OfficeWorkflowTemplateError(RuntimeError):
    """Raised when a workflow template would violate Phase-5 boundaries."""


@dataclass(frozen=True)
class OfficeWorkflowRequest:
    """Request envelope for a deterministic Phase-5 workflow preview."""

    workflow_id: str
    document_id: str = "doc-workflow-preview-001"
    source_ref: str = "upload://arc-bot/sample-intake.pdf"
    extraction_ref: str = "artifact://arc-bot/phase4/document-extraction-preview"
    tenant_id: str = "single_tenant_local"
    worker_id: str = "arc-worker-001"
    operator_id: str = "operator-local"
    role_profile_id: str = "document_processing_bot"
    sensitivity_class: str = "office_internal"


def build_office_workflow_template_catalog() -> dict[str, Any]:
    """Build the canonical Phase-5 workflow-template catalog."""

    workflows = [_workflow_template(workflow_id) for workflow_id in PHASE5_WORKFLOW_IDS]
    role_profiles = [_role_profile(role_id) for role_id in PHASE5_ROLE_PROFILE_IDS]
    projection: dict[str, Any] = {
        "artifact_id": "arc_bot_phase5_office_workflow_template_catalog",
        "artifact_type": "phase5_office_workflow_template_catalog",
        "phase": "phase-5",
        "projection_scope": "workflow_templates_draft_preview_only",
        "source_access_mode": "template_catalog_no_file_read",
        "schema_ref": WORKFLOW_TEMPLATE_SCHEMA_REF,
        "fixture_ref": WORKFLOW_FIXTURE_REF,
        "workflow_ids": list(PHASE5_WORKFLOW_IDS),
        "role_profile_ids": list(PHASE5_ROLE_PROFILE_IDS),
        "approval_required_actions": list(PHASE5_APPROVAL_REQUIRED_ACTIONS),
        "blocked_action_matrix": _blocked_action_matrix(),
        "workflow_templates": workflows,
        "role_profiles": role_profiles,
        "policy_refs": [
            "policy://arc-bot/phase5-draft-preview-only",
            "policy://arc-bot/guardian-required-before-consequential-action",
            "policy://arc-bot/no-external-send-without-approval",
            "policy://arc-bot/no-customer-system-mutation",
        ],
        "runbook_refs": [
            "runbook://arc-bot/workflow-template-review",
            "runbook://arc-bot/approval-required-actions",
        ],
        "raw_content_persisted": False,
        "file_read_performed": False,
        "file_write_performed": False,
        "model_invocation_performed": False,
        "network_egress_performed": False,
        "provider_sdk_used": False,
        "connector_action_performed": False,
        "customer_system_mutation_performed": False,
        "external_message_send_performed": False,
        "form_submission_performed": False,
        "runtime_execution_blocked": True,
        "runtime_authority_blocked": True,
    }
    _assert_phase5_guardrails(projection)
    return projection


def build_office_workflow_preview(request: OfficeWorkflowRequest) -> dict[str, Any]:
    """Build one deterministic draft workflow preview without execution."""

    validation_errors = _validate_request(request)
    catalog = build_office_workflow_template_catalog()
    workflow = _find_by_id(catalog["workflow_templates"], "workflow_id", request.workflow_id)
    role_profile = _find_by_id(catalog["role_profiles"], "role_profile_id", request.role_profile_id)
    if workflow is None:
        validation_errors.append("unsupported_workflow_id")
        workflow = _workflow_template(PHASE5_WORKFLOW_IDS[0])
    if role_profile is None:
        validation_errors.append("unsupported_role_profile_id")
        role_profile = _role_profile(PHASE5_ROLE_PROFILE_IDS[0])
    elif request.workflow_id not in role_profile["allowed_workflow_ids"]:
        validation_errors.append("workflow_not_allowed_for_role_profile")

    action_request = ArcActionRequest(
        action_id=f"arc-workflow-preview:{request.workflow_id}:{request.document_id}",
        action_kind="document_extract_preview",
        tenant_id=request.tenant_id,
        worker_id=request.worker_id,
        operator_id=request.operator_id,
        task_ref=f"task://arc/local/office-workflow-preview/{request.workflow_id}",
        data_sensitivity=request.sensitivity_class,
        requested_tool_pack="office_docs",
        evidence_refs=tuple(_workflow_evidence_ref_ids(request)),
        payload_summary=(
            "deterministic office workflow draft template preview; "
            "no customer-system mutation"
        ),
    )
    guardian_decision = evaluate_arc_action(action_request)
    evidence_refs = build_arc_evidence_refs(action_request, guardian_decision)
    spine_event = ArcSpineEvent(
        event_id=f"spine-event:office-workflow-preview:{request.workflow_id}:{request.document_id}",
        event_type="office_workflow_template_preview_projected",
        action_id=action_request.action_id,
        task_ref=action_request.task_ref,
        worker_id=request.worker_id,
        tenant_id=request.tenant_id,
        evidence_refs=action_request.evidence_refs,
        guardian_decision_ref=guardian_decision.decision_id,
        guardian_decision_result=guardian_decision.decision,
        reason_code=guardian_decision.reason_code,
    )
    status = "blocked" if validation_errors else "draft_preview_ready"

    projection: dict[str, Any] = {
        "artifact_id": f"arc_bot_phase5_office_workflow_preview:{request.workflow_id}:{request.document_id}",
        "artifact_type": "phase5_office_workflow_preview",
        "phase": "phase-5",
        "projection_scope": "workflow_draft_preview_only",
        "source_access_mode": "template_and_metadata_only_no_file_read",
        "workflow_id": request.workflow_id,
        "document_id": request.document_id,
        "tenant_id": request.tenant_id,
        "worker_id": request.worker_id,
        "role_profile_id": request.role_profile_id,
        "preview_status": status,
        "blocked_reasons": sorted(set(validation_errors)),
        "ready_for_operator_review": status == "draft_preview_ready",
        "workflow_template": workflow,
        "role_profile": role_profile,
        "draft_output": _draft_output_preview(request, workflow),
        "blocked_action_matrix": workflow["blocked_action_matrix"],
        "approval_required_actions": list(PHASE5_APPROVAL_REQUIRED_ACTIONS),
        "guardian_decision": asdict(guardian_decision),
        "approval_request": None,
        "evidence_refs": [asdict(ref) for ref in evidence_refs],
        "spine_event": asdict(spine_event),
        "policy_refs": workflow["policy_refs"],
        "runbook_refs": workflow["runbook_refs"],
        "raw_content_persisted": False,
        "raw_content_included": False,
        "file_read_performed": False,
        "file_write_performed": False,
        "ocr_performed": False,
        "parser_invoked": False,
        "model_invocation_performed": False,
        "network_egress_performed": False,
        "provider_sdk_used": False,
        "connector_action_performed": False,
        "customer_system_mutation_performed": False,
        "external_message_send_performed": False,
        "form_submission_performed": False,
        "runtime_execution_blocked": True,
        "runtime_authority_blocked": True,
        "request": asdict(request),
    }
    _assert_phase5_guardrails(projection)
    return projection


def _workflow_template(workflow_id: str) -> dict[str, Any]:
    definition = _workflow_definitions()[workflow_id]
    return {
        "workflow_id": workflow_id,
        "name": definition["name"],
        "purpose": definition["purpose"],
        "output_artifact_type": definition["output_artifact_type"],
        "output_mode": "draft_preview_only",
        "schema_ref": WORKFLOW_TEMPLATE_SCHEMA_REF,
        "fixture_ref": WORKFLOW_FIXTURE_REF,
        "allowed_input_artifacts": [
            "phase3_document_intake_preview",
            "phase4_document_extraction_preview",
        ],
        "draft_sections": definition["draft_sections"],
        "recommended_role_profile_ids": definition["recommended_role_profile_ids"],
        "guardian_required": True,
        "requires_operator_review": True,
        "finalization_requires_approval": True,
        "local_model_required_for_template": False,
        "blocked_action_matrix": _blocked_action_matrix(),
        "approval_required_actions": list(PHASE5_APPROVAL_REQUIRED_ACTIONS),
        "policy_refs": [
            f"policy://arc-bot/phase5-workflow/{workflow_id}",
            "policy://arc-bot/draft-preview-only",
            "policy://arc-bot/no-customer-system-mutation",
        ],
        "runbook_refs": [
            f"runbook://arc-bot/workflows/{workflow_id}",
            "runbook://arc-bot/operator-review-before-final-output",
        ],
        "raw_content_persisted": False,
        "file_read_performed": False,
        "file_write_performed": False,
        "model_invocation_performed": False,
        "connector_action_performed": False,
        "customer_system_mutation_performed": False,
        "external_message_send_performed": False,
        "form_submission_performed": False,
        "runtime_execution_blocked": True,
        "runtime_authority_blocked": True,
    }


def _role_profile(role_profile_id: str) -> dict[str, Any]:
    role = _role_definitions()[role_profile_id]
    return {
        "role_profile_id": role_profile_id,
        "name": role["name"],
        "purpose": role["purpose"],
        "allowed_workflow_ids": role["allowed_workflow_ids"],
        "allowed_tool_packs": ["office_docs"],
        "guardian_required": True,
        "output_mode": "draft_preview_only",
        "blocked_action_matrix": _blocked_action_matrix(),
        "cannot_send_external_messages": True,
        "cannot_update_customer_records": True,
        "cannot_submit_forms": True,
        "cannot_write_connectors": True,
        "runtime_execution_blocked": True,
        "runtime_authority_blocked": True,
    }


def _workflow_definitions() -> dict[str, dict[str, Any]]:
    return {
        "intake_note_summary": {
            "name": "Intake note summary",
            "purpose": "Prepare a short operator-reviewed intake note from document metadata and redacted extraction refs.",
            "output_artifact_type": "intake_note_summary_draft",
            "draft_sections": [
                "source_metadata",
                "customer_or_case_refs_placeholder",
                "key_dates_placeholder",
                "operator_review_notes",
            ],
            "recommended_role_profile_ids": [
                "document_processing_bot",
                "billing_intake_assistant",
            ],
        },
        "insurance_claim_packet_triage": {
            "name": "Insurance claim packet triage",
            "purpose": "Prepare an insurance-office triage preview for claim packet routing and missing evidence review.",
            "output_artifact_type": "insurance_claim_triage_draft",
            "draft_sections": [
                "claim_packet_type_placeholder",
                "policy_or_claim_refs_placeholder",
                "loss_event_metadata_placeholder",
                "triage_route_recommendation_placeholder",
            ],
            "recommended_role_profile_ids": [
                "document_processing_bot",
                "compliance_review_assistant",
            ],
        },
        "policy_document_summary": {
            "name": "Policy document summary",
            "purpose": "Prepare a policy-document summary preview for operator review.",
            "output_artifact_type": "policy_document_summary_draft",
            "draft_sections": [
                "policy_metadata",
                "coverage_sections_placeholder",
                "exclusions_placeholder",
                "operator_review_questions",
            ],
            "recommended_role_profile_ids": [
                "document_processing_bot",
                "compliance_review_assistant",
            ],
        },
        "missing_information_checklist": {
            "name": "Missing information checklist",
            "purpose": "Prepare a checklist draft for information an operator may need to request or verify.",
            "output_artifact_type": "missing_information_checklist_draft",
            "draft_sections": [
                "missing_identifiers_placeholder",
                "missing_dates_placeholder",
                "missing_signatures_placeholder",
                "operator_verification_items",
            ],
            "recommended_role_profile_ids": [
                "document_processing_bot",
                "customer_support_draft_bot",
                "billing_intake_assistant",
                "compliance_review_assistant",
            ],
        },
        "customer_service_draft_reply": {
            "name": "Customer-service draft reply",
            "purpose": "Prepare an internal draft reply for operator review before any external send.",
            "output_artifact_type": "customer_service_reply_draft",
            "draft_sections": [
                "customer_context_placeholder",
                "acknowledgement_draft_placeholder",
                "requested_information_placeholder",
                "approval_before_send_notice",
            ],
            "recommended_role_profile_ids": ["customer_support_draft_bot"],
        },
        "internal_follow_up_task_draft": {
            "name": "Internal follow-up task draft",
            "purpose": "Prepare an internal follow-up task draft for supervisor or team review.",
            "output_artifact_type": "internal_follow_up_task_draft",
            "draft_sections": [
                "assignee_placeholder",
                "due_date_placeholder",
                "source_document_refs",
                "blocked_external_actions_notice",
            ],
            "recommended_role_profile_ids": [
                "document_processing_bot",
                "billing_intake_assistant",
                "compliance_review_assistant",
            ],
        },
    }


def _role_definitions() -> dict[str, dict[str, Any]]:
    return {
        "document_processing_bot": {
            "name": "Document Processing Bot",
            "purpose": "Stages document intake, extraction, summaries, triage, checklists, and internal task drafts for review.",
            "allowed_workflow_ids": [
                "intake_note_summary",
                "insurance_claim_packet_triage",
                "policy_document_summary",
                "missing_information_checklist",
                "internal_follow_up_task_draft",
            ],
        },
        "customer_support_draft_bot": {
            "name": "Customer Support Draft Bot",
            "purpose": "Prepares customer-service draft replies and missing-info checklists for operator approval.",
            "allowed_workflow_ids": [
                "missing_information_checklist",
                "customer_service_draft_reply",
            ],
        },
        "billing_intake_assistant": {
            "name": "Billing Intake Assistant",
            "purpose": "Prepares intake summaries, missing-information checklists, and internal billing follow-up drafts.",
            "allowed_workflow_ids": [
                "intake_note_summary",
                "missing_information_checklist",
                "internal_follow_up_task_draft",
            ],
        },
        "compliance_review_assistant": {
            "name": "Compliance Review Assistant",
            "purpose": "Prepares compliance review summaries, triage notes, checklists, and internal follow-up drafts.",
            "allowed_workflow_ids": [
                "insurance_claim_packet_triage",
                "policy_document_summary",
                "missing_information_checklist",
                "internal_follow_up_task_draft",
            ],
        },
    }


def _blocked_action_matrix() -> dict[str, dict[str, Any]]:
    return {
        action: {
            "status": "approval_required_before_execution",
            "guardian_required": True,
            "runtime_execution_blocked": True,
            "grants_execution": False,
            "allowed_in_phase5": False,
        }
        for action in PHASE5_APPROVAL_REQUIRED_ACTIONS
    }


def _draft_output_preview(
    request: OfficeWorkflowRequest,
    workflow: dict[str, Any],
) -> dict[str, Any]:
    return {
        "artifact_type": "phase5_workflow_draft_preview",
        "output_mode": "draft_preview_only",
        "output_status": "draft_pending_operator_review",
        "document_id": request.document_id,
        "source_ref": request.source_ref,
        "extraction_ref": request.extraction_ref,
        "workflow_id": workflow["workflow_id"],
        "output_artifact_type": workflow["output_artifact_type"],
        "sections": [
            {
                "section_id": section_id,
                "status": "placeholder_pending_operator_review",
                "raw_content_included": False,
            }
            for section_id in workflow["draft_sections"]
        ],
        "redacted_summary_only": True,
        "final_output_saved": False,
        "external_message_send_performed": False,
        "customer_system_mutation_performed": False,
        "connector_action_performed": False,
    }


def _validate_request(request: OfficeWorkflowRequest) -> list[str]:
    errors: list[str] = []
    required_fields = {
        "workflow_id": request.workflow_id,
        "document_id": request.document_id,
        "source_ref": request.source_ref,
        "extraction_ref": request.extraction_ref,
        "tenant_id": request.tenant_id,
        "worker_id": request.worker_id,
        "operator_id": request.operator_id,
        "role_profile_id": request.role_profile_id,
        "sensitivity_class": request.sensitivity_class,
    }
    for field_name, value in required_fields.items():
        if not isinstance(value, str) or not value.strip():
            errors.append(f"missing_{field_name}")
    return errors


def _workflow_evidence_ref_ids(request: OfficeWorkflowRequest) -> list[str]:
    return [
        f"evidence://arc-bot/document-intake/{request.document_id}",
        f"evidence://arc-bot/document-extraction/{request.document_id}",
        f"evidence://arc-bot/office-workflow-template/{request.workflow_id}",
        f"evidence://arc-bot/operator-review-required/{request.workflow_id}",
    ]


def _find_by_id(items: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    for item in items:
        if item[key] == value:
            return item
    return None


def _assert_phase5_guardrails(projection: dict[str, Any]) -> None:
    blocked_flags = (
        "raw_content_persisted",
        "file_read_performed",
        "file_write_performed",
        "model_invocation_performed",
        "network_egress_performed",
        "provider_sdk_used",
        "connector_action_performed",
        "customer_system_mutation_performed",
        "external_message_send_performed",
        "form_submission_performed",
    )
    for flag in blocked_flags:
        if projection[flag] is not False:
            raise OfficeWorkflowTemplateError(f"{flag} must remain false")
    if projection["runtime_execution_blocked"] is not True:
        raise OfficeWorkflowTemplateError("runtime_execution_blocked must stay true")
    if projection["runtime_authority_blocked"] is not True:
        raise OfficeWorkflowTemplateError("runtime_authority_blocked must stay true")

    matrices = [projection.get("blocked_action_matrix", {})]
    if "workflow_templates" in projection:
        matrices.extend(item["blocked_action_matrix"] for item in projection["workflow_templates"])
        matrices.extend(item["blocked_action_matrix"] for item in projection["role_profiles"])
    if "workflow_template" in projection:
        matrices.append(projection["workflow_template"]["blocked_action_matrix"])
        matrices.append(projection["role_profile"]["blocked_action_matrix"])
    for matrix in matrices:
        for action in PHASE5_APPROVAL_REQUIRED_ACTIONS:
            entry = matrix.get(action)
            if not entry or entry["status"] != "approval_required_before_execution":
                raise OfficeWorkflowTemplateError(f"{action} must require approval")
            if entry["runtime_execution_blocked"] is not True:
                raise OfficeWorkflowTemplateError(f"{action} must remain blocked")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render Phase-5 office workflow template previews."
    )
    parser.add_argument("--workflow-id", choices=PHASE5_WORKFLOW_IDS)
    parser.add_argument("--document-id", default="doc-workflow-preview-001")
    parser.add_argument("--source-ref", default="upload://arc-bot/sample-intake.pdf")
    parser.add_argument(
        "--extraction-ref",
        default="artifact://arc-bot/phase4/document-extraction-preview",
    )
    parser.add_argument("--tenant-id", default="single_tenant_local")
    parser.add_argument("--worker-id", default="arc-worker-001")
    parser.add_argument("--operator-id", default="operator-local")
    parser.add_argument("--role-profile-id", default="document_processing_bot")
    parser.add_argument("--sensitivity-class", default="office_internal")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--snapshot-path")
    return parser


def run_office_workflow_templates_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.workflow_id:
            projection = build_office_workflow_preview(
                OfficeWorkflowRequest(
                    workflow_id=args.workflow_id,
                    document_id=args.document_id,
                    source_ref=args.source_ref,
                    extraction_ref=args.extraction_ref,
                    tenant_id=args.tenant_id,
                    worker_id=args.worker_id,
                    operator_id=args.operator_id,
                    role_profile_id=args.role_profile_id,
                    sensitivity_class=args.sensitivity_class,
                )
            )
        else:
            projection = build_office_workflow_template_catalog()
    except OfficeWorkflowTemplateError as err:
        print(f"office workflow template preview failed: {err}", file=sys.stderr)
        return 1

    if args.snapshot_path:
        Path(args.snapshot_path).write_text(
            json.dumps(
                projection,
                sort_keys=True,
                indent=None if args.compact else 2,
            )
            + "\n",
            encoding="utf-8",
        )

    json.dump(projection, sys.stdout, indent=None if args.compact else 2, sort_keys=True)
    if not args.compact:
        sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_office_workflow_templates_preview()


if __name__ == "__main__":
    raise SystemExit(main())
