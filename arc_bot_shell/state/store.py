"""Local JSONL-backed run history for Arc Harness Shell."""

from __future__ import annotations

import json
from pathlib import Path

from .models import StateRunRecord


def default_state_dir(repo_root: Path) -> Path:
    return repo_root / "artifacts" / "state"


def default_state_path(repo_root: Path) -> Path:
    return default_state_dir(repo_root) / "runs.jsonl"


class JsonlStateStore:
    """Append-only JSONL state store."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, record: StateRunRecord) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record.to_dict(), sort_keys=True))
            handle.write("\n")
        return self.path

    def exists(self) -> bool:
        return self.path.exists()

    def list_runs(self, *, limit: int | None = None) -> list[StateRunRecord]:
        if not self.path.exists():
            return []
        records: list[StateRunRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                payload = json.loads(stripped)
                if isinstance(payload, dict):
                    records.append(StateRunRecord.from_dict(payload))
        records.reverse()
        if limit is not None:
            return records[:limit]
        return records

    def get_run(self, run_id: str) -> StateRunRecord | None:
        for record in self.list_runs():
            if record.run_id == run_id:
                return record
        return None
