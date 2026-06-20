"""Tests for Phase-5 office workflow template contracts."""

from __future__ import annotations

import inspect
import io
import json
from pathlib import Path
from unittest.mock import patch

from phase0_runtime_ui_scaffold.basic_console import build_basic_guardian_console_projection
from phase5_office_workflows import workflows as workflows_module
from phase5_office_workflows import (
    PHASE5_APPROVAL_REQUIRED_ACTIONS,
    PHASE5_ROLE_PROFILE_IDS,
    PHASE5_WORKFLOW_IDS,
    OfficeWorkflowRequest,
    build_office_workflow_preview,
    build_office_workflow_template_catalog,
    run_office_workflow_templates_preview,
)


FIXTURE_PATH = Path("tests/fixtures/arc_bot_phase5_office_workflow_templates.json")
SCHEMA_PATH = Path("docs/contracts/schemas/arc_bot_phase5_office_workflow_template.schema.json")


def test_phase5_catalog_contains_required_workflows_roles_and_blocked_matrix() -> None:
    catalog = build_office_workflow_template_catalog()

    assert catalog["artifact_type"] == "phase5_office_workflow_template_catalog"
    assert catalog["phase"] == "phase-5"
    assert tuple(catalog["workflow_ids"]) == PHASE5_WORKFLOW_IDS
    assert tuple(catalog["role_profile_ids"]) == PHASE5_ROLE_PROFILE_IDS
    assert tuple(catalog["approval_required_actions"]) == PHASE5_APPROVAL_REQUIRED_ACTIONS
    assert len(catalog["workflow_templates"]) == 6
    assert len(catalog["role_profiles"]) == 4

    for workflow in catalog["workflow_templates"]:
        assert workflow["schema_ref"] == "schema://arc-bot/phase5-office-workflow-template"
        assert workflow["fixture_ref"] == (
            "fixture://tests/fixtures/arc_bot_phase5_office_workflow_templates.json"
        )
        assert workflow["output_mode"] == "draft_preview_only"
        assert workflow["requires_operator_review"] is True
        assert workflow["finalization_requires_approval"] is True
        assert workflow["local_model_required_for_template"] is False
        assert workflow["raw_content_persisted"] is False
        assert workflow["file_read_performed"] is False
        assert workflow["model_invocation_performed"] is False
        assert workflow["customer_system_mutation_performed"] is False
        _assert_blocked_matrix(workflow["blocked_action_matrix"])


def test_phase5_fixture_and_schema_cover_each_workflow() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    catalog = build_office_workflow_template_catalog()

    assert fixture["schema_ref"] == schema["$id"]
    assert tuple(fixture["workflow_ids"]) == PHASE5_WORKFLOW_IDS
    assert tuple(fixture["role_profile_ids"]) == PHASE5_ROLE_PROFILE_IDS
    assert tuple(fixture["approval_required_actions"]) == PHASE5_APPROVAL_REQUIRED_ACTIONS
    assert schema["properties"]["workflow_id"]["enum"] == list(PHASE5_WORKFLOW_IDS)

    fixture_by_id = {
        workflow["workflow_id"]: workflow for workflow in fixture["workflow_templates"]
    }
    for workflow in catalog["workflow_templates"]:
        fixture_workflow = fixture_by_id[workflow["workflow_id"]]
        assert fixture_workflow["schema_ref"] == workflow["schema_ref"]
        assert fixture_workflow["fixture_ref"] == workflow["fixture_ref"]
        assert fixture_workflow["output_mode"] == workflow["output_mode"]
        assert fixture_workflow["draft_sections"] == workflow["draft_sections"]


def test_phase5_workflow_preview_is_draft_only_and_emits_evidence() -> None:
    projection = build_office_workflow_preview(
        OfficeWorkflowRequest(
            workflow_id="insurance_claim_packet_triage",
            document_id="doc-claim-001",
            source_ref="upload://arc-bot/claim.pdf",
            role_profile_id="document_processing_bot",
            sensitivity_class="customer_confidential",
        )
    )

    assert projection["artifact_type"] == "phase5_office_workflow_preview"
    assert projection["preview_status"] == "draft_preview_ready"
    assert projection["ready_for_operator_review"] is True
    assert projection["draft_output"]["output_mode"] == "draft_preview_only"
    assert projection["draft_output"]["output_status"] == (
        "draft_pending_operator_review"
    )
    assert projection["guardian_decision"]["decision"] == "allow_preview"
    assert projection["approval_request"] is None
    assert projection["spine_event"]["event_type"] == (
        "office_workflow_template_preview_projected"
    )
    assert projection["spine_event"]["persistence_mode"] == "projection_only"
    assert projection["evidence_refs"]
    assert projection["raw_content_persisted"] is False
    assert projection["external_message_send_performed"] is False
    assert projection["customer_system_mutation_performed"] is False
    assert projection["connector_action_performed"] is False
    _assert_blocked_matrix(projection["blocked_action_matrix"])


