"""Tests for the Guardian-grant-enforced local SOP draft executor."""

from __future__ import annotations

import json

import pytest

from arc_bot_shell.model import LocalModelExecutionError, OllamaTrainingDraftExecutor


def valid_grant() -> dict[str, object]:
    return {
        "grant_id": "grant:test",
        "guardian_decision_id": "guardian-decision:test",
        "execution_allowed": True,
        "requires_operator_opt_in": True,
        "side_effects_allowed": False,
        "granted_capability": "local_model_preview",
        "bound_action_type": "arc.local_model_preview",
    }


def test_executor_calls_only_loopback_after_opt_in_and_bound_grant() -> None:
    observed: dict[str, object] = {}

    def transport(url: str, payload: bytes, timeout: float) -> bytes:
        observed.update(url=url, payload=json.loads(payload), timeout=timeout)
        return json.dumps(
            {"response": "1. Review the synthetic intake.\n2. Stop before submit."}
        ).encode()

    result = OllamaTrainingDraftExecutor(
        operator_opt_in=True,
        transport=transport,
    ).execute(prompt="Draft a registration SOP.", grant=valid_grant())

    assert observed["url"] == "http://127.0.0.1:11434/api/generate"
    assert observed["payload"]["model"] == "qwen2.5:7b"
    assert result["status"] == "draft_completed"
    assert result["network_scope"] == "loopback_only"
    assert result["external_side_effects"] is False


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://127.0.0.1:11434",
        "http://192.168.1.10:11434",
        "http://user:secret@127.0.0.1:11434",
        "http://127.0.0.1:11434/api/generate",
    ],
)
def test_executor_rejects_non_loopback_or_credentialed_endpoint(endpoint: str) -> None:
    with pytest.raises(LocalModelExecutionError):
        OllamaTrainingDraftExecutor(endpoint=endpoint, operator_opt_in=True)


def test_executor_refuses_missing_operator_opt_in_before_transport() -> None:
    called = False

    def transport(_url: str, _payload: bytes, _timeout: float) -> bytes:
        nonlocal called
        called = True
        return b"{}"

    with pytest.raises(LocalModelExecutionError, match="opt-in"):
        OllamaTrainingDraftExecutor(transport=transport).execute(
            prompt="Draft an SOP.", grant=valid_grant()
        )
    assert called is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("execution_allowed", False),
        ("side_effects_allowed", True),
        ("granted_capability", "document_read"),
        ("bound_action_type", "external_send"),
    ],
)
def test_executor_refuses_wrong_grant_before_transport(field: str, value: object) -> None:
    grant = valid_grant()
    grant[field] = value
    with pytest.raises(LocalModelExecutionError, match="grant"):
        OllamaTrainingDraftExecutor(
            operator_opt_in=True,
            transport=lambda *_args: (_ for _ in ()).throw(AssertionError("no call")),
        ).execute(prompt="Draft an SOP.", grant=grant)
