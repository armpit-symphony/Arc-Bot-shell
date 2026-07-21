from __future__ import annotations

import importlib
import json
from pathlib import Path
import socket
import threading
from typing import Any, Mapping

import pytest

from arc_guardian_spine import ArcActionRequest as ArcGovernedActionRequest
from arc_guardian_spine.lima_preflight import (
    call_lima_governed_preflight_for_arc_action,
)
from arc_bot_shell.contracts import ArcActionRequest, GuardianDecision
from arc_bot_shell.harness import run_task_packet
from arc_bot_shell.lima import LimaRuntimeAdapter, LimaRuntimeUnavailableError
from arc_bot_shell.state import JsonlStateStore
from lima.runtime import run_governed_request


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_PREVIEW = REPO_ROOT / 'samples' / 'tasks' / 'local_model_preview.json'
DECISION_ID = 'guardian-decision:test-v0-9'


def _request() -> ArcActionRequest:
    return ArcActionRequest.from_dict(
        json.loads(LOCAL_PREVIEW.read_text(encoding='utf-8'))
    )


def _governed_request() -> ArcGovernedActionRequest:
    return ArcGovernedActionRequest(
        action_id="arc-action:rc1-supported-preflight",
        action_kind="status_read",
        operator_id="operator-rc1",
        worker_id="arc-worker-rc1",
        tenant_id="tenant-rc1",
        task_ref="task://arc/rc1-supported-preflight",
        payload_summary="Read Arc worker status without execution.",
        evidence_refs=("evidence://arc/rc1-supported-preflight",),
    )


def _decision(**overrides: Any) -> GuardianDecision:
    values = {
        'decision_id': DECISION_ID,
        'action_id': _request().action_id,
        'status': 'allowed_preview_only',
        'evaluator': 'guardian_core',
        'reason': 'real-shaped Guardian allow',
        'allowed': True,
        'requires_approval': False,
        'requested_action': 'arc.local_model_preview',
        'metadata': {
            'guardian_status': 'allow',
            'guardian_adapter': 'guardian_core',
        },
    }
    values.update(overrides)
    return GuardianDecision(**values)


def _fake_result() -> Mapping[str, Any]:
    return {
        'provider': 'fake_local_model',
        'model': 'fake-preview-model',
        'output_text': 'Deterministic LIMA runtime preview.',
        'network_called': False,
        'credentials_used': False,
        'ollama_called': False,
    }


class AllowedGuardianFacade:
    def evaluate(self, request: ArcActionRequest, **_kwargs: object) -> GuardianDecision:
        return _decision(action_id=request.action_id)


class CountingLimaAdapter(LimaRuntimeAdapter):
    calls: int = 0

    def invoke(
        self,
        request: ArcActionRequest,
        decision: GuardianDecision,
    ):
        self.calls += 1
        return super().invoke(request, decision)


def test_supported_lima_rc_import_and_retired_harness_boundary() -> None:
    assert callable(run_governed_request)
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("lima.harness")


def test_retired_harness_fails_closed_before_supported_preflight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor_calls = 0

    def executor(_payload: Mapping[str, Any]) -> Mapping[str, Any]:
        nonlocal executor_calls
        executor_calls += 1
        return _fake_result()

    with pytest.raises(
        LimaRuntimeUnavailableError,
        match="LIMA public import unavailable",
    ):
        LimaRuntimeAdapter().execute(_request(), _decision(), executor)
    assert executor_calls == 0

    counters = {"network": 0, "background": 0}

    def block_network(*_args: object, **_kwargs: object) -> None:
        counters["network"] += 1
        raise AssertionError("governed preflight attempted network access")

    def block_thread(
        _self: threading.Thread,
        *_args: object,
        **_kwargs: object,
    ) -> None:
        counters["background"] += 1
        raise AssertionError("governed preflight attempted a background job")

    monkeypatch.setattr(socket.socket, "connect", block_network)
    monkeypatch.setattr(socket.socket, "connect_ex", block_network)
    monkeypatch.setattr(socket, "create_connection", block_network)
    monkeypatch.setattr(socket, "getaddrinfo", block_network)
    monkeypatch.setattr(threading.Thread, "start", block_thread)

    result = call_lima_governed_preflight_for_arc_action(_governed_request())

    assert result.lima_available is True
    assert result.decision.status == "allowed_dry_run"
    assert result.decision.executable is False
    assert result.decision.execution_allowed is False
    assert result.decision.side_effects_allowed is False
    assert result.response["runtime_authority_blocked"] is True
    assert result.response["runtime_execution_blocked"] is True
    assert result.response["executable"] is False
    assert result.response["execution_allowed"] is False
    assert result.response["side_effects_allowed"] is False
    assert result.response["provider_model_routed"] is False
    assert result.response["tool_executed"] is False
    assert result.response["file_mutation_executed"] is False
    assert result.response["network_action_executed"] is False
    assert result.response["connector_invoked"] is False
    assert result.response["approval_token_issued"] is False
    assert counters == {"network": 0, "background": 0}


