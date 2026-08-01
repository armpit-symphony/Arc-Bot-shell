"""Local Arc, Guardian, LIMA, and Ollama integration diagnostics."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import importlib
import inspect
import json
import os
from pathlib import Path
import sys
from typing import Callable, Iterator, Mapping

from .contracts import (
    GuardianContractProbe,
    LimaContractProbe,
    build_contract_report,
)
from arc_bot_shell.guardian import (
    DEFAULT_GUARDIAN_CONTRACT_REFERENCE,
    DEFAULT_OLLAMA_URL,
)
from arc_bot_shell.lima import (
    LIMA_PINNED_COMMIT,
    LIMA_PINNED_REFERENCE,
    LIMA_PINNED_TAG_OBJECT,
    normalize_loopback_ollama_url,
)

DEFAULT_OLLAMA_TIMEOUT_SECONDS = 0.75


@dataclass(frozen=True)
class DoctorConfig:
    """Explicit local integration configuration."""

    lima_path: Path | None
    guardian_path: Path | None
    ollama_url: str | None
    ollama_model: str | None
    guardian_mode: str = "fail_closed"
    guardian_reference: str = DEFAULT_GUARDIAN_CONTRACT_REFERENCE

    @classmethod
    def from_environ(cls, environ: Mapping[str, str]) -> "DoctorConfig":
        return cls(
            lima_path=_optional_path(environ.get("ARC_LIMA_PATH")),
            guardian_path=_optional_path(environ.get("ARC_GUARDIAN_PATH")),
            ollama_url=_optional_text(environ.get("ARC_OLLAMA_URL")),
            ollama_model=_optional_text(environ.get("ARC_OLLAMA_MODEL")),
            guardian_mode=(
                _optional_text(environ.get("ARC_GUARDIAN_MODE")) or "fail_closed"
            ),
            guardian_reference=(
                _optional_text(environ.get("ARC_GUARDIAN_REFERENCE"))
                or DEFAULT_GUARDIAN_CONTRACT_REFERENCE
            ),
        )


@dataclass(frozen=True)
class DoctorProbes:
    """Injectable probe functions for clean-clone tests."""

    guardian: Callable[[Path | None], GuardianContractProbe]
    lima: Callable[[Path | None], LimaContractProbe]
    ollama: Callable[[str, str, float], "OllamaProbeResult"]


@dataclass(frozen=True)
class OllamaProbeResult:
    """Bounded Ollama server and configured-model availability result."""

    reachable: bool
    model_available: bool


def _optional_text(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return value.strip()


def _optional_path(value: str | None) -> Path | None:
    text = _optional_text(value)
    return None if text is None else Path(text).expanduser()


@contextmanager
def _temporary_sys_path(path: Path) -> Iterator[None]:
    text = str(path.resolve())
    inserted = text not in sys.path
    if inserted:
        sys.path.insert(0, text)
    try:
        importlib.invalidate_caches()
        yield
    finally:
        if inserted:
            sys.path.remove(text)


def _import_configured_module(path: Path | None, module_name: str) -> object:
    if path is None:
        module = importlib.import_module(module_name)
    else:
        with _temporary_sys_path(path):
            module = importlib.import_module(module_name)
    origin_text = getattr(module, "__file__", None)
    if origin_text is None:
        raise ImportError(f"{module_name} has no filesystem origin")
    origin = Path(origin_text).resolve()
    if path is not None and not origin.is_relative_to(path.resolve()):
        raise ImportError(f"{module_name} resolved outside the configured path")
    return module


def _type_name(value: object) -> str:
    module = getattr(value, "__module__", None)
    name = getattr(value, "__qualname__", getattr(value, "__name__", None))
    if module and name:
        return f"{module}.{name}"
    return str(value)


def _annotation_text(value: object) -> str:
    if value is inspect.Signature.empty:
        return "unspecified"
    if isinstance(value, str):
        return value
    return str(value).replace("typing.", "")


def _source_requires_sparkbot_imports(source_root: Path) -> bool:
    import_prefixes = (
        "from app ",
        "from app.",
        "import app ",
        "from sparkbot ",
        "from sparkbot.",
        "import sparkbot ",
    )
    for source_path in source_root.rglob("*.py"):
        try:
            lines = source_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            continue
        for line in lines:
            if line.strip().startswith(import_prefixes):
                return True
    return False


def probe_guardian_contract(path: Path | None) -> GuardianContractProbe:
    """Inspect and safely exercise the Guardian package-level public contract."""

    if path is not None and not path.is_dir():
        return GuardianContractProbe(
            available=False,
            mode="unavailable",
            import_path=None,
            evaluation_entrypoint=None,
            request_input_type=None,
            decision_output_type=None,
            decision_id_field=None,
            requires_sparkbot_imports=None,
            integration_compatible=False,
            blockers=("guardian_path_not_found",),
        )
    try:
        module = _import_configured_module(path, "guardian_core")
        request_type = getattr(module, "GuardianEvaluationRequest")
        decision_type = getattr(module, "GuardianDecision")
        evaluator = getattr(module, "evaluate_guardian_request")
    except (AttributeError, ImportError, ModuleNotFoundError) as exc:
        return GuardianContractProbe(
            available=False,
            mode="unavailable",
            import_path="guardian_core",
            evaluation_entrypoint=None,
            request_input_type=None,
            decision_output_type=None,
            decision_id_field=None,
            requires_sparkbot_imports=None,
            integration_compatible=False,
            blockers=(f"guardian_import_failed:{type(exc).__name__}",),
        )

    request_fields = getattr(request_type, "__dataclass_fields__", {})
    decision_fields = getattr(decision_type, "__dataclass_fields__", {})
    decision_id_field = "decision_id" if "decision_id" in decision_fields else None
    blockers: list[str] = []
    contract_compatible = all(
        (
            callable(evaluator),
            "requested_action" in request_fields,
            "arguments" in request_fields,
            "policy_context" in request_fields,
            decision_id_field is not None,
            "status" in decision_fields,
            "allowed" in decision_fields,
        )
    )
    if not contract_compatible:
        blockers.append("guardian_contract_missing_decision_id")
    local_preview_policy_supported = False
    if contract_compatible:
        try:
            request = request_type(
                requested_action="arc.local_model_preview",
                arguments={
                    "model_adapter": "ollama",
                    "endpoint": DEFAULT_OLLAMA_URL,
                },
                policy_context={
                    "network_scope": "loopback_only",
                    "external_side_effects": False,
                    "credentials_required": False,
                    "execution_scope": "model_preview_only",
                    "runtime_route": "lima",
                },
                source="arc_bot_shell.integrations.doctor",
            )
            decision = evaluator(request)
            metadata = getattr(decision, "metadata", {})
            local_preview_policy_supported = all(
                (
                    isinstance(decision, decision_type),
                    bool(getattr(decision, "decision_id", "")),
                    getattr(decision, "status", None) == "allow",
                    getattr(decision, "allowed", None) is True,
                    getattr(decision, "requires_approval", None) is False,
                    not bool(metadata.get("execution_performed", True)),
                    not bool(metadata.get("external_services_called", True)),
                )
            )
        except Exception:
            local_preview_policy_supported = False
    if not local_preview_policy_supported:
        blockers.append("guardian_local_preview_policy_not_supported")

    return GuardianContractProbe(
        available=True,
        mode="guardian_core",
        import_path="guardian_core",
        evaluation_entrypoint="guardian_core.evaluate_guardian_request",
        request_input_type=_type_name(request_type),
        decision_output_type=_type_name(decision_type),
        decision_id_field=decision_id_field,
        requires_sparkbot_imports=False,
        integration_compatible=(contract_compatible and local_preview_policy_supported),
        blockers=tuple(blockers),
        contract_compatible=contract_compatible,
        decision_id_supported=decision_id_field is not None,
        local_preview_policy_supported=local_preview_policy_supported,
        policy_reference=DEFAULT_GUARDIAN_CONTRACT_REFERENCE,
    )


def probe_lima_contract(path: Path | None) -> LimaContractProbe:
    """Inspect and safely exercise LIMA's supported non-executing runtime API."""

    if path is not None and not path.is_dir():
        return LimaContractProbe(
            available=False,
            import_path=None,
            runtime_entrypoint=None,
            runtime_input_type=None,
            runtime_output_type=None,
            provider_executor_interface=None,
            guardian_request_type=None,
            guardian_decision_type=None,
            decision_id_field=None,
            requires_sparkbot_imports=None,
            integration_compatible=False,
            blockers=("lima_path_not_found",),
        )
    try:
        runtime = _import_configured_module(path, "lima.runtime")
        entrypoint = getattr(runtime, "run_governed_request")
    except (AttributeError, ImportError, ModuleNotFoundError) as exc:
        return LimaContractProbe(
            available=False,
            import_path="lima.runtime",
            runtime_entrypoint=None,
            runtime_input_type=None,
            runtime_output_type=None,
            provider_executor_interface=None,
            guardian_request_type=None,
            guardian_decision_type=None,
            decision_id_field=None,
            requires_sparkbot_imports=None,
            integration_compatible=False,
            blockers=(f"lima_import_failed:{type(exc).__name__}",),
        )

    signature = inspect.signature(entrypoint)
    governed_request = signature.parameters.get("request")
    decision_id_propagation_supported = False
    decision_id_field: str | None = None
    runtime_output_type: str | None = None
    non_executing_contract = False
    request_id = "arc-action:doctor-governed-preflight"
    try:
        decision = entrypoint(
            {
                "request_id": request_id,
                "consumer": "arc_bot_shell",
                "surface": "arc_bot_shell.integrations.doctor",
                "actor_id": "arc-doctor",
                "normalized_request": "Read Arc integration status without execution.",
                "requested_action": "status_read",
                "action_category": "read",
                "tool_name": "arc_status_preview",
                "tool_args": {},
                "trust_context": {
                    "tenant_id": "arc-doctor",
                    "worker_id": "arc-doctor",
                    "dry_run_only": True,
                    "execution_requested": False,
                    "side_effects_requested": False,
                },
                "evidence_refs": (),
            }
        )
        decision_payload = (
            dict(decision.to_dict())
            if callable(getattr(decision, "to_dict", None))
            else dict(getattr(decision, "__dict__", {}))
        )
        decision_id_field = (
            "decision_id" if isinstance(decision_payload.get("decision_id"), str) else None
        )
        runtime_output_type = _type_name(type(decision))
        decision_id_propagation_supported = (
            decision_payload.get("request_id") == request_id
            and decision_id_field == "decision_id"
        )
        non_executing_contract = all(
            (
                decision_payload.get("executable") is False,
                decision_payload.get("execution_allowed") is False,
                decision_payload.get("side_effects_allowed") is False,
            )
        )
    except Exception:
        decision_id_propagation_supported = False
        non_executing_contract = False
    blockers_list: list[str] = []
    if decision_id_field is None:
        blockers_list.append("lima_contract_missing_decision_id")
    if not decision_id_propagation_supported:
        blockers_list.append("lima_decision_id_propagation_failed")
    if not non_executing_contract:
        blockers_list.append("lima_non_executing_contract_failed")
    blockers_list.extend(
        (
            "retired_lima_harness_execution_disabled",
            "lima_loopback_ollama_execution_disabled",
        )
    )
    lima_source_root = (
        path / "lima"
        if path is not None
        else Path(str(getattr(runtime, "__file__"))).resolve().parents[1]
    )

    return LimaContractProbe(
        available=True,
        import_path="lima.runtime",
        runtime_entrypoint="lima.runtime.run_governed_request",
        runtime_input_type=(
            None
            if governed_request is None
            else _annotation_text(governed_request.annotation)
        ),
        runtime_output_type=runtime_output_type,
        provider_executor_interface=None,
        guardian_request_type=None,
        guardian_decision_type=None,
        decision_id_field=decision_id_field,
        requires_sparkbot_imports=_source_requires_sparkbot_imports(lima_source_root),
        integration_compatible=non_executing_contract
        and decision_id_propagation_supported,
        blockers=tuple(blockers_list),
        decision_id_propagation_supported=decision_id_propagation_supported,
        fake_executor_smoke_ready=False,
        loopback_ollama_supported=False,
    )


