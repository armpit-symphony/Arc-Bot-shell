"""Guardian facade tests for Arc Harness Shell v0.1."""

from __future__ import annotations

from arc_bot_shell.contracts import ArcActionRequest
from arc_bot_shell.guardian import GuardianFacade, GuardianSuiteAdapter


def _request(**overrides: object) -> ArcActionRequest:
    payload = {
        "action_id": "arc-action-test-001",
        "task_ref": "task://tests/001",
        "action_name": "arc.preview_operator_response",
        "summary": "Preview a safe operator response.",
        "preview_only": True,
        "requested_capabilities": [],
        "payload": {},
    }
    payload.update(overrides)
    return ArcActionRequest.from_dict(payload)


def test_guardian_facade_allows_preview_only_safe_actions_when_suite_is_missing() -> None:
    facade = GuardianFacade(
        primary=GuardianSuiteAdapter(import_module=lambda name: (_ for _ in ()).throw(ImportError(name)))
    )
    decision = facade.evaluate(_request())

    assert decision.status == "allowed_preview_only"
    assert decision.evaluator == "fail_closed_guardian"


def test_guardian_facade_blocks_external_send() -> None:
    facade = GuardianFacade(
        primary=GuardianSuiteAdapter(import_module=lambda name: (_ for _ in ()).throw(ImportError(name)))
    )
    decision = facade.evaluate(_request(requested_capabilities=["external_send"]))

    assert decision.status == "blocked"
    assert decision.block_category == "external_send"


def test_missing_guardian_suite_fails_closed_for_consequential_requests() -> None:
    facade = GuardianFacade(
        primary=GuardianSuiteAdapter(import_module=lambda name: (_ for _ in ()).throw(ImportError(name)))
    )
    decision = facade.evaluate(
        _request(
            action_id="arc-action-test-002",
            requested_capabilities=["file_write"],
        )
    )

    assert decision.status == "blocked"
    assert decision.evaluator == "fail_closed_guardian"
    assert decision.block_category == "file_write"


def test_guardian_facade_can_require_operator_approval() -> None:
    facade = GuardianFacade(
        primary=GuardianSuiteAdapter(import_module=lambda name: (_ for _ in ()).throw(ImportError(name)))
    )
    decision = facade.evaluate(
        _request(
            action_id="arc-action-test-003",
            preview_only=False,
        )
    )

    assert decision.status == "requires_operator_approval"