@pytest.mark.parametrize(
    'decision',
    [
        _decision(decision_id=''),
        _decision(status='blocked', allowed=False),
        _decision(
            status='requires_operator_approval',
            allowed=False,
            requires_approval=True,
            metadata={'guardian_status': 'requires_approval'},
        ),
    ],
)
def test_invalid_guardian_decisions_fail_before_lima_executor(
    decision: GuardianDecision,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    entrypoint_loads = 0

    def load_entrypoint() -> object:
        nonlocal entrypoint_loads
        entrypoint_loads += 1
        raise AssertionError('LIMA must not load for an invalid Guardian decision')

    monkeypatch.setattr(
        LimaRuntimeAdapter,
        '_load_entrypoint',
        staticmethod(load_entrypoint),
    )

    def executor(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        nonlocal calls
        calls += 1
        return _fake_result()

    with pytest.raises(LimaRuntimeUnavailableError):
        LimaRuntimeAdapter().execute(_request(), decision, executor)

    assert entrypoint_loads == 0
    assert calls == 0


def test_missing_guardian_decision_fails_before_lima(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entrypoint_loads = 0

    def load_entrypoint() -> object:
        nonlocal entrypoint_loads
        entrypoint_loads += 1
        raise AssertionError('LIMA must not load without a Guardian decision')

    monkeypatch.setattr(
        LimaRuntimeAdapter,
        '_load_entrypoint',
        staticmethod(load_entrypoint),
    )

    with pytest.raises(LimaRuntimeUnavailableError, match='decision is required'):
        LimaRuntimeAdapter().execute(
            _request(),
            None,  # type: ignore[arg-type]
            lambda payload: _fake_result(),
        )

    assert entrypoint_loads == 0


def test_missing_lima_fails_closed_in_explicit_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing() -> object:
        raise LimaRuntimeUnavailableError('LIMA public import unavailable')

    monkeypatch.setattr(LimaRuntimeAdapter, '_load_entrypoint', staticmethod(missing))
    with pytest.raises(LimaRuntimeUnavailableError, match='unavailable'):
        LimaRuntimeAdapter().invoke(_request(), _decision())


def test_contract_mismatch_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def mismatched(
        request: Mapping[str, Any],
        executor: object,
    ) -> dict[str, Any]:
        return {
            'guardian_decision_id': 'guardian-decision:changed',
            'evidence': {'guardian_decision_id': 'guardian-decision:changed'},
            'executor_called': True,
            'network_called': False,
            'credentials_used': False,
            'ollama_called': False,
        }

    monkeypatch.setattr(
        LimaRuntimeAdapter,
        '_load_entrypoint',
        staticmethod(lambda: mismatched),
    )
    with pytest.raises(LimaRuntimeUnavailableError, match='lineage changed'):
        LimaRuntimeAdapter().invoke(_request(), _decision())


def test_missing_retired_surface_blocks_executor_errors_and_output() -> None:
    executor_calls = 0

    def unreachable_executor(_payload: Mapping[str, Any]) -> Mapping[str, Any]:
        nonlocal executor_calls
        executor_calls += 1
        raise AssertionError("retired executor must not be called")

    with pytest.raises(LimaRuntimeUnavailableError, match='public import unavailable'):
        LimaRuntimeAdapter().execute(
            _request(),
            _decision(),
            unreachable_executor,
        )

    with pytest.raises(LimaRuntimeUnavailableError, match='public import unavailable'):
        LimaRuntimeAdapter().execute(
            _request(),
            _decision(),
            unreachable_executor,
        )
    assert executor_calls == 0


def test_harness_records_fail_closed_when_retired_surface_is_missing(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / 'state' / 'runs.jsonl'
    adapter = CountingLimaAdapter()

    result = run_task_packet(
        LOCAL_PREVIEW,
        runtime_name='lima',
        executor_name='fake',
        evidence_dir=tmp_path / 'evidence',
        state_path=state_path,
        guardian_facade=AllowedGuardianFacade(),  # type: ignore[arg-type]
        runtime_port=adapter,
    )
    evidence = json.loads(result.evidence_path.read_text(encoding='utf-8'))
    state = JsonlStateStore(state_path).list_runs()[0]

    assert adapter.calls == 1
    assert result.exit_code == 4
    assert result.result_status == 'runtime_unavailable'
    assert result.blocked_reason is not None
    assert 'LIMA public import unavailable' in result.blocked_reason
    assert result.guardian_decision_id == DECISION_ID
    assert result.runtime_output == {}
    assert evidence['guardian_decision_id'] == DECISION_ID
    assert evidence['guardian']['decision_id'] == DECISION_ID
    assert evidence['runtime_metadata'] == {}
    assert state.guardian_decision_id == DECISION_ID
    assert result.lima_called is False
    assert evidence['lima_called'] is False
    assert state.lima_called is False
    assert result.executor_called is False
    assert evidence['executor_called'] is False
    assert state.executor_called is False
    assert result.network_called is False
    assert evidence['network_called'] is False
    assert state.network_called is False
    assert result.credentials_used is False
    assert evidence['credentials_used'] is False
    assert state.credentials_used is False
    assert result.execution_allowed is False
    assert state.execution_allowed is False
    assert result.external_side_effects is False
    assert state.external_side_effects is False
    assert result.ollama_called is False
    assert evidence['ollama_called'] is False
    assert state.ollama_called is False
    assert result.lima_entrypoint is None
    assert state.lima_entrypoint is None
    assert state.lima_result_status is None
