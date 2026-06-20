"""Ollama/Qwen local model readiness projection.

Phase 2 defines local model seat readiness without probing Ollama, invoking a
model, opening sockets, reading secrets, or calling LIMA Office. Live checks
must come later through Guardian/LIMA Office authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any, Literal


DEFAULT_QWEN_MODEL_ID = "qwen2.5:7b"
DEFAULT_OLLAMA_ENDPOINT_LABEL = "http://127.0.0.1:11434"
EXPECTED_RUNTIME = "ollama"
EXPECTED_MODEL_FAMILY = "qwen"

ReadinessStatus = Literal["ready", "setup_required", "blocked"]


class OllamaQwenReadinessProjectionError(RuntimeError):
    """Raised when the Phase-2 readiness projection violates safety policy."""


@dataclass(frozen=True)
class OllamaQwenHardwareProfile:
    """Operator-entered hardware profile for one Arc worker PC."""

    cpu_threads: int = 8
    system_ram_gb: int = 16
    gpu_label: str = "integrated_or_unknown"
    gpu_vram_gb: int = 0
    storage_free_gb: int = 30
    hardware_notes: str = "operator_confirmed_local_pc"


@dataclass(frozen=True)
class OllamaQwenReadinessInput:
    """Operator-attested readiness inputs for the Ollama/Qwen local seat."""

    worker_id: str = "arc-worker-001"
    tenant_id: str = "single_tenant_local"
    runtime: str = EXPECTED_RUNTIME
    model_family: str = EXPECTED_MODEL_FAMILY
    model_id: str = DEFAULT_QWEN_MODEL_ID
    endpoint_label: str = DEFAULT_OLLAMA_ENDPOINT_LABEL
    ollama_installed: bool = False
    ollama_service_reachable: bool = False
    qwen_model_present: bool = False
    lima_office_attached: bool = False
    hardware_profile: OllamaQwenHardwareProfile = OllamaQwenHardwareProfile()


def _readiness_status(readiness: OllamaQwenReadinessInput) -> ReadinessStatus:
    if readiness.runtime != EXPECTED_RUNTIME or readiness.model_family != EXPECTED_MODEL_FAMILY:
        return "blocked"
    if (
        readiness.ollama_installed
        and readiness.ollama_service_reachable
        and readiness.qwen_model_present
        and readiness.lima_office_attached
    ):
        return "ready"
    return "setup_required"


def _assert_readiness_guardrails(projection: dict[str, Any]) -> None:
    if projection["model_invocation_performed"] is not False:
        raise OllamaQwenReadinessProjectionError("Readiness must not invoke the model")
    if projection["network_probe_performed"] is not False:
        raise OllamaQwenReadinessProjectionError("Readiness must not open a network probe")
    if projection["provider_credentials_required"] is not False:
        raise OllamaQwenReadinessProjectionError(
            "Ollama/Qwen readiness must not need provider credentials"
        )
    if projection["cloud_fallback_allowed"] is not False:
        raise OllamaQwenReadinessProjectionError("Cloud fallback must stay disabled")
    if projection["runtime_execution_blocked"] is not True:
        raise OllamaQwenReadinessProjectionError("Runtime execution must remain blocked")


def build_ollama_qwen_readiness_projection(
    readiness: OllamaQwenReadinessInput | None = None,
) -> dict[str, Any]:
    """Build the Phase-2 local model readiness projection."""

    readiness = readiness or OllamaQwenReadinessInput()
    status = _readiness_status(readiness)
    missing = []
    if readiness.ollama_installed is not True:
        missing.append("ollama_install")
    if readiness.ollama_service_reachable is not True:
        missing.append("ollama_localhost_service")
    if readiness.qwen_model_present is not True:
        missing.append("qwen_model_pull")
    if readiness.lima_office_attached is not True:
        missing.append("lima_office_worker_attachment")
    if readiness.runtime != EXPECTED_RUNTIME:
        missing.append("runtime_must_be_ollama")
    if readiness.model_family != EXPECTED_MODEL_FAMILY:
        missing.append("model_family_must_be_qwen")

    projection: dict[str, Any] = {
        "artifact_id": "arc_bot_phase2_ollama_qwen_readiness_v1",
        "artifact_type": "phase2_ollama_qwen_readiness_projection",
        "phase": "phase-2",
        "projection_scope": "planning_read_only",
        "source_access_mode": "operator_attested_no_probe",
        "worker_id": readiness.worker_id,
        "tenant_id": readiness.tenant_id,
        "runtime": readiness.runtime,
        "runtime_choice": EXPECTED_RUNTIME,
        "provider_kind": "local_model",
        "model_family": readiness.model_family,
        "model_id": readiness.model_id,
        "endpoint_label": readiness.endpoint_label,
        "localhost_only": True,
        "readiness_status": status,
        "connection_indicator": "green_check" if status == "ready" else "red_attention",
        "ollama_installed": readiness.ollama_installed,
        "ollama_service_reachable": readiness.ollama_service_reachable,
        "qwen_model_present": readiness.qwen_model_present,
        "lima_office_attached": readiness.lima_office_attached,
        "hardware_profile": asdict(readiness.hardware_profile),
        "hardware_posture": {
            "cpu_ready": readiness.hardware_profile.cpu_threads >= 4,
            "memory_ready": readiness.hardware_profile.system_ram_gb >= 16,
            "gpu_required": False,
            "storage_ready": readiness.hardware_profile.storage_free_gb >= 20,
        },
        "missing_requirements": sorted(missing),
        "model_invocation_performed": False,
        "network_probe_performed": False,
        "ollama_api_call_performed": False,
        "provider_sdk_used": False,
        "provider_credentials_required": False,
        "credential_material_present": False,
        "cloud_fallback_allowed": False,
        "network_egress_allowed": False,
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "guardian_required_before_model_call": True,
        "evidence_refs": [
            "evidence://arc-bot/phase2/ollama-install-attestation",
            "evidence://arc-bot/phase2/qwen-model-attestation",
            "evidence://arc-bot/phase2/lima-office-worker-attachment",
        ],
        "policy_refs": [
            "policy://arc-bot/local-model-only",
            "policy://arc-bot/no-cloud-fallback",
            "policy://arc-bot/guardian-required-before-model-call",
        ],
        "runbook_refs": [
            "runbook://arc-bot/install-ollama",
            "runbook://arc-bot/pull-qwen-model",
            "runbook://arc-bot/attach-worker-to-lima-office",
        ],
    }
    _assert_readiness_guardrails(projection)
    return projection


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render Phase-2 Ollama/Qwen local model readiness projection."
    )
    parser.add_argument("--model-id", default=DEFAULT_QWEN_MODEL_ID)
    parser.add_argument("--endpoint-label", default=DEFAULT_OLLAMA_ENDPOINT_LABEL)
    parser.add_argument("--ollama-installed", action="store_true")
    parser.add_argument("--ollama-service-reachable", action="store_true")
    parser.add_argument("--qwen-model-present", action="store_true")
    parser.add_argument("--lima-office-attached", action="store_true")
    parser.add_argument("--cpu-threads", type=int, default=8)
    parser.add_argument("--system-ram-gb", type=int, default=16)
    parser.add_argument("--gpu-label", default="integrated_or_unknown")
    parser.add_argument("--gpu-vram-gb", type=int, default=0)
    parser.add_argument("--storage-free-gb", type=int, default=30)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--snapshot-path")
    return parser


def run_ollama_qwen_readiness_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    readiness = OllamaQwenReadinessInput(
        model_id=args.model_id,
        endpoint_label=args.endpoint_label,
        ollama_installed=args.ollama_installed,
        ollama_service_reachable=args.ollama_service_reachable,
        qwen_model_present=args.qwen_model_present,
        lima_office_attached=args.lima_office_attached,
        hardware_profile=OllamaQwenHardwareProfile(
            cpu_threads=args.cpu_threads,
            system_ram_gb=args.system_ram_gb,
            gpu_label=args.gpu_label,
            gpu_vram_gb=args.gpu_vram_gb,
            storage_free_gb=args.storage_free_gb,
        ),
    )

    try:
        projection = build_ollama_qwen_readiness_projection(readiness)
    except OllamaQwenReadinessProjectionError as err:
        print(f"ollama/qwen readiness preview failed: {err}", file=sys.stderr)
        return 1

    if args.snapshot_path:
        with open(args.snapshot_path, "w", encoding="utf-8") as handle:
            json.dump(
                projection,
                handle,
                sort_keys=True,
                indent=None if args.compact else 2,
            )
            handle.write("\n")

    json.dump(projection, sys.stdout, indent=None if args.compact else 2, sort_keys=True)
    if not args.compact:
        sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_ollama_qwen_readiness_preview()


if __name__ == "__main__":
    raise SystemExit(main())
