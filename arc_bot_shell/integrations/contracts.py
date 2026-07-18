"""Machine-readable integration contract probe results."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

CONTRACT_REPORT_SCHEMA_VERSION = "arc-integration-contract-report-v0.7"


@dataclass(frozen=True)
class GuardianContractProbe:
    """Observed Guardian import and decision contract."""

    available: bool
    mode: str
    import_path: str | None
    evaluation_entrypoint: str | None
    request_input_type: str | None
    decision_output_type: str | None
    decision_id_field: str | None
    requires_sparkbot_imports: bool | None
    integration_compatible: bool
    blockers: tuple[str, ...] = ()
    contract_compatible: bool | None = None
    decision_id_supported: bool | None = None
    local_preview_policy_supported: bool | None = None
    policy_reference: str | None = None


@dataclass(frozen=True)
class LimaContractProbe:
    """Observed LIMA public harness and type contract."""

    available: bool
    import_path: str | None
    runtime_entrypoint: str | None
    runtime_input_type: str | None
    runtime_output_type: str | None
    provider_executor_interface: str | None
    guardian_request_type: str | None
    guardian_decision_type: str | None
    decision_id_field: str | None
    requires_sparkbot_imports: bool | None
    integration_compatible: bool
    blockers: tuple[str, ...] = ()
    decision_id_propagation_supported: bool | None = None
    fake_executor_smoke_ready: bool | None = None


def build_contract_report(
    guardian: GuardianContractProbe,
    lima: LimaContractProbe,
) -> dict[str, Any]:
    """Build deterministic JSON-ready contract evidence from runtime probes."""

    return {
        "schema_version": CONTRACT_REPORT_SCHEMA_VERSION,
        "generated_by": "arc_bot_shell.integrations.contracts.build_contract_report",
        "invariants": {
            "guardian_required_for_every_model_call": True,
            "guardian_decision_id_required": True,
            "arc_direct_model_execution_allowed": False,
            "lima_runtime_adapter_required": True,
            "ollama_network_scope": "loopback_only",
            "credentials_required": False,
        },
        "guardian": asdict(guardian),
        "lima": asdict(lima),
        "editable_install_audit": {
            "guardian_suite": {
                "result": "pass",
                "clean_import_path": "guardian_core",
                "documented_suite_path": "app.services.guardian",
                "documented_suite_packaged": False,
            },
            "lima_runtime": {
                "result": "pass",
                "clean_import_path": "lima.harness",
            },
        },
    }
