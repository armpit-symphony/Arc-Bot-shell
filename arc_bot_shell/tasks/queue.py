"""JSONL-backed local task queue for Arc Harness Shell."""

from __future__ import annotations

import json
from pathlib import Path

from .models import TASK_STATUSES, TaskRecord


def default_task_queue_dir(repo_root: Path) -> Path:
    return repo_root / "artifacts" / "tasks"


def default_task_queue_path(repo_root: Path) -> Path:
    return default_task_queue_dir(repo_root) / "tasks.jsonl"


class JsonlTaskQueue:
    """Local JSONL task queue with replace-on-update semantics."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def exists(self) -> bool:
        return self.path.exists()

    def _read_all(self) -> list[TaskRecord]:
        if not self.path.exists():
            return []
        records: list[TaskRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                payload = json.loads(stripped)
                if isinstance(payload, dict):
                    records.append(TaskRecord.from_dict(payload))
        return records

    def _write_all(self, records: list[TaskRecord]) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record.to_dict(), sort_keys=True))
                handle.write("\n")
        return self.path

    def append(self, record: TaskRecord) -> Path:
        records = self._read_all()
        records.append(record)
        return self._write_all(records)

    def upsert(self, record: TaskRecord) -> Path:
        records = self._read_all()
        for index, existing in enumerate(records):
            if existing.task_id == record.task_id:
                records[index] = record
                return self._write_all(records)
        records.append(record)
        return self._write_all(records)

    def list_tasks(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[TaskRecord]:
        records = self._read_all()
        records.reverse()
        if status is not None:
            records = [record for record in records if record.status == status]
        if limit is not None:
            return records[:limit]
        return records

    def get_task(self, task_id: str) -> TaskRecord | None:
        for record in self.list_tasks():
            if record.task_id == task_id:
                return record
        return None

    def counts_by_status(self) -> dict[str, int]:
        counts = {status: 0 for status in TASK_STATUSES}
        for record in self._read_all():
            counts[record.status] = counts.get(record.status, 0) + 1
        return counts
