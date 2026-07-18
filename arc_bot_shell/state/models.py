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
    lima_entrypoint: str | None = None
    lima_result_status: str | None = None
    executor_called: bool = False
    network_called: bool = False
    credentials_used: bool = False
    guardian_called: bool = True
    executor_kind: str | None = None
    executor_name: str | None = None
    executor_call_count: int = 0
    endpoint: str | None = None
    network_scope: str | None = None
    external_side_effects: bool = False
    duration_ms: int | None = None
    output_reference: str | None = None
    error_category: str | None = None
    lima_input_guardian_decision_id: str | None = None
    executor_input_guardian_decision_id: str | None = None
    execution_allowed: bool = False

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
            lima_entrypoint=(
                None
                if payload.get("lima_entrypoint") is None
                else str(payload["lima_entrypoint"])
            ),
            lima_result_status=(
                None
                if payload.get("lima_result_status") is None
                else str(payload["lima_result_status"])
            ),
            executor_called=bool(payload.get("executor_called", False)),
            network_called=bool(payload.get("network_called", False)),
            credentials_used=bool(payload.get("credentials_used", False)),
            guardian_called=bool(payload.get("guardian_called", True)),
            executor_kind=(
                None
                if payload.get("executor_kind") is None
                else str(payload["executor_kind"])
            ),
            executor_name=(
                None
                if payload.get("executor_name") is None
                else str(payload["executor_name"])
            ),
            executor_call_count=int(payload.get("executor_call_count", 0)),
            endpoint=(
                None
                if payload.get("endpoint") is None
                else str(payload["endpoint"])
            ),
            network_scope=(
                None
                if payload.get("network_scope") is None
                else str(payload["network_scope"])
            ),
            external_side_effects=bool(
                payload.get("external_side_effects", False)
            ),
            duration_ms=(
                None
                if payload.get("duration_ms") is None
                else int(payload["duration_ms"])
            ),
            output_reference=(
                None
                if payload.get("output_reference") is None
                else str(payload["output_reference"])
            ),
            error_category=(
                None
                if payload.get("error_category") is None
                else str(payload["error_category"])
            ),
            lima_input_guardian_decision_id=(
                None
                if payload.get("lima_input_guardian_decision_id") is None
                else str(payload["lima_input_guardian_decision_id"])
            ),
            executor_input_guardian_decision_id=(
                None
                if payload.get("executor_input_guardian_decision_id") is None
                else str(payload["executor_input_guardian_decision_id"])
            ),
            execution_allowed=bool(payload.get("execution_allowed", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
