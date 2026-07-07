"""Arc-to-LIMA governed dry-run preflight adapter.

This module maps Arc's ``ArcActionRequest`` into the accepted LIMA Week 1
runtime API. It returns decisions only; it does not execute tools, models,
connectors, sends, file mutations, schedulers, credentials, robotics, IoT, or
physical-world actions.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

from .base import ArcActionRequest


ARC_LIMA_SOURCE_POLICY = "arc_guardian_spine.lima_preflight:v0.1"
ARC_LIMA_CONSUMER = "arc_bot_shell"
ARC_LIMA_SURFACE = "arc_guardian_spine.lima_preflight"


class ArcLimaGovernedPreflightError(RuntimeError):
    """Raised when Arc cannot build a governed LIMA preflight request."""


@dataclass(frozen=True)
class ArcLimaFailClosedDecision:
    """Arc-side denied decision used when LIMA is unavailable or input is invalid."""

    decision_id: str
    request_id: str
    consumer: str
    status: str = "denied"
    allowed: bool = False
    requires_approval: bool = False
    risk_level: str = "blocked"
    reason_codes: tuple[str, ...] = ("arc_lima_preflight_fail_closed",)
    source_policy: str = ARC_LIMA_SOURCE_POLICY
    audit_event: Mapping[str, Any] | None = None
    executable: bool = False
    execution_allowed: bool = False
    side_effects_allowed: bool = False
    metadata: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "consumer": self.consumer,
            "status": self.status,
            "allowed": False,
            "requires_approval": False,
            "risk_level": self.risk_level,
            "reason_codes": tuple(self.reason_codes),
            "source_policy": self.source_policy,
            "audit_event": dict(self.audit_event or {}),
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
            "metadata": dict(self.metadata or {}),
        }


@dataclass(frozen=True)
class ArcLimaGovernedPreflightResult:
    """Arc-facing result for a LIMA governed dry-run preflight."""

    arc_action_id: str
    lima_request: dict[str, Any]
    decision: Any
    lima_available: bool
    error: str | None = None

    @property
    def response(self) -> dict[str, Any]:
        decision_dict = _decision_to_dict(self.decision)
        return {
            "record_type": "arc_lima_governed_preflight_dry_run_result",
            "arc_action_id": self.arc_action_id,
            "arc_worker_id": self.lima_request.get("trust_context", {}).get("worker_id"),
            "tenant_id": self.lima_request.get("trust_context", {}).get("tenant_id"),
            "dry_run": True,
            "status": (
                "lima_governed_preflight_completed"
                if self.lima_available
                else "lima_governed_preflight_fail_closed"
            ),
            "lima_available": self.lima_available,
            "lima_request_id": decision_dict.get("request_id"),
            "lima_decision_id": decision_dict.get("decision_id"),
            "lima_decision_status": decision_dict.get("status"),
            "lima_audit_event_id": dict(decision_dict.get("audit_event") or {}).get("event_id"),
            "runtime_authority_blocked": True,
            "runtime_execution_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
            "provider_model_routed": False,
            "tool_executed": False,
            "file_mutation_executed": False,
            "network_action_executed": False,
            "connector_invoked": False,
            "approval_token_issued": False,
            "proof_not_authority": True,
            "error": self.error,
        }

    @property
    def lima_response(self) -> dict[str, Any]:
        return _decision_to_dict(self.decision)

    @property
    def lima_audit_event(self) -> dict[str, Any]:
        return dict(self.lima_response.get("audit_event") or {})

    @property
    def lima_audit_lineage(self) -> dict[str, Any]:
        return {}


def call_lima_governed_preflight_for_arc_action(
    request: ArcActionRequest,
    *,
    lima_repo_path: str | Path | None = None,
    lima_runner: Callable[[dict[str, Any]], Any] | None = None,
) -> ArcLimaGovernedPreflightResult:
    """Submit an Arc action to LIMA's governed dry-run runtime seam."""

    try:
        lima_request = normalize_for_lima(request)
    except Exception as exc:
        return _fail_closed_result(
            request,
            request_id="malformed-arc-action",
            reason_codes=("malformed_arc_action_request", "fail_closed"),
            error=str(exc),
        )

    try:
        runner = lima_runner or _load_lima_runner(lima_repo_path)
        decision = runner(lima_request)
    except Exception as exc:
        return _fail_closed_result(
            request,
            request_id=lima_request["request_id"],
            lima_request=lima_request,
            reason_codes=("lima_unavailable", "fail_closed"),
            error=str(exc),
        )

    return ArcLimaGovernedPreflightResult(
        arc_action_id=request.action_id,
        lima_request=lima_request,
        decision=decision,
        lima_available=True,
    )


