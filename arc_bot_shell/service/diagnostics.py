"""Sanitized local diagnostics bundle generation."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import platform
import subprocess
import zipfile
from typing import Any, Mapping

from .config import OperatorConfig


SENSITIVE_KEYS = {
    "authorization",
    "credential",
    "credentials",
    "password",
    "prompt",
    "secret",
    "token",
    "output_text",
}


def redact_diagnostics(value: Any) -> Any:
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(sensitive in lowered for sensitive in SENSITIVE_KEYS):
                sanitized[str(key)] = "[REDACTED]"
            else:
                sanitized[str(key)] = redact_diagnostics(item)
        return sanitized
    if isinstance(value, list):
        return [redact_diagnostics(item) for item in value]
    return value


def _command_version(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = (completed.stdout or completed.stderr).strip()
    return output.splitlines()[0] if output else None


def create_diagnostics_bundle(
    config: OperatorConfig,
    *,
    doctor_report: Mapping[str, object],
    health_report: Mapping[str, object],
    recent_log_lines: int = 200,
) -> str:
    paths = config.paths
    paths.diagnostics_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_path = paths.diagnostics_dir / f"arc-diagnostics-{stamp}.zip"
    safe_config = redact_diagnostics(config.to_dict())
    manifest = (
        json.loads(paths.manifest_path.read_text(encoding="utf-8-sig"))
        if paths.manifest_path.exists()
        else {}
    )
    startup_state = (
        json.loads(paths.startup_state_path.read_text(encoding="utf-8-sig"))
        if paths.startup_state_path.exists()
        else {"registered": False}
    )
    log_lines: list[str] = []
    if paths.service_log_path.exists():
        log_lines = paths.service_log_path.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines()[-recent_log_lines:]
    metadata = {
        "python_version": platform.python_version(),
        "ollama_version": _command_version(["ollama", "--version"]),
        "configured_model": config.model,
        "evidence_bodies_included": False,
        "task_payloads_included": False,
        "environment_included": False,
    }
    entries = {
        "config.json": safe_config,
        "installation-manifest.json": redact_diagnostics(manifest),
        "doctor.json": redact_diagnostics(dict(doctor_report)),
        "health.json": redact_diagnostics(dict(health_report)),
        "startup-state.json": redact_diagnostics(startup_state),
        "versions.json": metadata,
    }
    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries.items():
            archive.writestr(
                name,
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
            )
        archive.writestr("recent-service.log", "\n".join(log_lines) + "\n")
    return str(bundle_path)
