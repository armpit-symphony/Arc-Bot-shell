"""LIMA runtime ports with explicit configuration resolution."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterator, Literal, Protocol

from arc_bot_shell.contracts import ArcActionRequest, GuardianDecision, LimaRuntimeResult


class LimaRuntimeUnavailableError(RuntimeError):
    """Raised when the configured LIMA runtime cannot be used."""


class LimaRuntimePort(Protocol):
    """Protocol for runtime adapters used by the Arc harness."""

    adapter_name: str

    def invoke(
        self,
        request: ArcActionRequest,
        decision: GuardianDecision,
    ) -> LimaRuntimeResult:
        """Execute a preview-safe runtime action."""


@dataclass(frozen=True)
class ResolvedLimaImport:
    """Resolved LIMA import source."""

    source: Literal["explicit_path", "workspace_lock", "installed_package"]
    checkout_path: Path | None = None


def load_workspace_lock(repo_root: Path) -> dict[str, Any] | None:
    lock_path = repo_root / "workspace.lock.json"
    if not lock_path.exists():
        return None
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LimaRuntimeUnavailableError("workspace.lock.json must contain an object")
    return payload


def _resolve_lima_path_from_lock(repo_root: Path) -> Path | None:
    payload = load_workspace_lock(repo_root)
    if payload is None:
        return None
    dependencies = payload.get("dependencies", [])
    if not isinstance(dependencies, list):
        raise LimaRuntimeUnavailableError("workspace.lock.json dependencies must be a list")
    for item in dependencies:
        if not isinstance(item, dict):
            continue
        if item.get("name") == "LIMA-AI-OS":
            raw_path = item.get("path")
            if isinstance(raw_path, str) and raw_path:
                return (repo_root / raw_path).resolve()
    return None


def _validate_lima_checkout(path: Path) -> Path:
    adapter_file = path / "lima" / "adapters" / "__init__.py"
    if not adapter_file.exists():
        raise LimaRuntimeUnavailableError(
            f"configured LIMA checkout is missing the public lima.adapters package: {path}"
        )
    return path


@contextmanager
def _temporary_sys_path(path: Path | None) -> Iterator[None]:
    if path is None:
        yield
        return
    text = str(path)
    inserted = False
    if text not in sys.path:
        sys.path.insert(0, text)
        inserted = True
    try:
        yield
    finally:
        if inserted:
            sys.path.remove(text)


@dataclass
class FakeLimaRuntimePort:
    """Deterministic local fake runtime for CI and smoke tests."""

    adapter_name: str = "fake"

    def invoke(
        self,
        request: ArcActionRequest,
        decision: GuardianDecision,
    ) -> LimaRuntimeResult:
        output = {
            "consumer": "arc_bot_shell",
            "mode": "fake",
            "action_name": request.action_name,
            "task_ref": request.task_ref,
            "guardian_status": decision.status,
            "preview_text": f"Preview ready for {request.action_name}: {request.summary}",
        }
        return LimaRuntimeResult(
            runtime_adapter=self.adapter_name,
            result_status="preview_completed",
            output=output,
        )


@dataclass
class DisabledLimaRuntimePort:
    """Fail-closed runtime fallback."""

    reason: str = "LIMA runtime is disabled"
    adapter_name: str = "disabled"

    def invoke(
        self,
        request: ArcActionRequest,
        decision: GuardianDecision,
    ) -> LimaRuntimeResult:
        raise LimaRuntimeUnavailableError(self.reason)


@dataclass
class LocalLimaImportRuntimePort:
    """LIMA runtime port backed by the public lima.adapters surface."""

    repo_root: Path
    configured_path: Path | None = None
    env_var_name: str = "ARC_LIMA_PATH"
    adapter_name: str = "local_import"

    def resolve_lima_import(self) -> ResolvedLimaImport:
        if self.configured_path is not None:
            return ResolvedLimaImport(
                source="explicit_path",
                checkout_path=_validate_lima_checkout(self.configured_path.resolve()),
            )

        env_path = os.environ.get(self.env_var_name)
        if env_path:
            return ResolvedLimaImport(
                source="explicit_path",
                checkout_path=_validate_lima_checkout(Path(env_path).resolve()),
            )

        locked_path = _resolve_lima_path_from_lock(self.repo_root)
        if locked_path is not None:
            return ResolvedLimaImport(
                source="workspace_lock",
                checkout_path=_validate_lima_checkout(locked_path),
            )

        try:
            importlib.import_module("lima.adapters")
        except Exception as exc:
            raise LimaRuntimeUnavailableError(
                "LIMA runtime is not installed and no explicit ARC_LIMA_PATH or workspace.lock.json path was provided"
            ) from exc
        return ResolvedLimaImport(source="installed_package", checkout_path=None)

    def build_runtime_input(
        self,
        request: ArcActionRequest,
        decision: GuardianDecision,
    ) -> dict[str, Any]:
        action_category = "informational"
        if request.action_name == "arc.classify_task_packet":
            action_category = "classification"
        elif request.action_name == "arc.preview_operator_response":
            action_category = "drafting"
        elif request.action_name == "arc.generate_evidence_packet":
            action_category = "evidence"
        elif request.action_name == "arc.mark_task_blocked":
            action_category = "planning"
        return {
            "input_id": request.action_id,
            "consumer": "arc_bot_shell",
            "actor_id": request.operator_id,
            "shell_id": request.worker_id,
            "tenant_ref": request.tenant_id,
            "normalized_request": request.summary,
            "requested_action": request.action_name,
            "action_category": action_category,
            "source_channel": "arc_harness_shell_v0_1",
            "intent_id": f"arc-intent:{request.action_id}",
            "target_ref": request.task_ref,
            "session_ref": f"arc-session:{request.worker_id}",
            "evidence_refs": (
                f"evidence://arc-harness/{request.action_id}/guardian-decision",
                f"evidence://arc-harness/{request.action_id}/task-packet",
            ),
            "metadata": {
                "guardian_decision_id": decision.decision_id,
                "guardian_status": decision.status,
                "preview_only": request.preview_only,
                "requested_capabilities": list(request.requested_capabilities),
                "task_payload_keys": sorted(request.payload.keys()),
            },
        }

    def invoke(
        self,
        request: ArcActionRequest,
        decision: GuardianDecision,
    ) -> LimaRuntimeResult:
        resolved = self.resolve_lima_import()
        with _temporary_sys_path(resolved.checkout_path):
            adapters = importlib.import_module("lima.adapters")
            if not hasattr(adapters, "V1ShellRuntimeInput") or not hasattr(
                adapters, "run_v1_shell_governed_preflight"
            ):
                raise LimaRuntimeUnavailableError(
                    "configured LIMA checkout is missing V1ShellRuntimeInput or run_v1_shell_governed_preflight"
                )
            payload = self.build_runtime_input(request, decision)
            shell_input = adapters.V1ShellRuntimeInput(**payload)
            raw_result = adapters.run_v1_shell_governed_preflight(shell_input)
        response = dict(getattr(raw_result, "response", {}))
        response["import_source"] = resolved.source
        if resolved.checkout_path is not None:
            response["checkout_path"] = str(resolved.checkout_path)
        return LimaRuntimeResult(
            runtime_adapter=self.adapter_name,
            result_status="preview_completed",
            output=response,
        )


def build_runtime_port(
    runtime_name: str,
    repo_root: Path,
) -> LimaRuntimePort:
    if runtime_name == "fake":
        return FakeLimaRuntimePort()
    if runtime_name == "local_import":
        return LocalLimaImportRuntimePort(repo_root=repo_root)
    if runtime_name == "disabled":
        return DisabledLimaRuntimePort()
    raise LimaRuntimeUnavailableError(
        f"unsupported runtime {runtime_name!r}; expected fake, local_import, or disabled"
    )
