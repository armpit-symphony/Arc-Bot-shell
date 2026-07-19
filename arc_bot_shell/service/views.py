"""Read-only operator projections for local Arc records."""

from __future__ import annotations

from datetime import datetime, timezone

from arc_bot_shell.approvals import JsonlApprovalStore
from arc_bot_shell.state import JsonlStateStore
from arc_bot_shell.tasks import JsonlTaskQueue

from .config import OperatorConfig


def list_tasks(config: OperatorConfig, limit: int) -> list[dict[str, object]]:
    return [
        record.to_dict()
        for record in JsonlTaskQueue(config.paths.task_queue_path).list_tasks(
            limit=limit
        )
    ]


def list_history(config: OperatorConfig, limit: int) -> list[dict[str, object]]:
    return [
        record.to_dict()
        for record in JsonlStateStore(config.paths.state_path).list_runs(limit=limit)
    ]


def list_approvals(config: OperatorConfig, limit: int) -> list[dict[str, object]]:
    return [
        record.to_dict()
        for record in JsonlApprovalStore(
            config.paths.approval_path
        ).list_approvals(limit=limit)
    ]


def list_evidence(config: OperatorConfig, limit: int) -> list[dict[str, object]]:
    if not config.paths.evidence_dir.exists():
        return []
    files = sorted(
        config.paths.evidence_dir.glob("*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return [
        {
            "path": str(item),
            "size_bytes": item.stat().st_size,
            "modified_at": datetime.fromtimestamp(
                item.stat().st_mtime, timezone.utc
            )
            .isoformat()
            .replace("+00:00", "Z"),
        }
        for item in files[:limit]
    ]