def normalize_for_lima(request: ArcActionRequest) -> dict[str, Any]:
    """Normalize an Arc action request into LIMA's ``GovernedRequest`` mapping."""

    _validate_arc_request(request)
    action_category = map_arc_action_category(request.action_kind)
    return {
        "request_id": request.action_id.strip(),
        "consumer": ARC_LIMA_CONSUMER,
        "surface": ARC_LIMA_SURFACE,
        "actor_id": request.operator_id.strip(),
        "normalized_request": request.payload_summary,
        "requested_action": request.action_kind.strip(),
        "action_category": action_category,
        "tool_name": _tool_name_for_category(action_category, request.action_kind),
        "tool_args": {
            "arc_action_id": request.action_id,
            "worker_id": request.worker_id,
            "tenant_id": request.tenant_id,
            "task_ref": request.task_ref,
            "arc_action_kind": request.action_kind,
        },
        "trust_context": {
            "tenant_id": request.tenant_id,
            "worker_id": request.worker_id,
            "task_ref": request.task_ref,
            "source_shell": "arc_bot_shell",
            "dry_run_only": True,
            "execution_requested": False,
            "side_effects_requested": False,
        },
        "evidence_refs": tuple(request.evidence_refs),
    }


def map_arc_action_category(action_kind: str) -> str:
    """Map Arc action words to LIMA Week 1 policy categories."""

    folded = str(action_kind or "").strip().lower().replace("_", " ")
    if not folded:
        return "unknown"

    if _contains_any(folded, ("shell", "terminal", "execute", "command", "ssh")):
        return "shell"
    if _contains_any(folded, ("robot", "drone", "iot", "physical")):
        return "physical_world"
    if _contains_any(folded, ("vault", "secret", "credential", "reveal")):
        return "credential_access"
    if _contains_any(folded, ("model", "provider", "route")):
        return "model_call"
    if _contains_any(folded, ("connector", "browser network")):
        return "connector_call"
    if _contains_any(folded, ("file", "delete", "mutate", "mutation")):
        return "file_mutation"
    if _contains_any(folded, ("send", "email", "slack", "calendar", "create", "write", "export")):
        return "external_write"
    if _contains_any(folded, ("draft", "summarize")):
        return "drafting"
    if "plan" in folded:
        return "planning"
    if _contains_any(folded, ("status", "read", "list", "show", "get", "preview", "intake", "extract")):
        return "read"
    return "unknown"


def record_lima_governed_preflight_projection(
    result: ArcLimaGovernedPreflightResult,
) -> dict[str, Any]:
    """Build a projection-only Arc evidence record for a LIMA dry-run result."""

    if not isinstance(result, ArcLimaGovernedPreflightResult):
        raise ArcLimaGovernedPreflightError(
            "result must be an ArcLimaGovernedPreflightResult"
        )

    response = result.response
    return {
        "record_type": "arc_lima_governed_preflight_projection_record",
        "projection_scope": "in_memory_evidence_only",
        "persistence_mode": "projection_only",
        "arc_action_id": result.arc_action_id,
        "source_record_type": response["record_type"],
        "dry_run": True,
        "status": "recorded_projection_only",
        "lima_request_id": response["lima_request_id"],
        "lima_decision_id": response["lima_decision_id"],
        "lima_audit_event_id": response["lima_audit_event_id"],
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "executable": False,
        "execution_allowed": False,
        "side_effects_allowed": False,
        "provider_model_routed": False,
        "tool_executed": False,
        "file_mutation_executed": False,
        "network_action_executed": False,
        "connector_invoked": False,
        "approval_token_issued": False,
        "proof_not_authority": True,
    }


