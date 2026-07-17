from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import importlib
from typing import Any

from arc_bot_shell.contracts import ArcActionRequest, GuardianDecision, LimaRuntimeResult

from .ports import LimaRuntimeUnavailableError


LIMA_ENTRYPOINT = 'lima.harness.execute_v1_live_provider_model_call'
LIMA_PINNED_REFERENCE = 'lima-runtime-v1-arc-consumer-baseline'
LIMA_PINNED_COMMIT = 'cd40f486be19e01026d293b374b99d213ca275d9'
FAKE_EXECUTOR_NAME = 'in_process_fake_executor'


def deterministic_fake_executor(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    decision_id = payload.get('guardian_decision_id')
    if not isinstance(decision_id, str) or not decision_id.strip():
        raise ValueError('Guardian decision_id is required by the fake executor')
    return {
        'provider': 'fake_local_model',
        'model': 'fake-preview-model',
        'output_text': 'Deterministic LIMA runtime preview.',
        'network_called': False,
        'credentials_used': False,
        'ollama_called': False,
    }


@dataclass
class LimaRuntimeAdapter:
    executor: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None
    adapter_name: str = 'lima_runtime'

    def execute(
        self,
        request: ArcActionRequest,
        guardian_decision: GuardianDecision,
        executor: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> LimaRuntimeResult:
        self._validate_preconditions(request, guardian_decision)
        entrypoint = self._load_entrypoint()
        runtime_request = self.build_runtime_request(request, guardian_decision)
        try:
            raw_result = entrypoint(runtime_request, executor)
        except Exception as exc:
            raise LimaRuntimeUnavailableError(
                f'LIMA runtime execution failed closed: {type(exc).__name__}: {exc}'
            ) from exc
        if not isinstance(raw_result, Mapping):
            raise LimaRuntimeUnavailableError(
                'LIMA runtime contract mismatch: result must be a mapping'
            )
        result = dict(raw_result)
        decision_id = guardian_decision.decision_id
        evidence = result.get('evidence')
        if (
            result.get('guardian_decision_id') != decision_id
            or not isinstance(evidence, Mapping)
            or evidence.get('guardian_decision_id') != decision_id
        ):
            raise LimaRuntimeUnavailableError(
                'LIMA runtime contract mismatch: Guardian decision_id lineage changed'
            )
        if result.get('executor_called') is not True:
            raise LimaRuntimeUnavailableError(
                'LIMA runtime contract mismatch: executor call was not recorded'
            )
        if result.get('network_called') is not False:
            raise LimaRuntimeUnavailableError(
                'LIMA runtime contract mismatch: network use is not allowed in v0.9'
            )
        if result.get('credentials_used') is not False:
            raise LimaRuntimeUnavailableError(
                'LIMA runtime contract mismatch: credentials are not allowed in v0.9'
            )
        if result.get('ollama_called') is not False:
            raise LimaRuntimeUnavailableError(
                'LIMA runtime contract mismatch: Ollama is not allowed in v0.9'
            )
        result.update(
            {
                'lima_adapter': self.adapter_name,
                'lima_entrypoint': LIMA_ENTRYPOINT,
                'lima_pinned_reference': LIMA_PINNED_REFERENCE,
                'lima_pinned_commit': LIMA_PINNED_COMMIT,
                'executor_name': FAKE_EXECUTOR_NAME,
                'normalized_output_summary': result.get('output_text'),
            }
        )
        return LimaRuntimeResult(
            runtime_adapter=self.adapter_name,
            result_status='lima_preview_completed',
            output=result,
        )

    def invoke(
        self,
        request: ArcActionRequest,
        decision: GuardianDecision,
    ) -> LimaRuntimeResult:
        return self.execute(
            request,
            decision,
            self.executor or deterministic_fake_executor,
        )

    @staticmethod
    def build_runtime_request(
        request: ArcActionRequest,
        decision: GuardianDecision,
    ) -> dict[str, Any]:
        return {
            'request_id': request.action_id,
            'runtime_consumer': 'arc_bot_shell',
            'requested_action': request.action_name,
            'guardian_decision': {
                'decision_id': decision.decision_id,
                'status': decision.metadata.get('guardian_status', 'allow'),
                'allowed': decision.allowed,
                'requires_approval': decision.requires_approval,
            },
            'executor_ref': FAKE_EXECUTOR_NAME,
            'normalized_request': {
                'action_id': request.action_id,
                'operator_id': request.operator_id,
                'actor_id': request.operator_id,
                'worker_id': request.worker_id,
                'shell_id': request.worker_id,
                'tenant_id': request.tenant_id,
                'tenant_ref': request.tenant_id,
                'task_ref': request.task_ref,
                'target_ref': request.task_ref,
                'summary': request.summary,
                'payload_summary': request.payload.get(
                    'payload_summary', request.summary
                ),
                'payload_keys': sorted(request.payload.keys()),
                'guardian_decision_id': decision.decision_id,
            },
            'evidence_refs': [
                f'evidence://arc-harness/{request.action_id}/guardian-decision',
                f'evidence://arc-harness/{request.action_id}/task-packet',
            ],
        }

    @staticmethod
    def _validate_preconditions(
        request: ArcActionRequest,
        decision: GuardianDecision,
    ) -> None:
        if not isinstance(decision, GuardianDecision):
            raise LimaRuntimeUnavailableError('Guardian decision is required')
        if not decision.decision_id.strip():
            raise LimaRuntimeUnavailableError('Guardian decision_id is required')
        if decision.status != 'allowed_preview_only':
            raise LimaRuntimeUnavailableError('Guardian decision is not allow')
        if decision.metadata.get('guardian_status') not in {None, 'allow'}:
            raise LimaRuntimeUnavailableError('Guardian status is not allow')
        if decision.allowed is not True:
            raise LimaRuntimeUnavailableError('Guardian allowed must be true')
        if decision.requires_approval is not False:
            raise LimaRuntimeUnavailableError(
                'Guardian approval-required decision cannot reach LIMA'
            )
        if request.action_name != 'arc.local_model_preview':
            raise LimaRuntimeUnavailableError(
                'only arc.local_model_preview is eligible for LIMA v0.9'
            )
        if not request.preview_only:
            raise LimaRuntimeUnavailableError('LIMA v0.9 requires preview_only=true')

    @staticmethod
    def _load_entrypoint() -> Callable[
        [Mapping[str, Any], Callable[[Mapping[str, Any]], Mapping[str, Any]]],
        dict[str, Any],
    ]:
        try:
            harness = importlib.import_module('lima.harness')
            entrypoint = getattr(harness, 'execute_v1_live_provider_model_call')
        except (AttributeError, ImportError, ModuleNotFoundError) as exc:
            raise LimaRuntimeUnavailableError(
                f'LIMA public import unavailable: {type(exc).__name__}'
            ) from exc
        if not callable(entrypoint):
            raise LimaRuntimeUnavailableError('LIMA public entrypoint is not callable')
        return entrypoint
