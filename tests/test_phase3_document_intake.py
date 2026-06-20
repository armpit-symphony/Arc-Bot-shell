"""Tests for Phase-3 document intake metadata contract."""

from __future__ import annotations

import inspect
import io
import json
from pathlib import Path
from unittest.mock import patch

from phase0_runtime_ui_scaffold.basic_console import build_basic_guardian_console_projection
from phase3_document_intake import intake as intake_module
from phase3_document_intake import (
    SUPPORTED_DOCUMENT_TYPES,
    DocumentIntakeRequest,
    build_document_intake_preview,
    classify_document_type,
    run_document_intake_preview,
)


def test_document_type_classification_uses_metadata_only() -> None:
    assert classify_document_type("upload://arc/doc.pdf") == "pdf"
    assert classify_document_type("upload://arc/notes.txt") == "text"
    assert classify_document_type("upload://arc/scan.jpeg") == "image_scan"
    assert classify_document_type("upload://arc/letter.docx") == "word_document"
    assert classify_document_type("upload://arc/unknown.bin") == "unknown"
    assert classify_document_type("upload://arc/unknown.bin", "pdf") == "pdf"


def test_document_intake_preview_ready_for_supported_pdf_metadata() -> None:
    projection = build_document_intake_preview(
        DocumentIntakeRequest(
            document_id="doc-001",
            source_ref="upload://arc-bot/customer-intake.pdf",
            sensitivity_class="customer_confidential",
        )
    )

    assert projection["artifact_type"] == "phase3_document_intake_preview"
    assert projection["phase"] == "phase-3"
    assert projection["classified_document_type"] == "pdf"
    assert projection["supported_document_types"] == list(SUPPORTED_DOCUMENT_TYPES)
    assert projection["intake_status"] == "ready_for_review"
    assert projection["ready_for_review"] is True
    assert projection["blocked_reasons"] == []
    assert projection["guardian_required_before_processing"] is True
    assert projection["raw_content_persisted"] is False
    assert projection["raw_content_included"] is False
    assert projection["file_read_performed"] is False
    assert projection["file_write_performed"] is False
    assert projection["ocr_performed"] is False
    assert projection["parser_invoked"] is False
    assert projection["model_invocation_performed"] is False
    assert projection["connector_action_performed"] is False
    assert projection["customer_system_mutation_performed"] is False
    assert projection["runtime_execution_blocked"] is True
    assert projection["redacted_summary_only"] is True
    assert projection["evidence_refs"]


def test_document_intake_preview_supports_mvp_document_types() -> None:
    cases = {
        "claim.pdf": "pdf",
        "notes.txt": "text",
        "scan.png": "image_scan",
        "policy.docx": "word_document",
    }
    for filename, expected_type in cases.items():
        projection = build_document_intake_preview(
            DocumentIntakeRequest(
                document_id=f"doc-{expected_type}",
                source_ref=f"upload://arc-bot/{filename}",
            )
        )
        assert projection["classified_document_type"] == expected_type
        assert projection["intake_status"] == "ready_for_review"


def test_document_intake_preview_blocks_missing_or_unsupported_metadata() -> None:
    unsupported = build_document_intake_preview(
        DocumentIntakeRequest(
            document_id="doc-bad",
            source_ref="upload://arc-bot/archive.exe",
        )
    )
    assert unsupported["intake_status"] == "blocked"
    assert "unsupported_or_unknown_document_type" in unsupported["blocked_reasons"]

    missing = build_document_intake_preview(
        DocumentIntakeRequest(
            document_id="",
            source_ref="",
            sensitivity_class="secret",
            allowed_processing_mode="full_parse",
        )
    )
    assert missing["intake_status"] == "blocked"
    assert "missing_document_id" in missing["blocked_reasons"]
    assert "missing_source_ref" in missing["blocked_reasons"]
    assert "unsupported_sensitivity_class" in missing["blocked_reasons"]
    assert "unsupported_processing_mode" in missing["blocked_reasons"]


def test_document_intake_preview_cli_can_export_metadata_only(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "document_intake_preview.json"
    output = io.StringIO()

    with patch("sys.stdout", output):
        status = run_document_intake_preview(
            [
                "--document-id=doc-cli",
                "--source-ref=upload://arc-bot/scan.jpg",
                "--sensitivity-class=regulated_preview",
                "--compact",
                f"--snapshot-path={snapshot_path}",
            ]
        )

    assert status == 0
    cli_payload = json.loads(output.getvalue())
    file_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert cli_payload == file_payload
    assert cli_payload["classified_document_type"] == "image_scan"
    assert cli_payload["file_read_performed"] is False
    assert cli_payload["raw_content_persisted"] is False


def test_document_intake_module_has_no_file_read_parser_model_or_network_paths() -> None:
    source = inspect.getsource(intake_module)

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


def test_basic_console_embeds_document_intake_preview() -> None:
    projection = build_basic_guardian_console_projection()
    intake = projection["file_upload"]["document_intake_preview"]

    assert intake["artifact_type"] == "phase3_document_intake_preview"
    assert intake["classified_document_type"] == "pdf"
    assert intake["intake_status"] == "ready_for_review"
    assert intake["raw_content_persisted"] is False
    assert intake["file_read_performed"] is False
    assert intake["model_invocation_performed"] is False