def normalize_ollama_url(value: str) -> str:
    """Return a loopback-only Ollama base URL or raise ValueError."""

    return normalize_loopback_ollama_url(value)


def probe_ollama_reachability(
    url: str,
    model: str,
    timeout_seconds: float,
) -> OllamaProbeResult:
    """Fail closed without network; direct model probes are retired."""

    del url, model, timeout_seconds
    return OllamaProbeResult(reachable=False, model_available=False)


DEFAULT_PROBES = DoctorProbes(
    guardian=probe_guardian_contract,
    lima=probe_lima_contract,
    ollama=probe_ollama_reachability,
)


def _missing_guardian() -> GuardianContractProbe:
    return GuardianContractProbe(
        available=False,
        mode="unavailable",
        import_path=None,
        evaluation_entrypoint=None,
        request_input_type=None,
        decision_output_type=None,
        decision_id_field=None,
        requires_sparkbot_imports=None,
        integration_compatible=False,
        blockers=("ARC_GUARDIAN_PATH_not_configured",),
    )


def _missing_lima() -> LimaContractProbe:
    return LimaContractProbe(
        available=False,
        import_path=None,
        runtime_entrypoint=None,
        runtime_input_type=None,
        runtime_output_type=None,
        provider_executor_interface=None,
        guardian_request_type=None,
        guardian_decision_type=None,
        decision_id_field=None,
        requires_sparkbot_imports=None,
        integration_compatible=False,
        blockers=("ARC_LIMA_PATH_not_configured",),
    )


