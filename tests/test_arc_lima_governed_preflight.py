"""Arc-to-LIMA governed dry-run preflight tests."""

from __future__ import annotations

from pathlib import Path

from arc_guardian_spine import ArcActionRequest
from arc_guardian_spine.lima_preflight import (
    ArcLimaGovernedPreflightResult,
    call_lima_governed_preflight_for_arc_action,
    map_arc_action_category,
    normalize_for_lima,
    record_lima_governed_preflight_projection,
)


LIMA_REPO = Path(__file__).resolve().parents[2] / "LIMA-AI-OS"


def _arc_request(action_id: str, action_kind: str) -> ArcActionRequest:
    return ArcActionRequest(
        action_id=action_id,
        operator_id="operator-test",
        worker_id="arc-worker-test-001",
        tenant_id="tenant-test",
        payload_summary=f"Arc dry-run preflight for {action_kind}",
        action_kind=action_kind,
        task_ref="task://arc/test/preflight",
        evidence_refs=("evidence://arc/test/preflight",),
    )


def test_arc_safe_read_status_request_gets_allowed_dry_run() -> None:
    result = call_lima_governed_preflight_for_arc_action(
        _arc_request("arc-read-001", "status_read"),
        lima_repo_path=LIMA_REPO,
    )

    assert result.lima_available is True
    assert result.decision.status == "allowed_dry_run"
    assert result.decision.allowed is True
    assert result.lima_request["request_id"] == "arc-read-001"
    assert result.lima_request["actor_id"] == "operator-test"
    assert result.lima_request["trust_context"]["tenant_id"] == "tenant-test"
    assert result.lima_request["trust_context"]["worker_id"] == "arc-worker-test-001"
    assert result.lima_request["normalized_request"] == "Arc dry-run preflight for status_read"
    assert result.lima_request["requested_action"] == "status_read"
    assert result.lima_request["action_category"] == "read"
    assert result.lima_request["tool_name"] == "arc_status_preview"
    assert result.lima_request["evidence_refs"] == ("evidence://arc/test/preflight",)
    _assert_no_execution_allowed(result)


def test_arc_external_write_send_request_gets_confirm_required() -> None:
    result = call_lima_governed_preflight_for_arc_action(
        _arc_request("arc-send-001", "send_email"),
        lima_repo_path=LIMA_REPO,
    )

    assert result.decision.status == "confirm_required"
    assert result.decision.allowed is False
    assert result.decision.requires_approval is True
    assert result.lima_request["action_category"] == "external_write"
    assert result.lima_request["tool_name"] == "send_email"
    _assert_no_execution_allowed(result)


def test_arc_shell_tool_execution_request_gets_denied() -> None:
    result = call_lima_governed_preflight_for_arc_action(
        _arc_request("arc-shell-001", "shell_command_execute"),
        lima_repo_path=LIMA_REPO,
    )

    assert result.decision.status == "denied"
    assert result.decision.allowed is False
    assert result.decision.requires_approval is False
    assert result.lima_request["action_category"] == "shell"
    assert result.lima_request["tool_name"] == "terminal_send"
    _assert_no_execution_allowed(result)


def test_arc_file_mutation_request_never_allows_execution() -> None:
    result = call_lima_governed_preflight_for_arc_action(
        _arc_request("arc-file-001", "file_write"),
        lima_repo_path=LIMA_REPO,
    )

    assert result.decision.status in {"confirm_required", "denied"}
    assert result.decision.allowed is False
    assert result.lima_request["action_category"] == "file_mutation"
    _assert_no_execution_allowed(result)


def test_unknown_arc_action_fails_closed_through_lima() -> None:
    result = call_lima_governed_preflight_for_arc_action(
        _arc_request("arc-unknown-001", "unmapped_future_action"),
        lima_repo_path=LIMA_REPO,
    )

    assert result.decision.status == "denied"
    assert "unknown_tool_or_action" in tuple(result.decision.reason_codes)
    assert result.lima_request["action_category"] == "unknown"
    _assert_no_execution_allowed(result)


