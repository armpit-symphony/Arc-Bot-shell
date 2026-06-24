"""Field deployment package projection tests."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

from phase10_field_deployment.package import (
    build_arc_field_deployment_readiness_projection,
    run_arc_field_deployment_package_preview,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_field_deployment_package_is_read_only_and_runtime_blocked() -> None:
    projection = build_arc_field_deployment_readiness_projection()

    assert projection["artifact_type"] == "arc_field_deployment_readiness_projection"
    assert projection["phase"] == "phase-g-field-deployment-package"
    assert projection["projection_scope"] == "planning_read_only"
    assert projection["source_access_mode"] == "read_only"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["production_ready"] is False
    assert projection["production_deployment_allowed"] is False


def test_field_deployment_package_preserves_single_tenant_topology() -> None:
    topology = build_arc_field_deployment_readiness_projection()["deployment_topology"]

    assert topology["supervisor_servers"] == 1
    assert topology["worker_min"] == 1
    assert topology["worker_max"] == 8
    assert topology["tenant_mode"] == "single_tenant"


def test_field_deployment_package_referenced_docs_exist() -> None:
    projection = build_arc_field_deployment_readiness_projection()
    refs = (
        projection["setup_guides"]
        + projection["support_runbooks"]
        + [projection["external_dependency_ref"]]
    )

    missing = [ref for ref in refs if not (REPO_ROOT / ref).exists()]
    assert not missing


def test_field_deployment_package_blocks_runtime_capabilities() -> None:
    blocked = set(build_arc_field_deployment_readiness_projection()["blocked_runtime_capabilities"])

    assert "software_install_or_update" in blocked
    assert "service_start_or_supervisor_attachment" in blocked
    assert "local_model_invocation" in blocked
    assert "connector_read_or_write" in blocked
    assert "durable_evidence_write" in blocked
    assert "approval_token_issuance_or_verification" in blocked


def test_field_deployment_package_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_arc_field_deployment_package_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_id"] == "arc_field_deployment_readiness_v1"
    assert parsed["runtime_execution_blocked"] is True
