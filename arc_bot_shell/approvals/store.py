"""JSONL-backed local approval queue for Arc Harness Shell."""

from __future__ import annotations

import json
from pathlib import Path

from .models import APPROVAL_STATUSES, ApprovalRecord


def default_approval_dir(repo_root: Path) -> Path:
    return repo_root / "artifacts" / "approvals"


def default_approval_path(repo_root: Path) -> Path:
    return default_approval_dir(repo_root) / "approvals.jsonl"


class JsonlApprovalStore:
    """Local JSONL approval queue with replace-on-update semantics."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def exists(self) -> bool:
        return self.path.exists()

    def _read_all(self) -> list[ApprovalRecord]:
        if not self.path.exists():
            return []
        records: list[ApprovalRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                payload = json.loads(stripped)
                if isinstance(payload, dict):
                    records.append(ApprovalRecord.from_dict(payload))
        return records

    def _write_all(self, records: list[ApprovalRecord]) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record.to_dict(), sort_keys=True))
                handle.write("\n")
        return self.path

    def append(self, record: ApprovalRecord) -> Path:
        records = self._read_all()
        records.append(record)
        return self._write_all(records)

    def upsert(self, record: ApprovalRecord) -> Path:
        records = self._read_all()
        for index, existing in enumerate(records):
            if existing.approval_id == record.approval_id:
                records[index] = record
                return self._write_all(records)
        records.append(record)
        return self._write_all(records)

    def list_approvals(
        self,
        *,
        status: str | None = None,
        task_id: str | None = None,
        limit: int | None = None,
    ) -> list[ApprovalRecord]:
        records = self._read_all()
        records.reverse()
        if status is not None:
            records = [record for record in records if record.status == status]
        if task_id is not None:
            records = [record for record in records if record.task_id == task_id]
        if limit is not None:
            return records[:limit]
        return records

    def get_approval(self, approval_id: str) -> ApprovalRecord | None:
        for record in self.list_approvals():
            if record.approval_id == approval_id:
                return record
        return None

    def counts_by_status(self) -> dict[str, int]:
        counts = {status: 0 for status in APPROVAL_STATUSES}
        for record in self._read_all():
            counts[record.status] = counts.get(record.status, 0) + 1
        return counts
