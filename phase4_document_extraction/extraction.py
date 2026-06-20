"""Phase-4 guarded document extraction preview contract.

This module creates deterministic metadata previews for local office documents.
It never opens files, reads document bytes, performs OCR, invokes parsers, uses
any provider SDK, opens sockets, writes raw content, or mutates a
customer system.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from arc_guardian_spine.base import (
    ArcActionRequest,
    ArcSpineEvent,
    build_arc_approval_request,
    build_arc_evidence_refs,
    evaluate_arc_action,
)
from phase3_document_intake import (
    DocumentIntakeRequest,
    build_document_intake_preview,
)


PHASE4_REQUIRED_LOCAL_MODEL_GATES = (
    "local_model_seat_ready",
    "approval_token_ref",
    "redaction_policy_ref",
    "output_policy_ref",
)


class DocumentExtractionPreviewError(RuntimeError):
    """Raised when the extraction preview would violate Phase-4 boundaries."""


@dataclass(frozen=True)
class DocumentExtractionRequest:
    """Metadata-only extraction preview request for one local office document."""

    extraction_id: str
    document_id: str
    source_ref: str
    document_type: str = "auto"
    tenant_id: str = "single_tenant_local"
    worker_id: str = "arc-worker-001"
    operator_id: str = "operator-local"
    sensitivity_class: str = "office_internal"
    operator_supplied_category: str = "uncategorized_office_document"
    upload_ref: str = "upload://arc-bot/manual-staging"
    requires_local_model: bool = False
    local_model_seat_ready: bool = False
    approval_token_ref: str = ""
    redaction_policy_ref: str = ""
    output_policy_ref: str = ""


class LocalModelPreviewProvider(Protocol):
    """Injectable provider shape for later approved local model previews."""

    def build_model_preview(
        self,
        request: DocumentExtractionRequest,
        deterministic_preview: dict[str, Any],
    ) -> dict[str, Any]:
        """Return a preview projection without performing runtime execution."""


@dataclass(frozen=True)
class BlockedLocalModelPreviewProvider:
    """Default provider that records why local model invocation remains blocked."""

    blocked_reason: str = "local_model_invocation_requires_guardian_approval_and_policies"

    def build_model_preview(
        self,
        request: DocumentExtractionRequest,
        deterministic_preview: dict[str, Any],
    ) -> dict[str, Any]:
        missing_gates = _missing_local_model_gates(request)
        return {
            "provider_kind": "blocked_local_model_preview_provider",
            "provider_runtime": "readiness_packet_runtime_family_label",
            "provider_model_family": "qwen",
            "provider_model_alias": "qwen2.5:7b",
            "provider_interface": "injectable_preview_provider",
            "provider_called_for_projection": True,
            "runtime_execution_blocked": True,
            "runtime_authority_blocked": True,
            "local_model_execution_blocked": True,
            "model_invocation_performed": False,
            "network_egress_performed": False,
            "provider_sdk_used": False,
            "blocked_reason": self.blocked_reason,
            "missing_gate_data": missing_gates,
            "phase4_execution_boundary": "provider_interface_only_no_model_call",
            "deterministic_preview_ref": deterministic_preview["artifact_id"],
        }


def build_document_extraction_preview(
    request: DocumentExtractionRequest,
    provider: LocalModelPreviewProvider | None = None,
) -> dict[str, Any]:
    """Build a guarded extraction preview artifact without runtime execution."""

    validation_errors = _validate_request(request)
    intake_preview = build_document_intake_preview(
        DocumentIntakeRequest(
            document_id=request.document_id,
            source_ref=request.source_ref,
            document_type=request.document_type,
            tenant_id=request.tenant_id,
            sensitivity_class=request.sensitivity_class,
            intake_operator=request.operator_id,
            upload_ref=request.upload_ref,
        )
    )
    if intake_preview["intake_status"] == "blocked":
        validation_errors.extend(
            f"intake_{reason}" for reason in intake_preview["blocked_reasons"]
        )

    missing_model_gates = (
        _missing_local_model_gates(request) if request.requires_local_model else []
    )
    action_request = ArcActionRequest(
        action_id=f"arc-extraction-preview:{request.extraction_id}",
        action_kind="document_extract_preview",
        tenant_id=request.tenant_id,
        worker_id=request.worker_id,
        operator_id=request.operator_id,
        task_ref=f"task://arc/local/document-extraction-preview/{request.document_id}",
        data_sensitivity=request.sensitivity_class,
        requested_tool_pack=(
            "local_model_preview" if request.requires_local_model else "office_docs"
        ),
        evidence_refs=tuple(_evidence_ref_ids(request)),
        payload_summary=(
            "metadata-only deterministic document extraction preview; "
            "raw document content omitted"
        ),
    )
    guardian_decision = evaluate_arc_action(action_request)
    evidence_refs = build_arc_evidence_refs(action_request, guardian_decision)
    approval_request = build_arc_approval_request(action_request, guardian_decision)

    deterministic_preview = _deterministic_metadata_preview(request, intake_preview)
    provider_projection = (
        (provider or BlockedLocalModelPreviewProvider()).build_model_preview(
            request,
            deterministic_preview,
        )
        if request.requires_local_model
        else _non_model_provider_projection(deterministic_preview)
    )
    spine_event = ArcSpineEvent(
        event_id=f"spine-event:document-extraction-preview:{request.extraction_id}",
        event_type="document_extraction_preview_projected",
        action_id=action_request.action_id,
        task_ref=action_request.task_ref,
        worker_id=request.worker_id,
        tenant_id=request.tenant_id,
        evidence_refs=action_request.evidence_refs,
        guardian_decision_ref=guardian_decision.decision_id,
        guardian_decision_result=guardian_decision.decision,
        reason_code=guardian_decision.reason_code,
    )

    status = _extraction_status(
        intake_blocked=intake_preview["intake_status"] == "blocked",
        validation_errors=validation_errors,
        requires_local_model=request.requires_local_model,
        missing_model_gates=missing_model_gates,
    )
    projection: dict[str, Any] = {
        "artifact_id": deterministic_preview["artifact_id"],
        "artifact_type": "phase4_document_extraction_preview",
        "phase": "phase-4",
        "projection_scope": "deterministic_metadata_preview",
        "source_access_mode": "metadata_only_no_file_read",
        "extraction_id": request.extraction_id,
        "document_id": request.document_id,
        "tenant_id": request.tenant_id,
        "worker_id": request.worker_id,
        "source_ref": request.source_ref,
        "upload_ref": request.upload_ref,
        "extraction_status": status,
        "blocked_reasons": sorted(set(validation_errors)),
        "ready_for_review": status == "ready_for_review",
        "approval_required": guardian_decision.approval_required,
        "local_model_required": request.requires_local_model,
        "deterministic_preview": deterministic_preview,
        "filename_metadata": deterministic_preview["filename_metadata"],
        "classified_document_type": deterministic_preview["classified_document_type"],
        "page_count_placeholder": deterministic_preview["page_count_placeholder"],
        "checksum_placeholder": deterministic_preview["checksum_placeholder"],
        "operator_supplied_document_category": (
            request.operator_supplied_category.strip()
            or "uncategorized_office_document"
        ),
        "local_model_gate": {
            "required": request.requires_local_model,
            "local_model_seat_ready": request.local_model_seat_ready,
            "approval_token_ref": request.approval_token_ref,
            "redaction_policy_ref": request.redaction_policy_ref,
            "output_policy_ref": request.output_policy_ref,
            "missing_gate_data": missing_model_gates,
            "all_gate_data_present": not missing_model_gates,
            "phase4_execution_authority": "blocked_until_phase8_execution_gate",
        },
        "local_model_preview": provider_projection,
        "document_intake_preview": intake_preview,
        "guardian_decision": asdict(guardian_decision),
        "approval_request": asdict(approval_request) if approval_request else None,
        "evidence_refs": [asdict(ref) for ref in evidence_refs],
        "spine_event": asdict(spine_event),
        "policy_refs": [
            "policy://arc-bot/document-extraction-metadata-preview-only",
            "policy://arc-bot/local-model-only",
            "policy://arc-bot/no-cloud-fallback",
            "policy://arc-bot/no-provider-token",
            "policy://arc-bot/no-raw-content-persistence",
            "policy://arc-bot/guardian-required-before-local-model-preview",
        ],
        "runbook_refs": [
            "runbook://arc-bot/document-extraction-preview-review",
            "runbook://arc-bot/local-model-seat-readiness",
            "runbook://arc-bot/redaction-review",
        ],
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
        "runtime_execution_blocked": True,
        "runtime_authority_blocked": True,
        "local_model_execution_blocked": True,
        "request": asdict(request),
    }
    _assert_phase4_guardrails(projection)
    return projection


def _deterministic_metadata_preview(
    request: DocumentExtractionRequest,
    intake_preview: dict[str, Any],
) -> dict[str, Any]:
    filename = _filename_from_source_ref(request.source_ref)
    return {
        "artifact_id": f"arc_bot_phase4_document_extraction:{request.extraction_id}",
        "preview_kind": "deterministic_metadata_only",
        "document_id": request.document_id,
        "source_ref": request.source_ref,
        "filename_metadata": {
            "display_name": filename,
            "extension": _extension_from_filename(filename),
            "source_ref_scheme": _scheme_from_source_ref(request.source_ref),
        },
        "classified_document_type": intake_preview["classified_document_type"],
        "page_count_placeholder": "not_calculated_no_file_read",
        "checksum_placeholder": "not_calculated_no_file_read",
        "operator_supplied_document_category": (
            request.operator_supplied_category.strip()
            or "uncategorized_office_document"
        ),
        "file_read_performed": False,
        "parser_invoked": False,
        "ocr_performed": False,
        "model_invocation_performed": False,
    }


def _filename_from_source_ref(source_ref: str) -> str:
    cleaned = source_ref.strip()
    if not cleaned:
        return "unknown"
    normalized = cleaned.replace("\\", "/").rstrip("/")
    filename = normalized.rsplit("/", 1)[-1]
    return filename or "unknown"


def _extension_from_filename(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def _scheme_from_source_ref(source_ref: str) -> str:
    if "://" not in source_ref:
        return "local_label"
    return source_ref.split("://", 1)[0].lower() or "unknown"


def _validate_request(request: DocumentExtractionRequest) -> list[str]:
    errors: list[str] = []
    required_fields = {
        "extraction_id": request.extraction_id,
        "document_id": request.document_id,
        "source_ref": request.source_ref,
        "tenant_id": request.tenant_id,
        "worker_id": request.worker_id,
        "operator_id": request.operator_id,
        "operator_supplied_category": request.operator_supplied_category,
    }
    for field_name, value in required_fields.items():
        if not isinstance(value, str) or not value.strip():
            errors.append(f"missing_{field_name}")
    return errors


def _missing_local_model_gates(request: DocumentExtractionRequest) -> list[str]:
    missing = []
    if not request.local_model_seat_ready:
        missing.append("local_model_seat_ready")
    if not request.approval_token_ref.strip():
        missing.append("approval_token_ref")
    if not request.redaction_policy_ref.strip():
        missing.append("redaction_policy_ref")
    if not request.output_policy_ref.strip():
        missing.append("output_policy_ref")
    return missing


def _evidence_ref_ids(request: DocumentExtractionRequest) -> list[str]:
    refs = [
        "evidence://arc-bot/local-model-seat-readiness",
        f"evidence://arc-bot/document-intake/{request.document_id}",
        f"evidence://arc-bot/document-extraction/{request.extraction_id}",
    ]
    if request.redaction_policy_ref.strip():
        refs.append(request.redaction_policy_ref)
    else:
        refs.append(f"evidence://arc-bot/redaction-policy/{request.document_id}")
    if request.output_policy_ref.strip():
        refs.append(request.output_policy_ref)
    else:
        refs.append(f"evidence://arc-bot/output-policy/{request.document_id}")
    return refs


def _non_model_provider_projection(deterministic_preview: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider_kind": "not_required_for_deterministic_preview",
        "provider_interface": "injectable_preview_provider",
        "provider_called_for_projection": False,
        "runtime_execution_blocked": True,
        "runtime_authority_blocked": True,
        "local_model_execution_blocked": True,
        "model_invocation_performed": False,
        "network_egress_performed": False,
        "provider_sdk_used": False,
        "blocked_reason": "local_model_not_required_for_deterministic_metadata",
        "missing_gate_data": [],
        "deterministic_preview_ref": deterministic_preview["artifact_id"],
    }


def _extraction_status(
    *,
    intake_blocked: bool,
    validation_errors: list[str],
    requires_local_model: bool,
    missing_model_gates: list[str],
) -> str:
    if intake_blocked or validation_errors:
        return "blocked"
    if requires_local_model:
        return "approval_required" if missing_model_gates else "blocked_runtime"
    return "ready_for_review"


def _assert_phase4_guardrails(projection: dict[str, Any]) -> None:
    blocked_flags = (
        "raw_content_persisted",
        "raw_content_included",
        "file_read_performed",
        "file_write_performed",
        "ocr_performed",
        "parser_invoked",
        "model_invocation_performed",
        "network_egress_performed",
        "provider_sdk_used",
        "connector_action_performed",
        "customer_system_mutation_performed",
    )
    for flag in blocked_flags:
        if projection[flag] is not False:
            raise DocumentExtractionPreviewError(f"{flag} must remain false")
    if projection["runtime_execution_blocked"] is not True:
        raise DocumentExtractionPreviewError("runtime_execution_blocked must stay true")
    if projection["runtime_authority_blocked"] is not True:
        raise DocumentExtractionPreviewError("runtime_authority_blocked must stay true")
    if projection["local_model_execution_blocked"] is not True:
        raise DocumentExtractionPreviewError("local_model_execution_blocked must stay true")
    local_model_preview = projection["local_model_preview"]
    if local_model_preview["model_invocation_performed"] is not False:
        raise DocumentExtractionPreviewError("local model provider must not invoke model")
    if local_model_preview["runtime_execution_blocked"] is not True:
        raise DocumentExtractionPreviewError("local model provider must remain blocked")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render Phase-4 guarded document extraction preview."
    )
    parser.add_argument("--extraction-id", default="extract-preview-001")
    parser.add_argument("--document-id", default="doc-extract-preview-001")
    parser.add_argument("--source-ref", default="upload://arc-bot/sample-intake.pdf")
    parser.add_argument("--document-type", default="auto")
    parser.add_argument("--tenant-id", default="single_tenant_local")
    parser.add_argument("--worker-id", default="arc-worker-001")
    parser.add_argument("--operator-id", default="operator-local")
    parser.add_argument("--sensitivity-class", default="office_internal")
    parser.add_argument("--operator-category", default="uncategorized_office_document")
    parser.add_argument("--upload-ref", default="upload://arc-bot/manual-staging")
    parser.add_argument("--requires-local-model", action="store_true")
    parser.add_argument("--local-model-seat-ready", action="store_true")
    parser.add_argument("--approval-token-ref", default="")
    parser.add_argument("--redaction-policy-ref", default="")
    parser.add_argument("--output-policy-ref", default="")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--snapshot-path")
    return parser


def run_document_extraction_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    request = DocumentExtractionRequest(
        extraction_id=args.extraction_id,
        document_id=args.document_id,
        source_ref=args.source_ref,
        document_type=args.document_type,
        tenant_id=args.tenant_id,
        worker_id=args.worker_id,
        operator_id=args.operator_id,
        sensitivity_class=args.sensitivity_class,
        operator_supplied_category=args.operator_category,
        upload_ref=args.upload_ref,
        requires_local_model=args.requires_local_model,
        local_model_seat_ready=args.local_model_seat_ready,
        approval_token_ref=args.approval_token_ref,
        redaction_policy_ref=args.redaction_policy_ref,
        output_policy_ref=args.output_policy_ref,
    )

    try:
        projection = build_document_extraction_preview(request)
    except DocumentExtractionPreviewError as err:
        print(f"document extraction preview failed: {err}", file=sys.stderr)
        return 1

    if args.snapshot_path:
        with open(args.snapshot_path, "w", encoding="utf-8") as handle:
            json.dump(
                projection,
                handle,
                sort_keys=True,
                indent=None if args.compact else 2,
            )
            handle.write("\n")

    json.dump(projection, sys.stdout, indent=None if args.compact else 2, sort_keys=True)
    if not args.compact:
        sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_document_extraction_preview()


if __name__ == "__main__":
    raise SystemExit(main())
