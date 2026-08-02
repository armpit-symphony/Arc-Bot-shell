from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import hashlib
from typing import Any

from arc_bot_shell.contracts import ArcActionRequest, GuardianDecision, LimaRuntimeResult

from .ports import LimaRuntimeUnavailableError


LIMA_ENTRYPOINT = "lima.runtime.run_governed_request"
LIMA_PINNED_REFERENCE = "lima-runtime==0.1.0rc1"
LIMA_PINNED_COMMIT = "40d6f1379284931ee46f05650e9201d6f98975d6"
LIMA_PINNED_TAG_OBJECT = None

# Trust baselines this build still accepts from an operator config written by
# an earlier install, and normalises forward on load. A config persisted
# before the baseline moved must keep working; it must not silently keep
# claiming a LIMA commit that is no longer the one Arc runs.
LIMA_SUPERSEDED_COMMITS = frozenset(
    {
        # v0.10/v0.11 baseline, left behind when the install pin moved to the
        # LIMA v0.1 RC1 public API freeze.
        "4e7c648349f0a5a19694ac5f0c57b5cb14dc2b17",
    }
)
RETIRED_EXECUTION_DISABLED = (
    "retired lima.harness execution surface is disabled; "
    "use lima.runtime.run_governed_request through Arc governed preflight"
)
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
        del executor
        raise LimaRuntimeUnavailableError(RETIRED_EXECUTION_DISABLED)

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
        raise LimaRuntimeUnavailableError(RETIRED_EXECUTION_DISABLED)


def build_lima_runtime_adapter(
    executor_name: str | None,
    *,
    endpoint: str | None = None,
    model: str | None = None,
) -> LimaRuntimeAdapter:
    """Return a fail-closed adapter for the retired execution route."""

    if executor_name in {None, "fake"}:
        return LimaRuntimeAdapter()
    if executor_name == "ollama":
        del endpoint, model
        raise LimaRuntimeUnavailableError(RETIRED_EXECUTION_DISABLED)
    raise LimaRuntimeUnavailableError("unsupported LIMA executor")
