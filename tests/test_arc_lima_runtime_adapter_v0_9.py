from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from arc_bot_shell.contracts import ArcActionRequest, GuardianDecision
from arc_bot_shell.harness import run_task_packet
from arc_bot_shell.lima import (
    LIMA_ENTRYPOINT,
    LIMA_PINNED_COMMIT,
    LIMA_PINNED_REFERENCE,
    LimaRuntimeAdapter,
    LimaRuntimeUnavailableError,
)
from arc_bot_shell.state import JsonlStateStore


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_PREVIEW = REPO_ROOT / 'samples' / 'tasks' / 'local_model_preview.json'
DECISION_ID = 'guardian-decision:test-v0-9'


def _request() -> ArcActionRequest:
    return ArcActionRequest.from_dict(
        json.loads(LOCAL_PREVIEW.read_text(encoding='utf-8'))
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


def test_public_lima_import_is_clean() -> None:
    from lima.harness import execute_v1_live_provider_model_call

    assert callable(execute_v1_live_provider_model_call)


def test_guardian_allow_reaches_lima_once_with_exact_decision_id() -> None:
    calls: list[Mapping[str, Any]] = []

    def executor(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        calls.append(payload)
        return _fake_result()

    result = LimaRuntimeAdapter().execute(_request(), _decision(), executor)

    assert len(calls) == 1
    assert calls[0]['guardian_decision_id'] == DECISION_ID
    assert calls[0]['guardian_decision']['decision_id'] == DECISION_ID
    assert result.result_status == 'lima_preview_completed'
    assert result.output['guardian_decision_id'] == DECISION_ID
    assert result.output['evidence']['guardian_decision_id'] == DECISION_ID
    assert result.output['lima_entrypoint'] == LIMA_ENTRYPOINT
    assert result.output['lima_pinned_reference'] == LIMA_PINNED_REFERENCE
    assert result.output['lima_pinned_commit'] == LIMA_PINNED_COMMIT
    assert result.output['executor_called'] is True
    assert result.output['network_called'] is False
    assert result.output['credentials_used'] is False
    assert result.output['ollama_called'] is False


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


def test_executor_exception_and_malformed_output_are_controlled() -> None:
    def exploding(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        raise RuntimeError('fake executor failure')

    with pytest.raises(LimaRuntimeUnavailableError, match='failed closed'):
        LimaRuntimeAdapter().execute(_request(), _decision(), exploding)

    with pytest.raises(LimaRuntimeUnavailableError, match='failed closed'):
        LimaRuntimeAdapter().execute(
            _request(),
            _decision(),
            lambda payload: {'provider': 'fake_local_model'},
        )


def test_harness_records_same_lineage_in_result_evidence_and_state(
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
    assert result.result_status == 'lima_preview_completed'
    assert result.guardian_decision_id == DECISION_ID
    assert result.runtime_output['guardian_decision_id'] == DECISION_ID
    assert result.runtime_output['evidence']['guardian_decision_id'] == DECISION_ID
    assert evidence['guardian_decision_id'] == DECISION_ID
    assert evidence['guardian']['decision_id'] == DECISION_ID
    assert evidence['runtime_metadata']['guardian_decision_id'] == DECISION_ID
    assert state.guardian_decision_id == DECISION_ID
    assert result.lima_called is True
    assert evidence['lima_called'] is True
    assert state.lima_called is True
    assert result.executor_called is True
    assert evidence['executor_called'] is True
    assert state.executor_called is True
    assert result.network_called is False
    assert evidence['network_called'] is False
    assert state.network_called is False
    assert result.credentials_used is False
    assert evidence['credentials_used'] is False
    assert state.credentials_used is False
    assert result.ollama_called is False
    assert evidence['ollama_called'] is False
    assert state.ollama_called is False
    assert state.lima_entrypoint == LIMA_ENTRYPOINT
    assert state.lima_result_status == 'completed'