def test_phase5_workflow_preview_blocks_role_mismatch_and_unknown_workflow() -> None:
    role_mismatch = build_office_workflow_preview(
        OfficeWorkflowRequest(
            workflow_id="customer_service_draft_reply",
            role_profile_id="billing_intake_assistant",
        )
    )
    assert role_mismatch["preview_status"] == "blocked"
    assert "workflow_not_allowed_for_role_profile" in role_mismatch["blocked_reasons"]
    assert role_mismatch["customer_system_mutation_performed"] is False

    unsupported = build_office_workflow_preview(
        OfficeWorkflowRequest(workflow_id="unsupported_workflow")
    )
    assert unsupported["preview_status"] == "blocked"
    assert "unsupported_workflow_id" in unsupported["blocked_reasons"]
    assert unsupported["runtime_execution_blocked"] is True


def test_phase5_roles_cannot_mutate_or_send() -> None:
    catalog = build_office_workflow_template_catalog()

    for role in catalog["role_profiles"]:
        assert role["guardian_required"] is True
        assert role["output_mode"] == "draft_preview_only"
        assert role["cannot_send_external_messages"] is True
        assert role["cannot_update_customer_records"] is True
        assert role["cannot_submit_forms"] is True
        assert role["cannot_write_connectors"] is True
        assert role["runtime_execution_blocked"] is True
        _assert_blocked_matrix(role["blocked_action_matrix"])


def test_phase5_cli_exports_catalog_and_selected_workflow(tmp_path: Path) -> None:
    catalog_snapshot_path = tmp_path / "phase5_catalog.json"
    catalog_output = io.StringIO()
    with patch("sys.stdout", catalog_output):
        status = run_office_workflow_templates_preview(
            ["--compact", f"--snapshot-path={catalog_snapshot_path}"]
        )

    assert status == 0
    catalog_payload = json.loads(catalog_output.getvalue())
    assert catalog_payload == json.loads(catalog_snapshot_path.read_text(encoding="utf-8"))
    assert tuple(catalog_payload["workflow_ids"]) == PHASE5_WORKFLOW_IDS

    preview_output = io.StringIO()
    with patch("sys.stdout", preview_output):
        status = run_office_workflow_templates_preview(
            [
                "--workflow-id=missing_information_checklist",
                "--role-profile-id=compliance_review_assistant",
                "--compact",
            ]
        )

    assert status == 0
    preview_payload = json.loads(preview_output.getvalue())
    assert preview_payload["workflow_id"] == "missing_information_checklist"
    assert preview_payload["preview_status"] == "draft_preview_ready"
    assert preview_payload["model_invocation_performed"] is False


def test_basic_console_embeds_phase5_workflow_catalog() -> None:
    projection = build_basic_guardian_console_projection()
    workflows = projection["office_workflows"]

    assert workflows["guardian_required"] is True
    assert workflows["runtime_execution_blocked"] is True
    catalog = workflows["workflow_template_catalog"]
    assert catalog["artifact_type"] == "phase5_office_workflow_template_catalog"
    assert tuple(catalog["workflow_ids"]) == PHASE5_WORKFLOW_IDS
    assert catalog["customer_system_mutation_performed"] is False


def test_phase5_module_has_no_file_read_model_connector_or_network_paths() -> None:
    source = inspect.getsource(workflows_module)

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


def _assert_blocked_matrix(matrix: dict) -> None:
    assert set(matrix) == set(PHASE5_APPROVAL_REQUIRED_ACTIONS)
    for action in PHASE5_APPROVAL_REQUIRED_ACTIONS:
        entry = matrix[action]
        assert entry["status"] == "approval_required_before_execution"
        assert entry["guardian_required"] is True
        assert entry["runtime_execution_blocked"] is True
        assert entry["grants_execution"] is False
        assert entry["allowed_in_phase5"] is False