def test_malformed_arc_request_fails_closed() -> None:
    result = call_lima_governed_preflight_for_arc_action(
        ArcActionRequest(
            action_id="",
            operator_id="operator-test",
            worker_id="arc-worker-test-001",
            tenant_id="tenant-test",
            payload_summary="missing action id",
            action_kind="status_read",
        ),
        lima_repo_path=LIMA_REPO,
    )

    assert result.lima_available is False
    assert result.decision.status == "denied"
    assert result.decision.allowed is False
    assert "malformed_arc_action_request" in result.decision.reason_codes
    _assert_no_execution_allowed(result)


def test_lima_unavailable_path_fails_closed() -> None:
    def unavailable_runner(_: dict[str, object]) -> object:
        raise RuntimeError("LIMA unavailable for test")

    result = call_lima_governed_preflight_for_arc_action(
        _arc_request("arc-lima-unavailable-001", "status_read"),
        lima_runner=unavailable_runner,
    )

    assert result.lima_available is False
    assert result.decision.status == "denied"
    assert result.decision.allowed is False
    assert "lima_unavailable" in result.decision.reason_codes
    _assert_no_execution_allowed(result)


def test_normalization_maps_required_arc_fields_to_lima_request() -> None:
    request = _arc_request("arc-map-001", "calendar_create")
    lima_request = normalize_for_lima(request)

    assert lima_request == {
        "request_id": "arc-map-001",
        "consumer": "arc_bot_shell",
        "surface": "arc_guardian_spine.lima_preflight",
        "actor_id": "operator-test",
        "normalized_request": "Arc dry-run preflight for calendar_create",
        "requested_action": "calendar_create",
        "action_category": "external_write",
        "tool_name": "calendar_create_event",
        "tool_args": {
            "arc_action_id": "arc-map-001",
            "worker_id": "arc-worker-test-001",
            "tenant_id": "tenant-test",
            "task_ref": "task://arc/test/preflight",
            "arc_action_kind": "calendar_create",
        },
        "trust_context": {
            "tenant_id": "tenant-test",
            "worker_id": "arc-worker-test-001",
            "task_ref": "task://arc/test/preflight",
            "source_shell": "arc_bot_shell",
            "dry_run_only": True,
            "execution_requested": False,
            "side_effects_requested": False,
        },
        "evidence_refs": ("evidence://arc/test/preflight",),
    }


def test_action_category_mapper_uses_lima_week1_categories() -> None:
    assert map_arc_action_category("show_status") == "read"
    assert map_arc_action_category("draft_summary") == "drafting"
    assert map_arc_action_category("plan_next_step") == "planning"
    assert map_arc_action_category("send_slack_message") == "external_write"
    assert map_arc_action_category("terminal_command") == "shell"
    assert map_arc_action_category("file_delete") == "file_mutation"
    assert map_arc_action_category("provider_model_route") == "model_call"
    assert map_arc_action_category("robot_physical_action") == "physical_world"
    assert map_arc_action_category("future_unknown") == "unknown"


def test_projection_record_is_sanitized_and_non_executing() -> None:
    result = call_lima_governed_preflight_for_arc_action(
        _arc_request("arc-record-001", "status_read"),
        lima_repo_path=LIMA_REPO,
    )

    record = record_lima_governed_preflight_projection(result)

    assert record["record_type"] == "arc_lima_governed_preflight_projection_record"
    assert record["projection_scope"] == "in_memory_evidence_only"
    assert record["persistence_mode"] == "projection_only"
    assert record["arc_action_id"] == "arc-record-001"
    assert record["dry_run"] is True
    assert record["execution_allowed"] is False
    assert record["side_effects_allowed"] is False
    assert record["tool_executed"] is False
    assert record["connector_invoked"] is False


def _assert_no_execution_allowed(result: ArcLimaGovernedPreflightResult) -> None:
    assert result.decision.executable is False
    assert result.decision.execution_allowed is False
    assert result.decision.side_effects_allowed is False
    assert result.response["executable"] is False
    assert result.response["execution_allowed"] is False
    assert result.response["side_effects_allowed"] is False
    assert result.response["tool_executed"] is False
    assert result.response["file_mutation_executed"] is False
    assert result.response["network_action_executed"] is False
    assert result.response["connector_invoked"] is False
