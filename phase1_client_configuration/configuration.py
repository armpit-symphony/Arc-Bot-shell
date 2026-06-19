"""Phase-1 client configuration projection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLIENT_CONFIGURATION_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "arc_bot_phase1_client_configuration.json"
)

EXPECTED_PHASE_GATE_NAME = "ARC_BOT_PHASE1_CLIENT_CONFIGURATION"
EXPECTED_PHASE = "phase-1"


class ClientConfigurationPhaseGateError(RuntimeError):
    """Raised when phase gate validation fails."""


class ClientConfigurationSchemaError(ValueError):
    """Raised when the client configuration contract is invalid."""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ClientConfigurationSchemaError(f"Expected JSON object at {path}")
    return payload


def _assert_required_phase_gate(payload: dict[str, Any], *, expected_name: str) -> None:
    gate = payload.get("phase_gate")
    if not isinstance(gate, dict):
        raise ClientConfigurationSchemaError("phase_gate missing or invalid")

    if gate.get("name") != expected_name:
        raise ClientConfigurationPhaseGateError(
            f"Unexpected phase gate name {gate.get('name')} != {expected_name}"
        )
    if gate.get("required") is not True:
        raise ClientConfigurationSchemaError("phase_gate.required must be true")
    if gate.get("flag") != "arc_bot_client_configuration_docs_only":
        raise ClientConfigurationSchemaError("phase_gate.flag must be arc_bot_client_configuration_docs_only")


def _assert_top_level_shape(payload: dict[str, Any]) -> None:
    required = {
        "artifact_id",
        "artifact_type",
        "artifact_version",
        "source_access_mode",
        "phase_gate",
        "tenant_boundary",
        "deployment_profile",
        "operator_roles",
        "connector_profiles",
        "policy_posture",
        "runtime_boundaries",
        "evidence_requirements",
    }
    missing = required.difference(payload)
    if missing:
        raise ClientConfigurationSchemaError(f"Missing required fields: {', '.join(sorted(missing))}")

    if payload["artifact_version"] != EXPECTED_PHASE:
        raise ClientConfigurationSchemaError(f"artifact_version must be {EXPECTED_PHASE}")
    if payload["artifact_type"] != "phase1_client_configuration_contract":
        raise ClientConfigurationSchemaError("artifact_type must be phase1_client_configuration_contract")
    if payload["source_access_mode"] != "docs_only":
        raise ClientConfigurationSchemaError("source_access_mode must be docs_only")

    tenant = payload["tenant_boundary"]
    if not isinstance(tenant, dict):
        raise ClientConfigurationSchemaError("tenant_boundary must be object")
    for key in ("tenant_id", "customer_context_id", "single_tenant_only"):
        if key not in tenant:
            raise ClientConfigurationSchemaError(f"tenant_boundary missing {key}")
    if tenant["single_tenant_only"] is not True:
        raise ClientConfigurationSchemaError("tenant_boundary.single_tenant_only must be true")
    if tenant.get("cross_tenant_memory_allowed") is not False:
        raise ClientConfigurationSchemaError("tenant_boundary.cross_tenant_memory_allowed must be false")
    if tenant.get("customer_data_write_allowed") is not False:
        raise ClientConfigurationSchemaError("tenant_boundary.customer_data_write_allowed must be false")

    deployment = payload["deployment_profile"]
    if not isinstance(deployment, dict):
        raise ClientConfigurationSchemaError("deployment_profile must be object")
    if deployment.get("target_topology") != "one_supervisor_with_1_to_8_arc_workers":
        raise ClientConfigurationSchemaError(
            "deployment_profile.target_topology must be one_supervisor_with_1_to_8_arc_workers"
        )
    if deployment.get("supervisor_count") != 1:
        raise ClientConfigurationSchemaError("deployment_profile.supervisor_count must be 1")
    if deployment.get("worker_count_min") != 1:
        raise ClientConfigurationSchemaError("deployment_profile.worker_count_min must be 1")
    if deployment.get("worker_count_max") != 8:
        raise ClientConfigurationSchemaError("deployment_profile.worker_count_max must be 8")
    if deployment.get("production_deployment_allowed") is not False:
        raise ClientConfigurationSchemaError("deployment_profile.production_deployment_allowed must be false")

    operator_roles = payload["operator_roles"]
    if not isinstance(operator_roles, list) or not operator_roles:
        raise ClientConfigurationSchemaError("operator_roles must be a non-empty list")
    for role in operator_roles:
        if not isinstance(role, dict):
            raise ClientConfigurationSchemaError("each operator_roles entry must be object")
        for key in ("role_id", "label", "allowed_metadata_actions", "blocked_actions"):
            if key not in role:
                raise ClientConfigurationSchemaError(f"operator role missing {key}")
        if not isinstance(role["allowed_metadata_actions"], list):
            raise ClientConfigurationSchemaError("allowed_metadata_actions must be list")
        if not isinstance(role["blocked_actions"], list) or not role["blocked_actions"]:
            raise ClientConfigurationSchemaError("blocked_actions must be a non-empty list")

    connector_profiles = payload["connector_profiles"]
    if not isinstance(connector_profiles, list) or not connector_profiles:
        raise ClientConfigurationSchemaError("connector_profiles must be a non-empty list")
    for connector in connector_profiles:
        if not isinstance(connector, dict):
            raise ClientConfigurationSchemaError("each connector_profile entry must be object")
        for key in (
            "connector_id",
            "label",
            "readiness",
            "credential_value_allowed",
            "live_read_allowed",
            "live_write_allowed",
            "oauth_flow_allowed",
            "webhook_allowed",
            "metadata_actions",
        ):
            if key not in connector:
                raise ClientConfigurationSchemaError(f"connector profile missing {key}")
        if connector["readiness"] not in {"blocked_mvp", "missing_contract", "review_required"}:
            raise ClientConfigurationSchemaError("connector readiness invalid")

    policy = payload["policy_posture"]
    if not isinstance(policy, dict):
        raise ClientConfigurationSchemaError("policy_posture must be object")
    for key in (
        "approval_required_for_external_actions",
        "guardian_review_required",
        "breakglass_allowed",
        "secret_material_allowed",
    ):
        if key not in policy:
            raise ClientConfigurationSchemaError(f"policy_posture missing {key}")
    if policy["approval_required_for_external_actions"] is not True:
        raise ClientConfigurationSchemaError(
            "policy_posture.approval_required_for_external_actions must be true"
        )
    if policy["guardian_review_required"] is not True:
        raise ClientConfigurationSchemaError("policy_posture.guardian_review_required must be true")
    if policy["breakglass_allowed"] is not False:
        raise ClientConfigurationSchemaError("policy_posture.breakglass_allowed must be false")
    if policy["secret_material_allowed"] is not False:
        raise ClientConfigurationSchemaError("policy_posture.secret_material_allowed must be false")

    runtime_boundaries = payload["runtime_boundaries"]
    if not isinstance(runtime_boundaries, dict) or not runtime_boundaries:
        raise ClientConfigurationSchemaError("runtime_boundaries must be non-empty object")
    for key, value in runtime_boundaries.items():
        if not isinstance(value, bool):
            raise ClientConfigurationSchemaError(f"runtime_boundaries.{key} must be bool")
        if value is not False:
            raise ClientConfigurationSchemaError(
                f"runtime_boundaries.{key} must be false in phase-1 planning"
            )

    evidence = payload["evidence_requirements"]
    if not isinstance(evidence, dict):
        raise ClientConfigurationSchemaError("evidence_requirements must be object")
    if evidence.get("policy_refs_required") is not True:
        raise ClientConfigurationSchemaError("evidence_requirements.policy_refs_required must be true")
    if evidence.get("evidence_refs_required") is not True:
        raise ClientConfigurationSchemaError("evidence_requirements.evidence_refs_required must be true")
    if evidence.get("rollback_refs_required") is not True:
        raise ClientConfigurationSchemaError("evidence_requirements.rollback_refs_required must be true")


def _build_blocked_runtime_actions() -> list[str]:
    return [
        "frontend_route_activation",
        "interactive_action_controls_activation",
        "runtime_execution",
        "provider_model_calls",
        "connector_oauth",
        "connector_live_read",
        "connector_live_write",
        "webhook_handling",
        "worker_dispatch",
        "customer_system_mutation",
        "persistence",
        "browser_network_file_device_robotics_behavior",
        "production_deployment",
    ]


def build_phase1_client_configuration_projection(
    *,
    client_configuration_path: str | Path = DEFAULT_CLIENT_CONFIGURATION_PATH,
    enable_phase_gate: bool = False,
    phase_gate_name: str = EXPECTED_PHASE_GATE_NAME,
) -> dict[str, Any]:
    """Build the read-only planning projection from fixture-backed config."""

    if not enable_phase_gate:
        raise ClientConfigurationPhaseGateError(
            "Phase-1 client configuration rendering requires enable_phase_gate=True"
        )

    payload = _load_json(Path(client_configuration_path))
    _assert_required_phase_gate(payload, expected_name=phase_gate_name)
    _assert_top_level_shape(payload)

    blocked_runtime_actions = _build_blocked_runtime_actions()

    return {
        "artifact_id": payload["artifact_id"],
        "artifact_type": "phase1_client_configuration_projection",
        "phase": EXPECTED_PHASE,
        "projection_scope": "planning_read_only",
        "source_access_mode": "read_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "phase_gate": {
            "enabled": True,
            "name": phase_gate_name,
            "required": True,
            "flag": payload["phase_gate"]["flag"],
        },
        "tenant_boundary": {
            "tenant_id": payload["tenant_boundary"]["tenant_id"],
            "customer_context_id": payload["tenant_boundary"]["customer_context_id"],
            "single_tenant_only": payload["tenant_boundary"]["single_tenant_only"],
        },
        "deployment_profile": {
            "target_topology": payload["deployment_profile"]["target_topology"],
            "supervisor_count": payload["deployment_profile"]["supervisor_count"],
            "worker_count_min": payload["deployment_profile"]["worker_count_min"],
            "worker_count_max": payload["deployment_profile"]["worker_count_max"],
        },
        "operator_roles_count": len(payload["operator_roles"]),
        "connector_profiles_count": len(payload["connector_profiles"]),
        "blocked_runtime_actions": blocked_runtime_actions,
        "runtime_boundaries": payload["runtime_boundaries"],
        "evidence_required_refs": [
            "policy_refs_required",
            "evidence_refs_required",
            "rollback_refs_required",
        ],
    }


def run_phase1_client_configuration_preview(argv: list[str] | None = None) -> int:
    """CLI preview for phase-1 client configuration."""

    parser = argparse.ArgumentParser(
        description="Render phase-1 client configuration projection"
    )
    parser.add_argument(
        "client_configuration_path",
        nargs="?",
        default=str(DEFAULT_CLIENT_CONFIGURATION_PATH),
        help="path to phase-1 client configuration fixture",
    )
    parser.add_argument("--compact", action="store_true", help="compact output")
    parser.add_argument(
        "--snapshot-path",
        default=None,
        help="write projection snapshot to a file",
    )
    parser.add_argument(
        "--no-phase-gate",
        action="store_true",
        help="disable phase gate (tests only)",
    )

    args = parser.parse_args(argv)

    try:
        projection = build_phase1_client_configuration_projection(
            client_configuration_path=args.client_configuration_path,
            enable_phase_gate=not args.no_phase_gate,
        )
    except (ClientConfigurationPhaseGateError, ClientConfigurationSchemaError) as err:
        print(f"phase1 client configuration preview failed: {err}", file=sys.stderr)
        return 1

    if args.snapshot_path is not None:
        Path(args.snapshot_path).write_text(
            json.dumps(projection, indent=None if args.compact else 2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    json.dump(
        projection,
        sys.stdout,
        indent=None if args.compact else 2,
        sort_keys=True,
    )
    if not args.compact:
        print()
    return 0


def main() -> int:
    return run_phase1_client_configuration_preview()


if __name__ == "__main__":
    raise SystemExit(main())
