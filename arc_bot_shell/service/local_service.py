"""Non-listening managed Arc background process."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Callable, Iterator, Mapping

from arc_bot_shell.health import build_health_report

from .config import OperatorConfig
from .pidfile import (
    DuplicateServiceError,
    ManagedProcessRecord,
    acquire_pidfile,
    process_is_alive,
    read_pidfile,
    release_pidfile,
    stop_requested,
    write_stop_request,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _append_jsonl(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(dict(payload), sort_keys=True))
        handle.write("\n")


def _write_json_atomic(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


@contextmanager
def configured_environment(config: OperatorConfig) -> Iterator[None]:
    previous: dict[str, str | None] = {}
    try:
        for key, value in config.environment().items():
            previous[key] = os.environ.get(key)
            os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@dataclass(frozen=True)
class ServiceStatus:
    running: bool
    pid: int | None
    started_at: str | None
    stale_pid_recovered: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def status_local_service(config: OperatorConfig) -> ServiceStatus:
    paths = config.paths
    record = read_pidfile(paths.pid_path)
    if record is None:
        if paths.pid_path.exists():
            paths.pid_path.unlink(missing_ok=True)
            return ServiceStatus(False, None, None, stale_pid_recovered=True)
        return ServiceStatus(False, None, None)
    if not process_is_alive(record.pid):
        paths.pid_path.unlink(missing_ok=True)
        paths.stop_request_path.unlink(missing_ok=True)
        return ServiceStatus(False, None, None, stale_pid_recovered=True)
    return ServiceStatus(True, record.pid, record.started_at)


def build_service_health_snapshot(config: OperatorConfig) -> dict[str, object]:
    with configured_environment(config):
        report = build_health_report(Path(config.app_root))
    return {
        "captured_at": _utc_now(),
        "service_listening": False,
        "network_bind": None,
        "health": report,
    }


def run_local_service(
    config: OperatorConfig,
    *,
    once: bool = False,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> int:
    paths = config.paths
    paths.ensure()
    record = ManagedProcessRecord.create(command="arc-local-service")
    acquire_pidfile(paths.pid_path, record)
    paths.stop_request_path.unlink(missing_ok=True)
    stopping = False

    def request_shutdown(signum: int, frame: object) -> None:
        del signum, frame
        nonlocal stopping
        stopping = True

    previous_sigterm = signal.signal(signal.SIGTERM, request_shutdown)
    previous_sigint = signal.signal(signal.SIGINT, request_shutdown)
    _append_jsonl(
        paths.service_log_path,
        {
            "event": "service_started",
            "at": _utc_now(),
            "pid": record.pid,
            "listening": False,
        },
    )
    try:
        while not stopping:
            _write_json_atomic(
                paths.health_snapshot_path,
                build_service_health_snapshot(config),
            )
            if once or stop_requested(paths.stop_request_path, record):
                break
            remaining = float(config.health_interval_seconds)
            while remaining > 0 and not stopping:
                if stop_requested(paths.stop_request_path, record):
                    stopping = True
                    break
                interval = min(0.25, remaining)
                sleep_fn(interval)
                remaining -= interval
    finally:
        release_pidfile(paths.pid_path, record.token)
        paths.stop_request_path.unlink(missing_ok=True)
        _append_jsonl(
            paths.service_log_path,
            {"event": "service_stopped", "at": _utc_now(), "pid": record.pid},
        )
        signal.signal(signal.SIGTERM, previous_sigterm)
        signal.signal(signal.SIGINT, previous_sigint)
    return 0


def start_local_service(
    config: OperatorConfig,
    *,
    wait_seconds: float = 10.0,
) -> ServiceStatus:
    current = status_local_service(config)
    if current.running:
        raise DuplicateServiceError(
            f"Arc local service is already running with PID {current.pid}"
        )
    paths = config.paths
    paths.ensure()
    command = [
        config.python_executable,
        "-m",
        "arc_bot_shell.service.local_service",
        "run",
        "--config",
        str(paths.config_path),
    ]
    creationflags = 0
    if os.name == "nt":
        creationflags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
    with paths.service_log_path.open("a", encoding="utf-8") as log_handle:
        subprocess.Popen(
            command,
            cwd=config.app_root,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=log_handle,
            close_fds=True,
            creationflags=creationflags,
            env={**os.environ, **config.environment()},
        )
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        status = status_local_service(config)
        if status.running:
            return status
        time.sleep(0.1)
    raise RuntimeError("Arc local service did not become ready")


def stop_local_service(
    config: OperatorConfig,
    *,
    wait_seconds: float = 15.0,
) -> ServiceStatus:
    paths = config.paths
    record = read_pidfile(paths.pid_path)
    if record is None:
        return status_local_service(config)
    if not process_is_alive(record.pid):
        paths.pid_path.unlink(missing_ok=True)
        paths.stop_request_path.unlink(missing_ok=True)
        return ServiceStatus(False, None, None, stale_pid_recovered=True)
    write_stop_request(paths.stop_request_path, record)
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        status = status_local_service(config)
        if not status.running:
            return status
        time.sleep(0.1)
    raise RuntimeError(
        "Arc local service did not stop; no process was force-terminated"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the local Arc service.")
    parser.add_argument("command", choices=("run", "start", "stop", "status"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--once", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = OperatorConfig.load(args.config)
    if args.command == "run":
        return run_local_service(config, once=args.once)
    if args.command == "start":
        payload = start_local_service(config).to_dict()
    elif args.command == "stop":
        payload = stop_local_service(config).to_dict()
    else:
        payload = status_local_service(config).to_dict()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
