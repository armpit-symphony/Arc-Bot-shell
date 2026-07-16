"""State record contracts for Arc Harness Shell."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class StateRunRecord:
    """One persisted harness run record."""

    run_id: str
    action_id: str
    task_ref: str
    requested_action: str
    guardian_decision_id: str
    guardian_status: str
    blocked_reason: str | None
    runtime_adapter: str
    runtime_called: bool
    result_status: str
    evidence_path: str
    created_at: str
    model_preview_called: bool = False
    model_preview_adapter: str | None = None
    model_name: str | None = None
    guardian_mode: str = "fail_closed"
    guardian_reason: str | None = None
    guardian_allowed: bool | None = None
    guardian_requires_approval: bool | None = None
    guardian_contract_reference: str | None = None
    eligible_for_lima: bool = False
    lima_called: bool = False
    ollama_called: bool = False

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "StateRunRecord":
        return cls(
            run_id=str(payload["run_id"]),
            action_id=str(payload["action_id"]),
            task_ref=str(payload["task_ref"]),
            requested_action=str(payload["requested_action"]),
            guardian_decision_id=str(payload["guardian_decision_id"]),
            guardian_status=str(payload["guardian_status"]),
            blocked_reason=(
                None
                if payload.get("blocked_reason") is None
                else str(payload["blocked_reason"])
            ),
            runtime_adapter=str(payload["runtime_adapter"]),
            runtime_called=bool(payload["runtime_called"]),
            result_status=str(payload["result_status"]),
            evidence_path=str(payload["evidence_path"]),
            created_at=str(payload["created_at"]),
            model_preview_called=bool(payload.get("model_preview_called", False)),
            model_preview_adapter=(
                None
                if payload.get("model_preview_adapter") is None
                else str(payload["model_preview_adapter"])
            ),
            model_name=(
                None
                if payload.get("model_name") is None
                else str(payload["model_name"])
            ),
            guardian_mode=str(payload.get("guardian_mode", "fail_closed")),
            guardian_reason=(
                None
                if payload.get("guardian_reason") is None
                else str(payload["guardian_reason"])
            ),
            guardian_allowed=(
                None
                if payload.get("guardian_allowed") is None
                else bool(payload["guardian_allowed"])
            ),
            guardian_requires_approval=(
                None
                if payload.get("guardian_requires_approval") is None
                else bool(payload["guardian_requires_approval"])
            ),
            guardian_contract_reference=(
                None
                if payload.get("guardian_contract_reference") is None
                else str(payload["guardian_contract_reference"])
            ),
            eligible_for_lima=bool(payload.get("eligible_for_lima", False)),
            lima_called=bool(
                payload.get("lima_called", payload.get("runtime_called", False))
            ),
            ollama_called=bool(payload.get("ollama_called", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
