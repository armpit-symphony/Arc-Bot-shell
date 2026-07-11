"""Approval queue models for Arc Harness Shell."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


APPROVAL_STATUSES = (
    "pending",
    "approved",
    "denied",
)

ApprovalStatus = Literal[
    "pending",
    "approved",
    "denied",
]


@dataclass(frozen=True)
class ApprovalRecord:
    """One local operator approval/denial record.

    Approval records are evidence/state records only in v0.6. They never grant
    connector, file, browser, network, device, robotics, credential, or office
    mutation execution authority.
    """

    approval_id: str
    task_id: str
    run_id: str
    action_id: str
    task_ref: str
    requested_action: str
    guardian_decision_id: str
    guardian_status: str
    blocked_reason: str | None
    evidence_path: str
    status: ApprovalStatus
    created_at: str
    updated_at: str
    operator_id: str | None = None
    decision_reason: str | None = None
    decided_at: str | None = None
    execution_allowed: bool = False
    execution_status: str = "not_executable_in_v0_6"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ApprovalRecord":
        return cls(
            approval_id=str(payload["approval_id"]),
            task_id=str(payload["task_id"]),
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
            evidence_path=str(payload["evidence_path"]),
            status=str(payload["status"]),  # type: ignore[arg-type]
            created_at=str(payload["created_at"]),
            updated_at=str(payload["updated_at"]),
            operator_id=None if payload.get("operator_id") is None else str(payload["operator_id"]),
            decision_reason=(
                None
                if payload.get("decision_reason") is None
                else str(payload["decision_reason"])
            ),
            decided_at=None if payload.get("decided_at") is None else str(payload["decided_at"]),
            execution_allowed=bool(payload.get("execution_allowed", False)),
            execution_status=str(payload.get("execution_status", "not_executable_in_v0_6")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
