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
                None if payload.get("blocked_reason") is None else str(payload["blocked_reason"])
            ),
            runtime_adapter=str(payload["runtime_adapter"]),
            runtime_called=bool(payload["runtime_called"]),
            result_status=str(payload["result_status"]),
            evidence_path=str(payload["evidence_path"]),
            created_at=str(payload["created_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
