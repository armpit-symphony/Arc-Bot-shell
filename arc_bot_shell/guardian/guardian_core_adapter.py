"""Adapter for the installed Guardian Suite standalone decision contract."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import importlib
import os
from pathlib import Path
import sys
from typing import Any, Callable, Iterator, Mapping

from arc_bot_shell.contracts import ArcActionRequest, GuardianDecision

DEFAULT_GUARDIAN_CONTRACT_REFERENCE = "guardian-core-v1.1-local-model-preview-policy"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
GUARDIAN_CORE_IMPORT_PATH = "guardian_core"
LOCAL_MODEL_PREVIEW_CONTEXT: Mapping[str, Any] = {
    "network_scope": "loopback_only",
    "external_side_effects": False,
    "credentials_required": False,
    "execution_scope": "model_preview_only",
    "runtime_route": "lima",
}


class GuardianCoreAdapterError(RuntimeError):
    """Raised when the public Guardian contract is missing or incompatible."""


PublicContract = tuple[type[Any], type[Any], Callable[[Any], Any], str]
ContractLoader = Callable[[Path | None], PublicContract]


@contextmanager
def _temporary_sys_path(path: Path | None) -> Iterator[None]:
    if path is None:
        yield
        return
    text = str(path.resolve())
    inserted = text not in sys.path
    if inserted:
        sys.path.insert(0, text)
    try:
        importlib.invalidate_caches()
        yield
    finally:
        if inserted:
            sys.path.remove(text)


def _load_public_contract(path: Path | None) -> PublicContract:
    try:
        with _temporary_sys_path(path):
            from guardian_core import (
                GuardianDecision as PublicGuardianDecision,
                GuardianEvaluationRequest,
                evaluate_guardian_request,
            )
    except Exception as exc:
        raise GuardianCoreAdapterError(
            f"guardian_core public contract import failed: {type(exc).__name__}"
        ) from exc

    module = sys.modules.get(GUARDIAN_CORE_IMPORT_PATH)
    origin_text = None if module is None else getattr(module, "__file__", None)
    if origin_text is None:
        raise GuardianCoreAdapterError("guardian_core has no import origin")
    origin = Path(origin_text).resolve()
    if path is not None and not origin.is_relative_to(path.resolve()):
        raise GuardianCoreAdapterError(
            "guardian_core resolved outside ARC_GUARDIAN_PATH"
        )
    return (
        GuardianEvaluationRequest,
        PublicGuardianDecision,
        evaluate_guardian_request,
        str(origin),
    )


def build_guardian_policy_context(
    request: ArcActionRequest,
) -> Mapping[str, Any]:
    """Return the reviewed policy context; requested action remains authoritative."""

    return dict(LOCAL_MODEL_PREVIEW_CONTEXT)


def _safe_arguments(request: ArcActionRequest, endpoint: str) -> dict[str, Any]:
    if request.action_name == "arc.local_model_preview":
        return {
            "model_adapter": "ollama",
            "endpoint": endpoint,
        }
    payload_summary = request.payload.get("payload_summary")
    return {
        "summary": request.summary,
        "payload_summary": (
            payload_summary if isinstance(payload_summary, str) else None
        ),
        "requested_capabilities": list(request.requested_capabilities),
    }


@dataclass
class GuardianCoreAdapter:
    """Arc adapter using only the supported Guardian package-level public API."""

    adapter_name = "guardian_core"

    guardian_path: Path | None = None
    endpoint: str = DEFAULT_OLLAMA_URL
    contract_reference: str = DEFAULT_GUARDIAN_CONTRACT_REFERENCE
    contract_loader: ContractLoader = _load_public_contract

    @classmethod
    def from_environ(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> "GuardianCoreAdapter":
        values = os.environ if environ is None else environ
        path_text = values.get("ARC_GUARDIAN_PATH", "").strip()
        endpoint = values.get("ARC_OLLAMA_URL", DEFAULT_OLLAMA_URL).strip()
        reference = values.get(
            "ARC_GUARDIAN_REFERENCE",
            DEFAULT_GUARDIAN_CONTRACT_REFERENCE,
        ).strip()
        return cls(
            guardian_path=None if not path_text else Path(path_text).expanduser(),
            endpoint=endpoint or DEFAULT_OLLAMA_URL,
            contract_reference=reference or DEFAULT_GUARDIAN_CONTRACT_REFERENCE,
        )

    def evaluate(
        self,
        request: ArcActionRequest,
        *,
        policy_context: Mapping[str, Any],
    ) -> GuardianDecision:
        (
            request_type,
            decision_type,
            evaluator,
            import_origin,
        ) = self.contract_loader(self.guardian_path)
        try:
            guardian_request = request_type(
                requested_action=request.action_name,
                arguments=_safe_arguments(request, self.endpoint),
                policy_context=dict(policy_context),
                actor_id=request.operator_id,
                task_ref=request.task_ref,
                source="arc_bot_shell",
                metadata={
                    "action_id": request.action_id,
                    "worker_id": request.worker_id,
                    "tenant_id": request.tenant_id,
                },
            )
            raw_decision = evaluator(guardian_request)
        except Exception as exc:
            raise GuardianCoreAdapterError(
                f"guardian_core evaluation failed: {type(exc).__name__}"
            ) from exc

        if not isinstance(raw_decision, decision_type):
            raise GuardianCoreAdapterError(
                "guardian_core evaluator returned an incompatible decision type"
            )
        decision_id = getattr(raw_decision, "decision_id", None)
        status = getattr(raw_decision, "status", None)
        allowed = getattr(raw_decision, "allowed", None)
        requires_approval = getattr(raw_decision, "requires_approval", None)
        if not isinstance(decision_id, str) or not decision_id.strip():
            raise GuardianCoreAdapterError(
                "guardian_core decision is missing decision_id"
            )
        if status not in {"allow", "deny", "requires_approval"}:
            raise GuardianCoreAdapterError(
                "guardian_core decision has an unsupported status"
            )
        if (
            (
                status == "allow"
                and (allowed is not True or requires_approval is not False)
            )
            or (
                status == "deny"
                and (allowed is not False or requires_approval is not False)
            )
            or (
                status == "requires_approval"
                and (allowed is not False or requires_approval is not True)
            )
        ):
            raise GuardianCoreAdapterError(
                "guardian_core decision fields are inconsistent"
            )

        arc_status = {
            "allow": "allowed_preview_only",
            "deny": "blocked",
            "requires_approval": "requires_operator_approval",
        }[status]
        return GuardianDecision(
            decision_id=decision_id,
            action_id=request.action_id,
            status=arc_status,  # type: ignore[arg-type]
            evaluator=self.adapter_name,
            reason=str(getattr(raw_decision, "reason", "")),
            allowed=allowed,
            requires_approval=requires_approval,
            requested_action=str(
                getattr(raw_decision, "requested_action", request.action_name)
            ),
            risk_level=getattr(raw_decision, "risk_level", None),
            policy_name=getattr(raw_decision, "policy_name", None),
            created_at=getattr(raw_decision, "created_at", None),
            metadata={
                "guardian_adapter": self.adapter_name,
                "guardian_import_path": GUARDIAN_CORE_IMPORT_PATH,
                "guardian_import_origin": import_origin,
                "guardian_contract_reference": self.contract_reference,
                "guardian_status": status,
                "guardian_allowed": allowed,
                "guardian_requires_approval": requires_approval,
                "guardian_request": {
                    "requested_action": request.action_name,
                    "arguments": _safe_arguments(request, self.endpoint),
                    "policy_context": dict(policy_context),
                },
                "guardian_metadata": dict(getattr(raw_decision, "metadata", {}) or {}),
            },
        )


__all__ = [
    "DEFAULT_GUARDIAN_CONTRACT_REFERENCE",
    "DEFAULT_OLLAMA_URL",
    "GUARDIAN_CORE_IMPORT_PATH",
    "GuardianCoreAdapter",
    "GuardianCoreAdapterError",
    "LOCAL_MODEL_PREVIEW_CONTEXT",
    "build_guardian_policy_context",
]
