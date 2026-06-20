"""Tests for Phase-4 guarded document extraction preview contract."""

from __future__ import annotations

import inspect
import io
import json
from pathlib import Path
from unittest.mock import patch

from phase4_document_extraction import extraction as extraction_module
from phase4_document_extraction import (
    DocumentExtractionRequest,
    build_document_extraction_preview,
    run_document_extraction_preview,
)


class RecordingPreviewProvider:
    def __init__(self) -> None:
        self.called = False

    def build_model_preview(
        self,
        request: DocumentExtractionRequest,
        deterministic_preview: dict,
    ) -> dict:
        self.called = True
        return {
            "provider_kind": "recording_preview_provider",
            "provider_interface": "injectable_preview_provider",
            "provider_called_for_projection": True,
            "runtime_execution_blocked": True,
            "runtime_authority_blocked": True,
            "local_model_execution_blocked": True,
            "model_invocation_performed": False,
            "network_egress_performed": False,
            "provider_sdk_used": False,
            "blocked_reason": "test_provider_projection_only",
            "missing_gate_data": [],
            "deterministic_preview_ref": deterministic_preview["artifact_id"],
        }


def test_document_extraction_preview_ready_for_deterministic_metadata() -> None:
    projection = build_document_extraction_preview(
        DocumentExtractionRequest(
            extraction_id="extract-001",
            document_id="doc-001",
            source_ref="upload://arc-bot/claims/customer-claim.pdf",
            sensitivity_class="customer_confidential",
            operator_supplied_category="insurance_claim_packet",
        )
    )

    assert projection["artifact_type"] == "phase4_document_extraction_preview"
    assert projection["phase"] == "phase-4"
    assert projection["extraction_status"] == "ready_for_review"
    assert projection["ready_for_review"] is True
    assert projection["classified_document_type"] == "pdf"
    assert projection["filename_metadata"]["display_name"] == "customer-claim.pdf"
    assert projection["filename_metadata"]["extension"] == "pdf"
    assert projection["filename_metadata"]["source_ref_scheme"] == "upload"
    assert projection["page_count_placeholder"] == "not_calculated_no_file_read"
    assert projection["checksum_placeholder"] == "not_calculated_no_file_read"
    assert projection["operator_supplied_document_category"] == "insurance_claim_packet"
    assert projection["local_model_required"] is False
    assert projection["local_model_preview"]["provider_called_for_projection"] is False
    assert projection["raw_content_persisted"] is False
    assert projection["file_read_performed"] is False
    assert projection["parser_invoked"] is False
    assert projection["ocr_performed"] is False
    assert projection["model_invocation_performed"] is False
    assert projection["network_egress_performed"] is False
    assert projection["connector_action_performed"] is False
    assert projection["customer_system_mutation_performed"] is False
    assert projection["runtime_execution_blocked"] is True


def test_document_extraction_preview_requires_approval_and_evidence_for_model_path() -> None:
    projection = build_document_extraction_preview(
        DocumentExtractionRequest(
            extraction_id="extract-model-missing",
            document_id="doc-model-missing",
            source_ref="upload://arc-bot/claim.pdf",
            operator_supplied_category="insurance_claim_packet",
            requires_local_model=True,
        )
    )

    assert projection["extraction_status"] == "approval_required"
    assert projection["approval_required"] is True
    assert projection["guardian_decision"]["decision"] == "approval_required"
    assert projection["guardian_decision"]["reason_code"] == (
        "local_model_preview_requires_guardian_approval"
    )
    assert projection["approval_request"]["grants_runtime_execution"] is False
    assert projection["approval_request"]["grants_local_model_execution"] is False
    assert projection["local_model_gate"]["missing_gate_data"] == [
        "local_model_seat_ready",
        "approval_token_ref",
        "redaction_policy_ref",
        "output_policy_ref",
    ]
    assert projection["local_model_preview"]["model_invocation_performed"] is False
    assert projection["local_model_preview"]["runtime_execution_blocked"] is True