def _validate_arc_request(request: ArcActionRequest) -> None:
    if not isinstance(request, ArcActionRequest):
        raise ArcLimaGovernedPreflightError("request must be an ArcActionRequest")

    required_fields = {
        "action_id": request.action_id,
        "operator_id": request.operator_id,
        "worker_id": request.worker_id,
        "tenant_id": request.tenant_id,
        "payload_summary": request.payload_summary,
        "action_kind": request.action_kind,
    }
    missing = [name for name, value in required_fields.items() if not str(value or "").strip()]
    if missing:
        raise ArcLimaGovernedPreflightError(
            f"Arc action request missing required fields: {', '.join(sorted(missing))}"
        )


def _load_lima_runner(
    lima_repo_path: str | Path | None,
) -> Callable[[dict[str, Any]], Any]:
    try:
        from lima.runtime import run_governed_request

        return run_governed_request
    except ModuleNotFoundError:
        _ensure_lima_repo_on_path(lima_repo_path)
        from lima.runtime import run_governed_request

        return run_governed_request


def _ensure_lima_repo_on_path(lima_repo_path: str | Path | None) -> None:
    repo_path = (
        Path(lima_repo_path)
        if lima_repo_path is not None
        else Path(__file__).resolve().parents[2] / "LIMA-AI-OS"
    ).resolve()
    if not (repo_path / "lima" / "runtime.py").exists():
        raise ArcLimaGovernedPreflightError(
            f"local LIMA checkout with lima.runtime not found at {repo_path}"
        )
    repo_text = str(repo_path)
    if repo_text not in sys.path:
        sys.path.insert(0, repo_text)


def _tool_name_for_category(action_category: str, action_kind: str) -> str:
    if action_category in {"read", "planning", "drafting"}:
        return "arc_status_preview"
    if action_category == "external_write":
        if "calendar" in action_kind.lower():
            return "calendar_create_event"
        if "slack" in action_kind.lower():
            return "send_slack_message"
        return "send_email"
    if action_category == "file_mutation":
        return "update_customer_record"
    if action_category == "credential_access":
        return "vault_reveal"
    if action_category == "shell":
        return "terminal_send"
    if action_category in {"model_call", "connector_call", "physical_world"}:
        return "execute_tool"
    return "unknown_arc_action"


def _fail_closed_result(
    request: Any,
    *,
    request_id: str,
    reason_codes: tuple[str, ...],
    error: str,
    lima_request: dict[str, Any] | None = None,
) -> ArcLimaGovernedPreflightResult:
    arc_action_id = getattr(request, "action_id", None) or request_id
    safe_request = lima_request or {
        "request_id": request_id,
        "consumer": ARC_LIMA_CONSUMER,
        "surface": ARC_LIMA_SURFACE,
        "actor_id": getattr(request, "operator_id", None) or "unknown",
        "normalized_request": getattr(request, "payload_summary", None) or "malformed Arc request",
        "requested_action": getattr(request, "action_kind", None) or "unknown",
        "action_category": "unknown",
        "tool_name": "unknown_arc_action",
        "tool_args": {},
        "trust_context": {
            "tenant_id": getattr(request, "tenant_id", None),
            "worker_id": getattr(request, "worker_id", None),
            "source_shell": "arc_bot_shell",
            "dry_run_only": True,
        },
        "evidence_refs": tuple(getattr(request, "evidence_refs", ()) or ()),
    }
    decision = ArcLimaFailClosedDecision(
        decision_id=f"arc-lima-fail-closed:{request_id}",
        request_id=request_id,
        consumer=ARC_LIMA_CONSUMER,
        reason_codes=reason_codes,
        audit_event={
            "event_id": f"arc-lima-audit:{request_id}",
            "request_id": request_id,
            "status": "denied",
            "reason_codes": reason_codes,
        },
        metadata={"error": error, "dry_run_only": True},
    )
    return ArcLimaGovernedPreflightResult(
        arc_action_id=str(arc_action_id),
        lima_request=safe_request,
        decision=decision,
        lima_available=False,
        error=error,
    )


def _decision_to_dict(decision: Any) -> dict[str, Any]:
    if hasattr(decision, "to_dict"):
        return dict(decision.to_dict())
    if hasattr(decision, "__dict__"):
        return dict(decision.__dict__)
    return {"status": "denied", "allowed": False, "reason_codes": ("unreadable_decision",)}


def _contains_any(value: str, needles: tuple[str, ...]) -> bool:
    return any(needle in value for needle in needles)
