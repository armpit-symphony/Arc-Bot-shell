from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import hashlib
import importlib
from typing import Any

from arc_bot_shell.contracts import ArcActionRequest, GuardianDecision, LimaRuntimeResult

from .ports import LimaRuntimeUnavailableError


LIMA_ENTRYPOINT = "lima.harness.execute_v1_live_provider_model_call"
LIMA_PINNED_REFERENCE = "lima-runtime-v1.1-loopback-ollama-executor"
LIMA_PINNED_COMMIT = "deea1c4f5b6d3455a7e97e4b621e22b8d22a6244"
LIMA_PINNED_TAG_OBJECT = "23470f3341fe6f70ebf3595efb9aef07791beed8"
FAKE_EXECUTOR_KIND = "fake"
FAKE_EXECUTOR_NAME = "in_process_fake_executor"


def deterministic_fake_executor(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    decision_id = payload.get("guardian_decision_id")
    if not isinstance(decision_id, str) or not decision_id.strip():
        raise ValueError("Guardian decision_id is required by the fake executor")
    return {
        "provider": "fake_local_model",
        "model": "fake-preview-model",
        "output_text": "Deterministic LIMA runtime preview.",
        "network_called": False,
        "credentials_used": False,
        "ollama_called": False,
    }


def _safe_output_metadata(result: Mapping[str, Any]) -> tuple[dict[str, Any], str | None]:
    output_text = result.get("output_text")
    if not isinstance(output_text, str) or not output_text:
        return {"present": False, "character_count": 0, "sha256": None}, None
    digest = hashlib.sha256(output_text.encode("utf-8")).hexdigest()
    record_hash = result.get("record_hash")
    reference = (
        f"lima-record://{record_hash}/output"
        if isinstance(record_hash, str) and record_hash
        else f"sha256:{digest}"
    )
    return {
        "present": True,
        "character_count": len(output_text),
        "sha256": digest,
    }, reference


@dataclass
class LimaRuntimeAdapter:
    executor: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None
    executor_kind: str = FAKE_EXECUTOR_KIND
    executor_name: str = FAKE_EXECUTOR_NAME
    endpoint: str | None = None
    model: str | None = None
    adapter_name: str = "lima_runtime"

    def execute(
        self,
        request: ArcActionRequest,
        guardian_decision: GuardianDecision,
        executor: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> LimaRuntimeResult:
        self._validate_preconditions(request, guardian_decision)
        entrypoint = self._load_entrypoint()
        runtime_request = self.build_runtime_request(
            request,
            guardian_decision,
            executor_kind=self.executor_kind,
            executor_ref=self.executor_name,
            endpoint=self.endpoint,
            model=self.model,
        )
        executor_call_count = 0
        executor_decision_id: str | None = None

        def counted_executor(payload: Mapping[str, Any]) -> Mapping[str, Any]:
            nonlocal executor_call_count, executor_decision_id
            executor_call_count += 1
            if executor_call_count != 1:
                raise RuntimeError("LIMA executor must be called exactly once")
            executor_decision_id = str(payload.get("guardian_decision_id", ""))
            if executor_decision_id != guardian_decision.decision_id:
                raise RuntimeError("Guardian decision_id changed before the executor")
            return executor(payload)

        try:
            raw_result = entrypoint(runtime_request, counted_executor)
        except Exception as exc:
            raise LimaRuntimeUnavailableError(
                f"LIMA runtime execution failed closed: {type(exc).__name__}: {exc}"
            ) from exc
        if not isinstance(raw_result, Mapping):
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: result must be a mapping"
            )
        result = dict(raw_result)
        decision_id = guardian_decision.decision_id
        evidence = result.get("evidence")
        result_decision = result.get("guardian_decision")
        if (
            result.get("guardian_decision_id") != decision_id
            or not isinstance(result_decision, Mapping)
            or result_decision.get("decision_id") != decision_id
            or not isinstance(evidence, Mapping)
            or evidence.get("guardian_decision_id") != decision_id
            or executor_decision_id != decision_id
        ):
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: Guardian decision_id lineage changed"
            )
        if result.get("executor_called") is not True or executor_call_count != 1:
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: executor was not called exactly once"
            )
        if result.get("executor_kind") != self.executor_kind:
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: executor_kind changed"
            )
        if result.get("credentials_used") is not False:
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: credentials are not allowed"
            )

        if self.executor_kind == FAKE_EXECUTOR_KIND:
            self._validate_fake_result(result)
            result_status = "lima_preview_completed"
        elif self.executor_kind == "loopback_ollama":
            self._validate_loopback_ollama_result(result)
            result_status = (
                "lima_ollama_preview_completed"
                if result.get("status") == "completed"
                else "lima_ollama_preview_unavailable"
            )
        else:
            raise LimaRuntimeUnavailableError("unsupported LIMA executor_kind")

        output_summary, output_reference = _safe_output_metadata(result)
        result.update(
            {
                "lima_adapter": self.adapter_name,
                "lima_entrypoint": LIMA_ENTRYPOINT,
                "lima_pinned_reference": LIMA_PINNED_REFERENCE,
                "lima_pinned_commit": LIMA_PINNED_COMMIT,
                "lima_pinned_tag_object": LIMA_PINNED_TAG_OBJECT,
                "executor_name": self.executor_name,
                "executor_call_count": executor_call_count,
                "lima_input_guardian_decision_id": decision_id,
                "executor_input_guardian_decision_id": executor_decision_id,
                "normalized_output_summary": output_summary,
                "output_reference": output_reference,
            }
        )
        return LimaRuntimeResult(
            runtime_adapter=self.adapter_name,
            result_status=result_status,
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
        *,
        executor_kind: str = FAKE_EXECUTOR_KIND,
        executor_ref: str = FAKE_EXECUTOR_NAME,
        endpoint: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        runtime_request: dict[str, Any] = {
            "request_id": request.action_id,
            "runtime_consumer": "arc_bot_shell",
            "requested_action": request.action_name,
            "guardian_decision": {
                "decision_id": decision.decision_id,
                "status": decision.metadata.get("guardian_status", "allow"),
                "allowed": decision.allowed,
                "requires_approval": decision.requires_approval,
            },
            "executor_kind": executor_kind,
            "executor_ref": executor_ref,
            "normalized_request": {
                "action_id": request.action_id,
                "operator_id": request.operator_id,
                "actor_id": request.operator_id,
                "worker_id": request.worker_id,
                "shell_id": request.worker_id,
                "tenant_id": request.tenant_id,
                "tenant_ref": request.tenant_id,
                "task_ref": request.task_ref,
                "target_ref": request.task_ref,
                "summary": request.summary,
                "payload_summary": request.payload.get(
                    "payload_summary", request.summary
                ),
                "payload_keys": sorted(request.payload.keys()),
                "guardian_decision_id": decision.decision_id,
            },
            "evidence_refs": [
                f"evidence://arc-harness/{request.action_id}/guardian-decision",
                f"evidence://arc-harness/{request.action_id}/task-packet",
            ],
        }
        if executor_kind == "loopback_ollama":
            runtime_request.update(
                {
                    "endpoint": endpoint,
                    "model": model,
                    "network_scope": "loopback_only",
                    "credentials_used": False,
                    "external_side_effects": False,
                }
            )
        return runtime_request

    @staticmethod
    def _validate_fake_result(result: Mapping[str, Any]) -> None:
        if result.get("network_called") is not False:
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: fake executor used network"
            )
        if result.get("ollama_called") is not False:
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: fake executor called Ollama"
            )

    def _validate_loopback_ollama_result(self, result: Mapping[str, Any]) -> None:
        if result.get("provider") != "ollama":
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: provider is not Ollama"
            )
        if result.get("endpoint") != self.endpoint or result.get("model") != self.model:
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: Ollama target changed"
            )
        if result.get("network_called") is not True:
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: Ollama network call was not reported"
            )
        if result.get("network_scope") != "loopback_only":
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: network scope is not loopback-only"
            )
        if result.get("ollama_called") is not True:
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: Ollama call was not reported"
            )
        if result.get("external_side_effects") is not False:
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: external side effects are not allowed"
            )
        if result.get("status") not in {"completed", "unavailable"}:
            raise LimaRuntimeUnavailableError(
                "LIMA runtime contract mismatch: unsupported Ollama status"
            )

    @staticmethod
    def _validate_preconditions(
        request: ArcActionRequest,
        decision: GuardianDecision,
    ) -> None:
        if not isinstance(decision, GuardianDecision):
            raise LimaRuntimeUnavailableError("Guardian decision is required")
        if not decision.decision_id.strip():
            raise LimaRuntimeUnavailableError("Guardian decision_id is required")
        if decision.status != "allowed_preview_only":
            raise LimaRuntimeUnavailableError("Guardian decision is not allow")
        if decision.metadata.get("guardian_status") not in {None, "allow"}:
            raise LimaRuntimeUnavailableError("Guardian status is not allow")
        if decision.allowed is not True:
            raise LimaRuntimeUnavailableError("Guardian allowed must be true")
        if decision.requires_approval is not False:
            raise LimaRuntimeUnavailableError(
                "Guardian approval-required decision cannot reach LIMA"
            )
        if request.action_name != "arc.local_model_preview":
            raise LimaRuntimeUnavailableError(
                "only arc.local_model_preview is eligible for LIMA"
            )
        if not request.preview_only:
            raise LimaRuntimeUnavailableError("LIMA requires preview_only=true")

    @staticmethod
    def _load_entrypoint() -> Callable[
        [Mapping[str, Any], Callable[[Mapping[str, Any]], Mapping[str, Any]]],
        dict[str, Any],
    ]:
        try:
            harness = importlib.import_module("lima.harness")
            entrypoint = getattr(harness, "execute_v1_live_provider_model_call")
        except (AttributeError, ImportError, ModuleNotFoundError) as exc:
            raise LimaRuntimeUnavailableError(
                f"LIMA public import unavailable: {type(exc).__name__}"
            ) from exc
        if not callable(entrypoint):
            raise LimaRuntimeUnavailableError("LIMA public entrypoint is not callable")
        return entrypoint