def test_document_extraction_preview_still_blocks_runtime_when_gate_data_is_present() -> None:
    provider = RecordingPreviewProvider()
    projection = build_document_extraction_preview(
        DocumentExtractionRequest(
            extraction_id="extract-model-gated",
            document_id="doc-model-gated",
            source_ref="upload://arc-bot/claim.pdf",
            operator_supplied_category="insurance_claim_packet",
            requires_local_model=True,
            local_model_seat_ready=True,
            approval_token_ref="approval-token://arc-bot/extract-model-gated",
            redaction_policy_ref="evidence://arc-bot/redaction-policy/doc-model-gated",
            output_policy_ref="evidence://arc-bot/output-policy/doc-model-gated",
        ),
        provider=provider,
    )

    assert provider.called is True
    assert projection["extraction_status"] == "blocked_runtime"
    assert projection["local_model_gate"]["missing_gate_data"] == []
    assert projection["local_model_gate"]["all_gate_data_present"] is True
    assert projection["local_model_gate"]["phase4_execution_authority"] == (
        "blocked_until_phase8_execution_gate"
    )
    assert projection["local_model_preview"]["provider_kind"] == (
        "recording_preview_provider"
    )
    assert projection["local_model_preview"]["model_invocation_performed"] is False
    assert projection["model_invocation_performed"] is False
    assert projection["runtime_execution_blocked"] is True
    assert projection["local_model_execution_blocked"] is True


def test_document_extraction_preview_blocks_unsupported_or_missing_intake_metadata() -> None:
    projection = build_document_extraction_preview(
        DocumentExtractionRequest(
            extraction_id="extract-bad",
            document_id="",
            source_ref="upload://arc-bot/archive.exe",
            operator_supplied_category="insurance_claim_packet",
        )
    )

    assert projection["extraction_status"] == "blocked"
    assert "missing_document_id" in projection["blocked_reasons"]
    assert (
        "intake_unsupported_or_unknown_document_type"
        in projection["blocked_reasons"]
    )
    assert projection["file_read_performed"] is False
    assert projection["model_invocation_performed"] is False


def test_document_extraction_preview_emits_spine_and_evidence_refs() -> None:
    projection = build_document_extraction_preview(
        DocumentExtractionRequest(
            extraction_id="extract-evidence",
            document_id="doc-evidence",
            source_ref="upload://arc-bot/customer-note.txt",
            operator_supplied_category="customer_service_note",
        )
    )

    evidence_types = {item["evidence_type"] for item in projection["evidence_refs"]}
    assert "local_model_seat_readiness" in evidence_types
    assert "document_intake_contract" in evidence_types
    assert "guardian_decision" in evidence_types
    assert projection["spine_event"]["event_type"] == (
        "document_extraction_preview_projected"
    )
    assert projection["spine_event"]["persistence_mode"] == "projection_only"
    assert projection["spine_event"]["guardian_decision_result"] == (
        projection["guardian_decision"]["decision"]
    )


def test_document_extraction_preview_cli_can_export_projection(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "document_extraction_preview.json"
    output = io.StringIO()

    with patch("sys.stdout", output):
        status = run_document_extraction_preview(
            [
                "--extraction-id=extract-cli",
                "--document-id=doc-cli",
                "--source-ref=upload://arc-bot/scan.jpg",
                "--operator-category=insurance_claim_packet",
                "--compact",
                f"--snapshot-path={snapshot_path}",
            ]
        )

    assert status == 0
    cli_payload = json.loads(output.getvalue())
    file_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert cli_payload == file_payload
    assert cli_payload["classified_document_type"] == "image_scan"
    assert cli_payload["local_model_required"] is False
    assert cli_payload["file_read_performed"] is False
    assert cli_payload["model_invocation_performed"] is False


def test_document_extraction_module_has_no_file_read_parser_model_or_network_paths() -> None:
    source = inspect.getsource(extraction_module)

    forbidden_terms = [
        "read_text",
        "read_bytes",
        "import socket",
        "import subprocess",
        "import requests",
        "import urllib",
        "pytesseract",
        "PdfReader",
        "python-docx",
        "ollama",
        "generate(",
        "chat(",
    ]
    for term in forbidden_terms:
        assert term not in source
