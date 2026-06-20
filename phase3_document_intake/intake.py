"""Phase-3 document intake metadata contract.

This module validates and classifies document intake metadata only. It never
opens files, reads document bytes, performs OCR, invokes a parser, calls a
model, writes raw content, or mutates customer systems.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any, Literal


SUPPORTED_DOCUMENT_TYPES = ("pdf", "text", "image_scan", "word_document")
SUPPORTED_PROCESSING_MODES = ("metadata_preview_only", "manual_review_only")
SUPPORTED_SENSITIVITY_CLASSES = (
    "office_internal",
    "customer_confidential",
    "regulated_preview",
)

DocumentType = Literal["pdf", "text", "image_scan", "word_document", "unknown"]
IntakeStatus = Literal["ready_for_review", "blocked"]


class DocumentIntakePreviewError(RuntimeError):
    """Raised when the intake preview would violate Phase-3 boundaries."""


@dataclass(frozen=True)
class DocumentIntakeRequest:
    """Metadata-only document intake request for one local office document."""

    document_id: str
    source_ref: str
    document_type: str = "auto"
    tenant_id: str = "single_tenant_local"
    sensitivity_class: str = "office_internal"
    intake_operator: str = "operator-local"
    allowed_processing_mode: str = "metadata_preview_only"
    upload_ref: str = "upload://arc-bot/manual-staging"


def classify_document_type(source_ref: str, declared_document_type: str = "auto") -> DocumentType:
    """Classify supported document type from metadata only."""

    declared = declared_document_type.strip().lower()
    if declared and declared != "auto":
        return _normalize_document_type(declared)

    lowered = source_ref.strip().lower()
    if lowered.endswith(".pdf"):
        return "pdf"
    if lowered.endswith(".txt") or lowered.endswith(".text"):
        return "text"
    if lowered.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
        return "image_scan"
    if lowered.endswith(".docx"):
        return "word_document"
    return "unknown"


def build_document_intake_preview(request: DocumentIntakeRequest) -> dict[str, Any]:
    """Build a metadata-only intake preview projection."""

    validation_errors = _validate_request(request)
    classified_type = classify_document_type(request.source_ref, request.document_type)
    if classified_type == "unknown":
        validation_errors.append("unsupported_or_unknown_document_type")

    status: IntakeStatus = "blocked" if validation_errors else "ready_for_review"
    projection: dict[str, Any] = {
        "artifact_id": f"arc_bot_phase3_document_intake:{request.document_id}",
        "artifact_type": "phase3_document_intake_preview",
        "phase": "phase-3",
        "projection_scope": "metadata_preview_only",
        "source_access_mode": "metadata_only_no_file_read",
        "document_id": request.document_id,
        "tenant_id": request.tenant_id,
        "source_ref": request.source_ref,
        "upload_ref": request.upload_ref,
        "declared_document_type": request.document_type,
        "classified_document_type": classified_type,
        "supported_document_types": list(SUPPORTED_DOCUMENT_TYPES),
        "sensitivity_class": request.sensitivity_class,
        "intake_operator": request.intake_operator,
        "allowed_processing_mode": request.allowed_processing_mode,
        "intake_status": status,
        "blocked_reasons": sorted(set(validation_errors)),
        "ready_for_review": status == "ready_for_review",
        "guardian_required_before_processing": True,
        "raw_content_persisted": False,
        "raw_content_included": False,
        "file_read_performed": False,
        "file_write_performed": False,
        "ocr_performed": False,
        "parser_invoked": False,
        "model_invocation_performed": False,
        "connector_action_performed": False,
        "customer_system_mutation_performed": False,
        "runtime_execution_blocked": True,
        "runtime_authority_blocked": True,
        "redacted_summary_only": True,
        "evidence_refs": _evidence_refs(request),
        "policy_refs": [
            "policy://arc-bot/document-intake-metadata-only",
            "policy://arc-bot/no-raw-content-persistence",
            "policy://arc-bot/guardian-required-before-processing",
        ],
        "runbook_refs": [
            "runbook://arc-bot/document-intake-review",
            "runbook://arc-bot/redaction-review",
        ],
        "request": asdict(request),
    }
    _assert_phase3_guardrails(projection)
    return projection


def _normalize_document_type(value: str) -> DocumentType:
    aliases = {
        "pdf": "pdf",
        "txt": "text",
        "text": "text",
        "image": "image_scan",
        "image_scan": "image_scan",
        "scan": "image_scan",
        "jpg": "image_scan",
        "jpeg": "image_scan",
        "png": "image_scan",
        "docx": "word_document",
        "word": "word_document",
        "word_document": "word_document",
    }
    return aliases.get(value, "unknown")  # type: ignore[return-value]


def _validate_request(request: DocumentIntakeRequest) -> list[str]:
    errors: list[str] = []
    required_fields = {
        "document_id": request.document_id,
        "source_ref": request.source_ref,
        "tenant_id": request.tenant_id,
        "sensitivity_class": request.sensitivity_class,
        "intake_operator": request.intake_operator,
        "allowed_processing_mode": request.allowed_processing_mode,
    }
    for field_name, value in required_fields.items():
        if not isinstance(value, str) or not value.strip():
            errors.append(f"missing_{field_name}")

    if request.allowed_processing_mode not in SUPPORTED_PROCESSING_MODES:
        errors.append("unsupported_processing_mode")
    if request.sensitivity_class not in SUPPORTED_SENSITIVITY_CLASSES:
        errors.append("unsupported_sensitivity_class")
    if request.document_type != "auto" and _normalize_document_type(request.document_type) == "unknown":
        errors.append("unsupported_declared_document_type")
    return errors


def _evidence_refs(request: DocumentIntakeRequest) -> list[dict[str, Any]]:
    return [
        {
            "ref_id": f"evidence://arc-bot/document-intake/{request.document_id}",
            "evidence_type": "document_intake_metadata",
            "required": True,
            "raw_content_persisted": False,
            "redacted_summary_only": True,
        },
        {
            "ref_id": f"evidence://arc-bot/redaction-policy/{request.document_id}",
            "evidence_type": "redaction_policy",
            "required": True,
            "raw_content_persisted": False,
            "redacted_summary_only": True,
        },
    ]


def _assert_phase3_guardrails(projection: dict[str, Any]) -> None:
    blocked_flags = (
        "raw_content_persisted",
        "raw_content_included",
        "file_read_performed",
        "file_write_performed",
        "ocr_performed",
        "parser_invoked",
        "model_invocation_performed",
        "connector_action_performed",
        "customer_system_mutation_performed",
    )
    for flag in blocked_flags:
        if projection[flag] is not False:
            raise DocumentIntakePreviewError(f"{flag} must remain false")
    if projection["runtime_execution_blocked"] is not True:
        raise DocumentIntakePreviewError("runtime_execution_blocked must stay true")
    if projection["redacted_summary_only"] is not True:
        raise DocumentIntakePreviewError("redacted_summary_only must stay true")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render Phase-3 document intake metadata preview."
    )
    parser.add_argument("--document-id", default="doc-intake-preview-001")
    parser.add_argument("--source-ref", default="upload://arc-bot/sample-intake.pdf")
    parser.add_argument("--document-type", default="auto")
    parser.add_argument("--tenant-id", default="single_tenant_local")
    parser.add_argument("--sensitivity-class", default="office_internal")
    parser.add_argument("--intake-operator", default="operator-local")
    parser.add_argument("--allowed-processing-mode", default="metadata_preview_only")
    parser.add_argument("--upload-ref", default="upload://arc-bot/manual-staging")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--snapshot-path")
    return parser


def run_document_intake_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    request = DocumentIntakeRequest(
        document_id=args.document_id,
        source_ref=args.source_ref,
        document_type=args.document_type,
        tenant_id=args.tenant_id,
        sensitivity_class=args.sensitivity_class,
        intake_operator=args.intake_operator,
        allowed_processing_mode=args.allowed_processing_mode,
        upload_ref=args.upload_ref,
    )

    try:
        projection = build_document_intake_preview(request)
    except DocumentIntakePreviewError as err:
        print(f"document intake preview failed: {err}", file=sys.stderr)
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
    return run_document_intake_preview()


if __name__ == "__main__":
    raise SystemExit(main())