def build_lima_runtime_adapter(
    executor_name: str | None,
    *,
    endpoint: str | None = None,
    model: str | None = None,
) -> LimaRuntimeAdapter:
    """Build only the two published LIMA executor kinds."""

    if executor_name in {None, "fake"}:
        return LimaRuntimeAdapter()
    if executor_name == "ollama":
        from .ollama_executor import (
            LOOPBACK_OLLAMA_EXECUTOR_KIND,
            LOOPBACK_OLLAMA_EXECUTOR_NAME,
            execute_loopback_ollama,
            normalize_loopback_ollama_url,
            resolve_ollama_model,
        )

        if endpoint is None:
            raise LimaRuntimeUnavailableError("Ollama endpoint is required")
        try:
            normalized_endpoint = normalize_loopback_ollama_url(endpoint)
            resolved_model = resolve_ollama_model(model)
        except ValueError as exc:
            raise LimaRuntimeUnavailableError(str(exc)) from exc
        return LimaRuntimeAdapter(
            executor=execute_loopback_ollama,
            executor_kind=LOOPBACK_OLLAMA_EXECUTOR_KIND,
            executor_name=LOOPBACK_OLLAMA_EXECUTOR_NAME,
            endpoint=normalized_endpoint,
            model=resolved_model,
        )
    raise LimaRuntimeUnavailableError("unsupported LIMA executor")
