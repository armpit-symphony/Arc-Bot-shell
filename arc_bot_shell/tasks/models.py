"""Task queue models for Arc Harness Shell."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


TASK_STATUSES = (
    "queued",
    "running",
    "completed",
    "blocked",
    "failed",
)

TaskStatus = Literal[
    "queued",
    "running",
    "completed",
    "blocked",
    "failed",
]


@dataclass(frozen=True)
class TaskRecord:
    """One local Arc task queue record."""

    task_id: str
    action_id: str
    task_ref: str
    requested_action: str
    payload_summary: str
    source: str
    status: TaskStatus
    created_at: str
    updated_at: str
    latest_run_id: str | None = None
    latest_guardian_status: str | None = None
    latest_result_status: str | None = None
    latest_evidence_path: str | None = None
    latest_error_message: str | None = None
    latest_approval_id: str | None = None
    latest_approval_status: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskRecord":
        return cls(
            task_id=str(payload["task_id"]),
            action_id=str(payload["action_id"]),
            task_ref=str(payload["task_ref"]),
            requested_action=str(payload["requested_action"]),
            payload_summary=str(payload["payload_summary"]),
            source=str(payload["source"]),
            status=str(payload["status"]),  # type: ignore[arg-type]
            created_at=str(payload["created_at"]),
            updated_at=str(payload["updated_at"]),
            latest_run_id=None if payload.get("latest_run_id") is None else str(payload["latest_run_id"]),
            latest_guardian_status=(
                None
                if payload.get("latest_guardian_status") is None
                else str(payload["latest_guardian_status"])
            ),
            latest_result_status=(
                None
                if payload.get("latest_result_status") is None
                else str(payload["latest_result_status"])
            ),
            latest_evidence_path=(
                None
                if payload.get("latest_evidence_path") is None
                else str(payload["latest_evidence_path"])
            ),
            latest_error_message=(
                None
                if payload.get("latest_error_message") is None
                else str(payload["latest_error_message"])
            ),
            latest_approval_id=(
                None
                if payload.get("latest_approval_id") is None
                else str(payload["latest_approval_id"])
            ),
            latest_approval_status=(
                None
                if payload.get("latest_approval_status") is None
                else str(payload["latest_approval_status"])
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
