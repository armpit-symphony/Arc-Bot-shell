"""Install-path and operator configuration contracts for Arc v0.11."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from typing import Any, Mapping

from arc_bot_shell.guardian import DEFAULT_GUARDIAN_CONTRACT_REFERENCE
from arc_bot_shell.lima import (
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_URL,
    LIMA_PINNED_COMMIT,
    LIMA_PINNED_REFERENCE,
    normalize_loopback_ollama_url,
    resolve_ollama_model,
)


ARC_STARTUP_TASK_NAME = "SparkPitLabs-ArcBot"
ARC_V0_10_ROLLBACK_TAG = "arc-harness-shell-v0.10"
ARC_V0_10_COMMIT = "fa1e93ff18203218a863b679f3d3608aa46bd5a4"
ARC_V0_11_VERSION = "0.11"
CONFIG_SCHEMA_VERSION = "arc-windows-operator-config-v1"


def default_install_root(environ: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    local_app_data = env.get("LOCALAPPDATA", "").strip()
    if not local_app_data:
        raise ValueError("LOCALAPPDATA is required for the default per-user install")
    return Path(local_app_data) / "SparkPitLabs" / "ArcBot"


def _is_relative_to(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
    except ValueError:
        return False
    return True


@dataclass(frozen=True)
class ArcInstallPaths:
    """All mutable operator paths, rooted outside the Arc source checkout."""

    root: Path
    app: Path
    venv: Path
    data: Path
    logs: Path
    config: Path
    releases: Path
    current: Path
    backups: Path
    manager: Path

    @classmethod
    def from_root(cls, root: Path) -> "ArcInstallPaths":
        resolved = root.expanduser().resolve()
        return cls(
            root=resolved,
            app=resolved / "app",
            venv=resolved / "venv",
            data=resolved / "data",
            logs=resolved / "logs",
            config=resolved / "config",
            releases=resolved / "releases",
            current=resolved / "current",
            backups=resolved / "backups",
            manager=resolved / "manager",
        )

    @property
    def config_path(self) -> Path:
        return self.config / "arc-config.json"

    @property
    def manifest_path(self) -> Path:
        return self.config / "installation-manifest.json"

    @property
    def manifest_history_path(self) -> Path:
        return self.config / "installation-history.jsonl"

    @property
    def pid_path(self) -> Path:
        return self.data / "service" / "arc-service.pid.json"

    @property
    def stop_request_path(self) -> Path:
        return self.data / "service" / "arc-service.stop.json"

    @property
    def health_snapshot_path(self) -> Path:
        return self.data / "service" / "health.json"

    @property
    def startup_state_path(self) -> Path:
        return self.config / "startup-state.json"

    @property
    def task_queue_path(self) -> Path:
        return self.data / "tasks" / "tasks.jsonl"

    @property
    def state_path(self) -> Path:
        return self.data / "state" / "runs.jsonl"

    @property
    def approval_path(self) -> Path:
        return self.data / "approvals" / "approvals.jsonl"

    @property
    def evidence_dir(self) -> Path:
        return self.data / "evidence"

    @property
    def service_log_path(self) -> Path:
        return self.logs / "service.jsonl"

    @property
    def audit_log_path(self) -> Path:
        return self.logs / "operator-audit.jsonl"

    @property
    def diagnostics_dir(self) -> Path:
        return self.data / "diagnostics"

    def ensure(self) -> None:
        for path in (
            self.root,
            self.app,
            self.venv,
            self.data,
            self.logs,
            self.config,
            self.releases,
            self.current,
            self.backups,
            self.manager,
            self.pid_path.parent,
            self.task_queue_path.parent,
            self.state_path.parent,
            self.approval_path.parent,
            self.evidence_dir,
            self.diagnostics_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def assert_data_separated_from(self, source_root: Path) -> None:
        source = source_root.resolve()
        if _is_relative_to(self.data.resolve(), source):
            raise ValueError("Arc operator data must be outside the source checkout")


@dataclass(frozen=True)
class OperatorConfig:
    """Sanitized configuration consumed by the launcher and local service."""

    install_root: str
    app_root: str
    python_executable: str
    guardian_mode: str = "guardian_core"
    guardian_path: str | None = None
    guardian_reference: str = DEFAULT_GUARDIAN_CONTRACT_REFERENCE
    lima_reference: str = LIMA_PINNED_REFERENCE
    lima_commit: str = LIMA_PINNED_COMMIT
    ollama_url: str = DEFAULT_OLLAMA_URL
    model: str = DEFAULT_OLLAMA_MODEL
    installed_version: str = ARC_V0_11_VERSION
    installed_tag: str | None = None
    installed_commit: str | None = None
    startup_task_name: str = ARC_STARTUP_TASK_NAME
    startup_registered: bool = False
    health_interval_seconds: float = 60.0
    schema_version: str = CONFIG_SCHEMA_VERSION

    def __post_init__(self) -> None:
        root = Path(self.install_root).expanduser().resolve()
        app = Path(self.app_root).expanduser().resolve()
        python = Path(self.python_executable).expanduser().resolve()
        if not root.is_absolute() or not app.is_absolute() or not python.is_absolute():
            raise ValueError("Arc operator paths must be absolute")
        if self.guardian_mode != "guardian_core":
            raise ValueError("v0.11 requires guardian_mode=guardian_core")
        if self.guardian_reference != DEFAULT_GUARDIAN_CONTRACT_REFERENCE:
            raise ValueError("Guardian reference does not match the v0.10 trust baseline")
        if self.lima_reference != LIMA_PINNED_REFERENCE:
            raise ValueError("LIMA reference does not match the v0.10 trust baseline")
        if self.lima_commit != LIMA_PINNED_COMMIT:
            raise ValueError("LIMA commit does not match the v0.10 trust baseline")
        normalize_loopback_ollama_url(self.ollama_url)
        resolve_ollama_model(self.model)
        if not 1 <= float(self.health_interval_seconds) <= 3600:
            raise ValueError("health_interval_seconds must be between 1 and 3600")
        if self.startup_task_name != ARC_STARTUP_TASK_NAME:
            raise ValueError("unsupported Arc startup task name")

    @property
    def paths(self) -> ArcInstallPaths:
        return ArcInstallPaths.from_root(Path(self.install_root))

    def environment(self) -> dict[str, str]:
        env = {
            "ARC_GUARDIAN_MODE": "guardian_core",
            "ARC_GUARDIAN_REFERENCE": self.guardian_reference,
            "ARC_OLLAMA_URL": normalize_loopback_ollama_url(self.ollama_url),
            "ARC_OLLAMA_MODEL": resolve_ollama_model(self.model),
        }
        if self.guardian_path:
            env["ARC_GUARDIAN_PATH"] = str(
                Path(self.guardian_path).expanduser().resolve()
            )
        return env

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OperatorConfig":
        allowed = set(cls.__dataclass_fields__)
        values = {key: value for key, value in payload.items() if key in allowed}
        return cls(**values)

    @classmethod
    def load(cls, path: Path) -> "OperatorConfig":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError("Arc operator config must be a JSON object")
        return cls.from_dict(payload)

    def write(self, path: Path | None = None) -> Path:
        target = path or self.paths.config_path
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)
        return target
