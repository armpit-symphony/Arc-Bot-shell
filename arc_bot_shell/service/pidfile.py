"""Token-bound PID lifecycle helpers for the managed Arc process."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid


class DuplicateServiceError(RuntimeError):
    """Raised when a live managed Arc service already owns the PID file."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ManagedProcessRecord:
    pid: int
    token: str
    started_at: str
    command: str

    @classmethod
    def create(cls, *, pid: int | None = None, command: str) -> "ManagedProcessRecord":
        return cls(
            pid=os.getpid() if pid is None else pid,
            token=uuid.uuid4().hex,
            started_at=_utc_now(),
            command=command,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ManagedProcessRecord":
        return cls(
            pid=int(payload["pid"]),
            token=str(payload["token"]),
            started_at=str(payload["started_at"]),
            command=str(payload["command"]),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.restype = ctypes.c_void_p
        handle = kernel32.OpenProcess(
            process_query_limited_information,
            False,
            pid,
        )
        if handle:
            exit_code = ctypes.c_ulong()
            queried = kernel32.GetExitCodeProcess(
                handle,
                ctypes.byref(exit_code),
            )
            kernel32.CloseHandle(handle)
            return bool(queried) and exit_code.value == 259
        return ctypes.get_last_error() == 5
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError, PermissionError):
        return False
    return True


def read_pidfile(path: Path) -> ManagedProcessRecord | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            return None
        return ManagedProcessRecord.from_dict(payload)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError):
        return None


def acquire_pidfile(path: Path, record: ManagedProcessRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_pidfile(path)
    if existing is not None and process_is_alive(existing.pid):
        raise DuplicateServiceError(
            f"Arc local service is already running with PID {existing.pid}"
        )
    if path.exists():
        path.unlink()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(
            descriptor,
            (json.dumps(record.to_dict(), sort_keys=True) + "\n").encode("utf-8"),
        )
    finally:
        os.close(descriptor)


def release_pidfile(path: Path, token: str) -> bool:
    record = read_pidfile(path)
    if record is None or record.token != token:
        return False
    path.unlink(missing_ok=True)
    return True


def write_stop_request(path: Path, record: ManagedProcessRecord) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            {"pid": record.pid, "token": record.token, "requested_at": _utc_now()},
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def stop_requested(path: Path, record: ManagedProcessRecord) -> bool:
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        isinstance(payload, dict)
        and payload.get("pid") == record.pid
        and payload.get("token") == record.token
    )