def run_doctor(
    config: DoctorConfig,
    probes: DoctorProbes = DEFAULT_PROBES,
) -> dict[str, object]:
    """Run explicit, fail-closed local integration diagnostics."""

    guardian = (
        probes.guardian(config.guardian_path)
        if config.guardian_path is not None or config.guardian_mode == "guardian_core"
        else _missing_guardian()
    )
    lima = probes.lima(config.lima_path)

    blockers = [*guardian.blockers, *lima.blockers]
    ollama_url: str | None = None
    if config.ollama_url is None:
        blockers.append("ARC_OLLAMA_URL_not_configured")
    else:
        try:
            ollama_url = normalize_ollama_url(config.ollama_url)
        except ValueError as exc:
            blockers.append(str(exc))
    if config.ollama_model is None:
        blockers.append("ARC_OLLAMA_MODEL_not_configured")

    ollama_configured = ollama_url is not None and config.ollama_model is not None
    ollama_reachable = False
    ollama_model_available = False
    if ollama_configured:
        blockers.append("ollama_probe_disabled_non_executing_control_plane")

    loopback_ollama_supported = (
        lima.integration_compatible
        if lima.loopback_ollama_supported is None
        else lima.loopback_ollama_supported
    )
    local_integration_ready = all(
        (
            guardian.available,
            guardian.integration_compatible,
            lima.available,
            lima.integration_compatible,
            loopback_ollama_supported is True,
            ollama_configured,
            ollama_reachable,
            ollama_model_available,
        )
    )
    unique_blockers = list(dict.fromkeys(blockers))
    real_guardian_ready = all(
        (
            guardian.available,
            guardian.integration_compatible,
            guardian.decision_id_supported is True,
            guardian.local_preview_policy_supported is True,
        )
    )
    guardian_to_lima_ready = all(
        (
            real_guardian_ready,
            lima.available,
            lima.integration_compatible,
            lima.decision_id_propagation_supported is True,
            lima.runtime_entrypoint == "lima.runtime.run_governed_request",
            lima.fake_executor_smoke_ready is False,
            loopback_ollama_supported is False,
        )
    )

    return {
        "arc_available": True,
        "guardian_available": guardian.available,
        "guardian_mode": guardian.mode,
        "guardian_import_path": guardian.import_path,
        "guardian_contract_compatible": (
            guardian.contract_compatible
            if guardian.contract_compatible is not None
            else guardian.integration_compatible
        ),
        "guardian_decision_id_supported": (
            guardian.decision_id_supported
            if guardian.decision_id_supported is not None
            else guardian.decision_id_field is not None
        ),
        "guardian_policy_version": config.guardian_reference,
        "local_preview_policy_supported": (
            guardian.local_preview_policy_supported is True
        ),
        "real_guardian_ready": real_guardian_ready,
        "lima_available": lima.available,
        "lima_import_path": lima.import_path,
        "lima_runtime_entrypoint": lima.runtime_entrypoint,
        "lima_installed_available": lima.available,
        "lima_public_import_path": lima.import_path,
        "lima_pinned_reference": LIMA_PINNED_REFERENCE,
        "lima_pinned_commit": LIMA_PINNED_COMMIT,
        "lima_pinned_tag_object": LIMA_PINNED_TAG_OBJECT,
        "lima_entrypoint_available": lima.runtime_entrypoint is not None,
        "guardian_to_lima_contract_compatible": guardian_to_lima_ready,
        "decision_id_propagation_supported": (
            lima.decision_id_propagation_supported is True
        ),
        "fake_executor_smoke_ready": lima.fake_executor_smoke_ready is True,
        "lima_loopback_ollama_supported": (
            loopback_ollama_supported is True
        ),
        "ollama_integration_ready": local_integration_ready,
        "ollama_configured": ollama_configured,
        "ollama_endpoint_valid": ollama_url is not None,
        "ollama_reachable": ollama_reachable,
        "ollama_model": config.ollama_model,
        "ollama_model_available": ollama_model_available,
        "local_integration_ready": local_integration_ready,
        "full_local_integration_ready": local_integration_ready,
        "blockers": unique_blockers,
        "contract_report": build_contract_report(guardian, lima),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect local Arc integrations.")
    parser.add_argument("command", choices=("doctor",))
    args = parser.parse_args(argv)
    if args.command == "doctor":
        report = run_doctor(DoctorConfig.from_environ(os.environ))
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0
