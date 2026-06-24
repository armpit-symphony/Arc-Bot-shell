"""Phase-G/Phase-10 field deployment package projection.

This module describes the repeatable local-PC deployment package Arc Bot needs
before a narrow field pilot. It is a planning/readiness projection only: it
does not install software, start services, call models, probe sockets, attach
to a supervisor, write durable state, or mutate customer systems.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ArcFieldDeploymentPackageError(RuntimeError):
    """Raised when the field deployment projection is incomplete or unsafe."""


SETUP_GUIDES: tuple[str, ...] = (
    "docs/deployment/ARC_WORKER_LOCAL_PC_SETUP.md",
    "docs/deployment/ARC_FIELD_DEPLOYMENT_PACKAGE.md",
)

SUPPORT_RUNBOOKS: tuple[str, ...] = (
    "docs/runbooks/worker_offline.md",
    "docs/runbooks/model_not_reachable.md",
    "docs/runbooks/approval_queue_stuck.md",
    "docs/runbooks/evidence_packet_missing.md",
    "docs/runbooks/document_preview_failed.md",
)

SMOKE_COMMANDS: tuple[str, ...] = (
    "python -m phase0_runtime_ui_scaffold.phase_chain "
    "--emit-status-snapshot --with-guardian-suite-seam --compact",
    "python -m phase6_lima_office_integration.read_adapter --compact",
    "python -m phase7_approval_evidence.readiness --compact",
    "python -m phase10_field_deployment.package --compact",
    "powershell -ExecutionPolicy Bypass -File scripts\\arc_worker_smoke.ps1",
)


def build_arc_field_deployment_readiness_projection() -> dict[str, Any]:
    """Build deterministic field-deployment readiness metadata."""

    projection: dict[str, Any] = {
        "artifact_type": "arc_field_deployment_readiness_projection",
        "artifact_id": "arc_field_deployment_readiness_v1",
        "phase": "phase-g-field-deployment-package",
        "status": "planning_ready_runtime_blocked",
        "projection_scope": "planning_read_only",
        "source_access_mode": "read_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "production_ready": False,
        "production_deployment_allowed": False,
        "requires_external_owner_input": True,
        "external_dependency_ref": (
            "docs/requests/GUARDIAN_LIMA_OFFICE_PHASE_D_APPROVAL_EVIDENCE_REQUEST.md"
        ),
        "deployment_topology": {
            "supervisor_servers": 1,
            "worker_min": 1,
            "worker_max": 8,
            "tenant_mode": "single_tenant",
            "target_node": "local_arc_worker_mini_pc",
        },
        "setup_guides": list(SETUP_GUIDES),
        "support_runbooks": list(SUPPORT_RUNBOOKS),
        "smoke_commands": list(SMOKE_COMMANDS),
        "field_readiness_checks": [
            "operator confirms single-tenant workspace label",
            "operator confirms worker identity label is assigned",
            "operator confirms supervisor attachment is pending approval",
            "operator confirms local model readiness is metadata-only",
            "operator confirms no live connector credentials are configured",
            "operator confirms rollback is docs-only for this phase",
        ],
        "blocked_runtime_capabilities": [
            "software_install_or_update",
            "service_start_or_supervisor_attachment",
            "live_lima_office_registration",
            "local_model_invocation",
            "cloud_model_fallback",
            "connector_read_or_write",
            "customer_system_mutation",
            "external_message_send",
            "durable_evidence_write",
            "approval_token_issuance_or_verification",
        ],
        "allowed_outputs": [
            "operator_setup_checklist",
            "read_only_smoke_projection",
            "support_runbook_selection",
            "field_readiness_gap_report",
        ],
        "rollback_posture": {
            "rollback_mode": "docs_only_no_runtime_changes",
            "destructive_actions_allowed": False,
            "customer_data_retention_change_allowed": False,
            "requires_operator_approval_for_future_runtime_changes": True,
        },
        "evidence_refs": [
            "proof:arc-bot:phase-g-field-deployment-package",
            "smoke:arc-worker:read-only-projection-suite",
        ],
        "policy_refs": [
            "CONTRACTS.md#arc-field-deployment-package",
            "AUTONOMY_BOUNDARIES.md",
            "SECURITY_MODEL.md",
        ],
    }

    _assert_projection_safe(projection)
    return projection


def _assert_projection_safe(projection: dict[str, Any]) -> None:
    if projection.get("runtime_authority_blocked") is not True:
        raise ArcFieldDeploymentPackageError("field package cannot grant authority")
    if projection.get("runtime_execution_blocked") is not True:
        raise ArcFieldDeploymentPackageError("field package cannot grant execution")
    if projection.get("production_ready") is not False:
        raise ArcFieldDeploymentPackageError("field package cannot claim production readiness")
    if projection.get("production_deployment_allowed") is not False:
        raise ArcFieldDeploymentPackageError("field package cannot allow deployment")

    topology = projection.get("deployment_topology", {})
    if topology.get("supervisor_servers") != 1:
        raise ArcFieldDeploymentPackageError("field topology must use one supervisor")
    if topology.get("worker_min") != 1 or topology.get("worker_max") != 8:
        raise ArcFieldDeploymentPackageError("field topology must use 1-8 workers")
    if topology.get("tenant_mode") != "single_tenant":
        raise ArcFieldDeploymentPackageError("field topology must be single-tenant")

    if not projection.get("setup_guides"):
        raise ArcFieldDeploymentPackageError("field package requires setup guides")
    if not projection.get("support_runbooks"):
        raise ArcFieldDeploymentPackageError("field package requires support runbooks")
    if not projection.get("smoke_commands"):
        raise ArcFieldDeploymentPackageError("field package requires smoke commands")


def run_arc_field_deployment_package_preview(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render Arc Bot field deployment readiness metadata."
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument("--snapshot-path", help="Write projection JSON to this file.")
    args = parser.parse_args(argv)

    try:
        projection = build_arc_field_deployment_readiness_projection()
    except (ArcFieldDeploymentPackageError, OSError, ValueError) as err:
        print(f"field deployment package preview failed: {err}", file=sys.stderr)
        return 1

    rendered = json.dumps(
        projection,
        sort_keys=True,
        indent=None if args.compact else 2,
    )
    if args.snapshot_path:
        Path(args.snapshot_path).write_text(rendered + "\n", encoding="utf-8")

    sys.stdout.write(rendered)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_arc_field_deployment_package_preview()


if __name__ == "__main__":
    raise SystemExit(main())
