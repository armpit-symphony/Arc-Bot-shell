"""Arc v0.10 Guardian -> LIMA -> loopback Ollama contract tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from arc_bot_shell.contracts import ArcActionRequest, GuardianDecision
from arc_bot_shell.harness import run_task_packet
from arc_bot_shell.lima import (
    LOOPBACK_OLLAMA_EXECUTOR_KIND,
    LOOPBACK_OLLAMA_EXECUTOR_NAME,
    LimaRuntimeAdapter,
    OllamaExecutorValidationError,
    RETIRED_OLLAMA_EXECUTION_DISABLED,
    normalize_loopback_ollama_url,
)
from arc_bot_shell.state import JsonlStateStore
import arc_bot_shell.lima as lima_package
import arc_bot_shell.lima.ollama_executor as ollama_executor_module


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_PREVIEW = REPO_ROOT / "samples" / "tasks" / "local_model_preview.json"
EXTERNAL_EMAIL = REPO_ROOT / "samples" / "tasks" / "external_email_send.json"
DECISION_ID = "guardian-decision:test-v0-10-loopback-ollama"
RETIRED_DISABLED = "retired lima.harness execution surface is disabled"
ENDPOINT = "http://127.0.0.1:11434"
MODEL = "qwen2.5:7b"


def _request() -> ArcActionRequest:
    return ArcActionRequest.from_dict(
        json.loads(LOCAL_PREVIEW.read_text(encoding="utf-8"))
    )


def _decision(**overrides: Any) -> GuardianDecision:
    values: dict[str, Any] = {
        "decision_id": DECISION_ID,
        "action_id": _request().action_id,
        "status": "allowed_preview_only",
        "evaluator": "guardian_core",
        "reason": "real-shaped Guardian local preview allow",
        "allowed": True,
        "requires_approval": False,
        "requested_action": "arc.local_model_preview",
        "metadata": {
            "guardian_status": "allow",
            "guardian_adapter": "guardian_core",
            "guardian_contract_reference": (
                "guardian-core-v1.1-local-model-preview-policy"
            ),
        },
    }
    values.update(overrides)
    return GuardianDecision(**values)


def _runtime_input(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "request_id": "arc-action:test-v0-10",
        "runtime_consumer": "arc_bot_shell",
        "requested_action": "arc.local_model_preview",
        "guardian_decision": {
            "decision_id": DECISION_ID,
            "status": "allow",
            "allowed": True,
            "requires_approval": False,
        },
        "guardian_decision_id": DECISION_ID,
        "executor_kind": LOOPBACK_OLLAMA_EXECUTOR_KIND,
        "executor_ref": LOOPBACK_OLLAMA_EXECUTOR_NAME,
        "endpoint": ENDPOINT,
        "model": MODEL,
        "network_scope": "loopback_only",
        "credentials_used": False,
        "external_side_effects": False,
        "normalized_request": {
            "action_id": "arc-action:test-v0-10",
            "task_ref": "task://tests/v0-10",
            "summary": "Prepare a safe local draft.",
            "payload_summary": "Draft only; do not send anything.",
        },
    }
    payload.update(overrides)
    return payload


class AllowedGuardianFacade:
    def evaluate(self, request: ArcActionRequest, **_kwargs: object) -> GuardianDecision:
        return _decision(action_id=request.action_id)


class DeniedGuardianFacade:
    def evaluate(self, request: ArcActionRequest, **_kwargs: object) -> GuardianDecision:
        return _decision(
            action_id=request.action_id,
            status="blocked",
            allowed=False,
            requires_approval=False,
            requested_action=request.action_name,
            reason="Guardian denied external action",
            metadata={"guardian_status": "deny"},
        )


class ApprovalGuardianFacade:
    def evaluate(self, request: ArcActionRequest, **_kwargs: object) -> GuardianDecision:
        return _decision(
            action_id=request.action_id,
            status="requires_operator_approval",
            allowed=False,
            requires_approval=True,
            reason="Guardian requires operator approval",
            metadata={"guardian_status": "requires_approval"},
        )


class ExplodingRuntime:
    adapter_name = "exploding"

    def invoke(self, _request: object, _decision: object) -> object:
        raise AssertionError("LIMA/Ollama must not be called")


def test_retired_direct_ollama_executor_is_not_public() -> None:
    assert not hasattr(lima_package, "execute_loopback_ollama")


def test_retired_direct_ollama_executor_fails_before_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    network_calls = 0

    def unexpected_network(*_args: object, **_kwargs: object) -> object:
        nonlocal network_calls
        network_calls += 1
        raise AssertionError("network must not be called")

    monkeypatch.setattr("urllib.request.urlopen", unexpected_network)
    assert not hasattr(ollama_executor_module, "_open_ollama_request")
    with pytest.raises(
        OllamaExecutorValidationError,
        match=RETIRED_OLLAMA_EXECUTION_DISABLED,
    ):
        ollama_executor_module.execute_loopback_ollama(_runtime_input())
    assert network_calls == 0


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("http://127.0.0.1:11434", "http://127.0.0.1:11434"),
        ("http://localhost:11434", "http://localhost:11434"),
    ),
)
def test_valid_loopback_endpoint_is_accepted(value: str, expected: str) -> None:
    assert normalize_loopback_ollama_url(value) == expected


def _realistic_executor(calls: list[Mapping[str, Any]]):
    def executor(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        calls.append(payload)
        return {
            "provider": "ollama",
            "model": MODEL,
            "output_text": "Deterministic LIMA Ollama operator preview.",
            "endpoint": ENDPOINT,
            "network_called": True,
            "network_scope": "loopback_only",
            "ollama_called": True,
            "credentials_used": False,
            "external_side_effects": False,
            "duration_ms": 9,
            "status": "completed",
            "error_category": None,
            "error_message": None,
        }

    return executor


def _adapter(calls: list[Mapping[str, Any]]) -> LimaRuntimeAdapter:
    return LimaRuntimeAdapter(
        executor=_realistic_executor(calls),
        executor_kind=LOOPBACK_OLLAMA_EXECUTOR_KIND,
        executor_name=LOOPBACK_OLLAMA_EXECUTOR_NAME,
        endpoint=ENDPOINT,
        model=MODEL,
    )


def test_retired_lima_harness_blocks_ollama_before_executor_and_network(
    tmp_path: Path,
) -> None:
    calls: list[Mapping[str, Any]] = []
    state_path = tmp_path / "state" / "runs.jsonl"
    result = run_task_packet(
        LOCAL_PREVIEW,
        runtime_name="lima",
        executor_name="ollama",
        evidence_dir=tmp_path / "evidence",
        state_path=state_path,
        guardian_facade=AllowedGuardianFacade(),  # type: ignore[arg-type]
        runtime_port=_adapter(calls),
    )
    evidence = json.loads(result.evidence_path.read_text(encoding="utf-8"))
    state = JsonlStateStore(state_path).list_runs()[0]

    assert calls == []
    assert result.exit_code == 4
    assert result.result_status == "runtime_unavailable"
    assert result.blocked_reason is not None
    assert RETIRED_DISABLED in result.blocked_reason
    assert result.guardian_called is True
    assert result.guardian_decision_id == DECISION_ID
    assert result.eligible_for_lima is True
    assert result.lima_input_guardian_decision_id is None
    assert result.executor_input_guardian_decision_id is None
    assert result.runtime_output == {}
    assert evidence["guardian_decision_id"] == DECISION_ID
    assert evidence["runtime_metadata"] == {}
    assert state.guardian_decision_id == DECISION_ID
    assert state.lima_input_guardian_decision_id is None
    assert state.executor_input_guardian_decision_id is None
    assert result.executor_call_count == 0
    assert state.executor_call_count == 0
    assert result.lima_called is False
    assert evidence["lima_called"] is False
    assert state.lima_called is False
    assert result.ollama_called is False
    assert evidence["ollama_called"] is False
    assert state.ollama_called is False
    assert result.network_called is False
    assert evidence["network_called"] is False
    assert state.network_called is False
    assert result.credentials_used is False
    assert evidence["credentials_used"] is False
    assert state.credentials_used is False
    assert result.external_side_effects is False
    assert evidence["external_side_effects"] is False
    assert state.external_side_effects is False
    assert result.execution_allowed is False
    assert state.execution_allowed is False
    assert result.evidence_written is True
    assert result.state_written is True


def test_retired_surface_blocks_controlled_ollama_executor(
    tmp_path: Path,
) -> None:
    executor_calls = 0

    def unavailable(_payload: Mapping[str, Any]) -> Mapping[str, Any]:
        nonlocal executor_calls
        executor_calls += 1
        raise AssertionError("retired Ollama executor must not be called")

    adapter = LimaRuntimeAdapter(
        executor=unavailable,
        executor_kind="loopback_ollama",
        executor_name=LOOPBACK_OLLAMA_EXECUTOR_NAME,
        endpoint=ENDPOINT,
        model=MODEL,
    )
    result = run_task_packet(
        LOCAL_PREVIEW,
        runtime_name="lima",
        executor_name="ollama",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state.jsonl",
        guardian_facade=AllowedGuardianFacade(),  # type: ignore[arg-type]
        runtime_port=adapter,
    )

    assert executor_calls == 0
    assert result.exit_code == 4
    assert result.result_status == "runtime_unavailable"
    assert result.blocked_reason is not None
    assert RETIRED_DISABLED in result.blocked_reason
    assert result.lima_called is False
    assert result.executor_called is False
    assert result.executor_call_count == 0
    assert result.ollama_called is False
    assert result.network_called is False
    assert result.credentials_used is False
    assert result.external_side_effects is False
    assert result.execution_allowed is False
    assert result.evidence_written is True
    assert result.state_written is True


def test_remote_endpoint_is_rejected_by_lima_before_executor(
    tmp_path: Path,
) -> None:
    calls: list[Mapping[str, Any]] = []
    adapter = LimaRuntimeAdapter(
        executor=_realistic_executor(calls),
        executor_kind="loopback_ollama",
        executor_name=LOOPBACK_OLLAMA_EXECUTOR_NAME,
        endpoint="http://192.168.1.20:11434",
        model=MODEL,
    )
    result = run_task_packet(
        LOCAL_PREVIEW,
        runtime_name="lima",
        executor_name="ollama",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state.jsonl",
        guardian_facade=AllowedGuardianFacade(),  # type: ignore[arg-type]
        runtime_port=adapter,
    )
    assert calls == []
    assert result.exit_code == 4
    assert result.lima_called is False
    assert result.executor_called is False
    assert result.ollama_called is False
    assert result.network_called is False


@pytest.mark.parametrize(
    ("guardian", "expected_status"),
    (
        (DeniedGuardianFacade(), "blocked"),
        (ApprovalGuardianFacade(), "requires_operator_approval"),
    ),
)
def test_denied_or_approval_required_never_reaches_lima_or_ollama(
    guardian: object,
    expected_status: str,
    tmp_path: Path,
) -> None:
    result = run_task_packet(
        EXTERNAL_EMAIL,
        runtime_name="lima",
        executor_name="ollama",
        evidence_dir=tmp_path / expected_status / "evidence",
        state_path=tmp_path / expected_status / "state.jsonl",
        guardian_facade=guardian,  # type: ignore[arg-type]
        runtime_port=ExplodingRuntime(),  # type: ignore[arg-type]
    )
    assert result.result_status == expected_status
    assert result.lima_called is False
    assert result.executor_called is False
    assert result.ollama_called is False
    assert result.network_called is False
    assert result.execution_allowed is False
    assert result.evidence_written is True
    assert result.state_written is True


def test_direct_ollama_model_adapter_is_blocked_before_model_call(
    tmp_path: Path,
) -> None:
    class ExplodingModel:
        adapter_name = "ollama"
        model_name = MODEL

        def preview(self, *_args: object) -> object:
            raise AssertionError("direct Ollama adapter must not be called")

    class TestAllowedGuardianFacade:
        def evaluate(
            self,
            request: ArcActionRequest,
            **_kwargs: object,
        ) -> GuardianDecision:
            return _decision(action_id=request.action_id, evaluator="test_fake")

    result = run_task_packet(
        LOCAL_PREVIEW,
        runtime_name="fake",
        model_adapter_name="ollama",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state.jsonl",
        guardian_facade=TestAllowedGuardianFacade(),  # type: ignore[arg-type]
        model_preview_adapter=ExplodingModel(),  # type: ignore[arg-type]
    )
    assert result.exit_code == 4
    assert result.result_status == "runtime_unavailable"
    assert result.model_preview_called is False
    assert result.lima_called is False
    assert result.ollama_called is False
    assert result.network_called is False
