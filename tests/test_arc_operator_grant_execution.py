"""Operator CLI wiring proofs for honouring a granted read-only capability."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import json

import pytest

from arc_bot_shell.control_plane import operator_cli
from arc_bot_shell.control_plane.execution import expected_capability_for


NOW = datetime.now(timezone.utc).replace(microsecond=0)


def _grant(**overrides: Any) -> dict[str, Any]:
    grant = {
        "grant_contract": "lima.governed_execution_grant",
        "grant_version": "v0.1",
        "grant_mode": "single_use_operator_gated",
        "grant_id": "grant:cli001",
        "decision_id": "decision:cli001",
        "request_id": "request-cli-001",
        "guardian_decision_id": "gd-cli-001",
        "policy_version": "guardian-policy-lab-v1",
        "policy_snapshot_hash": "sha256:" + "a" * 64,
        "guardian_binding_hash": "sha256:" + "b" * 64,
        "granted_capability": "document_read",
        "bound_tenant_id": "tenant-lab-001",
        "bound_worker_id": "arc-worker-001",
        "bound_action_type": "safe_read",
        "scope_hash": "sha256:" + "c" * 64,
        "nonce": "nonce-cli-001",
        "issued_at": NOW.isoformat().replace("+00:00", "Z"),
        "expires_at": (NOW + timedelta(seconds=120)).isoformat().replace("+00:00", "Z"),
        "execution_allowed": True,
        "side_effects_allowed": False,
        "requires_operator_opt_in": True,
    }
    grant.update(overrides)
    return grant


class _Args:
    """Only the attributes _honour_grant reads."""

    def __init__(self, **kwargs: Any) -> None:
        self.tenant_id = "tenant-lab-001"
        self.worker_id = "arc-worker-001"
        self.action = "safe_read"
        self.resource_id = "notes.txt"
        self.execute_granted_capability = False
        self.document_root = None
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def document_root(tmp_path: Path) -> Path:
    (tmp_path / "notes.txt").write_text("quarterly numbers", encoding="utf-8")
    return tmp_path


def _result(grant: dict[str, Any] | None) -> dict[str, Any]:
    return {"request_id": "request-cli-001", "execution_grant": grant}


def test_arc_opt_in_flag_defaults_off() -> None:
    parser = operator_cli._parser()
    args = parser.parse_args(
        [
            "--supervisor-url", "http://127.0.0.1:8080",
            "--tenant-id", "t", "--customer-context-id", "c",
            "--operator-id", "o", "--operator-key-id", "k",
            "--worker-id", "w", "--action", "safe_read",
            "--resource-type", "worker_status", "--resource-id", "r",
            "--replay-db", "replay.db", "--operator-key-stdin",
        ]
    )
    assert args.execute_granted_capability is False
    assert args.document_root is None


def test_grant_is_ignored_without_arc_opt_in(document_root: Path) -> None:
    args = _Args(document_root=document_root)
    execution = operator_cli._honour_grant(args, _result(_grant()))

    assert execution["performed"] is False
    assert execution["reason_code"] == "arc_execution_opt_in_disabled"
    assert execution["side_effects_performed"] is False


def test_opt_in_without_document_root_reads_nothing(tmp_path: Path) -> None:
    args = _Args(execute_granted_capability=True, document_root=None)
    execution = operator_cli._honour_grant(args, _result(_grant()))

    assert execution["performed"] is False
    assert execution["reason_code"] == "document_root_not_configured"


def test_opt_in_with_a_valid_grant_performs_the_read(document_root: Path) -> None:
    args = _Args(execute_granted_capability=True, document_root=document_root)
    execution = operator_cli._honour_grant(args, _result(_grant()))

    assert execution["performed"] is True
    assert execution["capability"] == "document_read"
    assert execution["byte_count"] == len("quarterly numbers")
    assert execution["grant_id"] == "grant:cli001"
    assert execution["side_effects_performed"] is False


def test_absent_grant_is_reported_not_raised(document_root: Path) -> None:
    args = _Args(execute_granted_capability=True, document_root=document_root)
    execution = operator_cli._honour_grant(args, _result(None))

    assert execution["performed"] is False
    assert execution["reason_code"] == "execution_grant_absent"


def test_document_content_is_not_echoed_into_cli_output(document_root: Path) -> None:
    args = _Args(execute_granted_capability=True, document_root=document_root)
    execution = operator_cli._honour_grant(args, _result(_grant()))

    assert execution["performed"] is True
    rendered = json.dumps(execution)
    assert "quarterly numbers" not in rendered
    assert "content" not in execution


def test_capability_is_derived_from_the_action_not_the_grant(
    document_root: Path,
) -> None:
    """A grant naming a capability Arc did not ask for must be refused."""

    args = _Args(execute_granted_capability=True, document_root=document_root)
    mismatched = _grant(granted_capability="draft_workspace")
    execution = operator_cli._honour_grant(args, _result(mismatched))

    assert execution["performed"] is False
    assert execution["reason_code"] == "execution_grant_binding_mismatch"


def test_unknown_action_has_no_expected_capability(document_root: Path) -> None:
    assert expected_capability_for("not_an_action") is None
    args = _Args(
        execute_granted_capability=True,
        document_root=document_root,
        action="not_an_action",
    )
    execution = operator_cli._honour_grant(args, _result(_grant()))

    assert execution["performed"] is False
    assert execution["reason_code"] == "execution_grant_binding_mismatch"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("bound_tenant_id", "other-tenant"),
        ("bound_worker_id", "other-worker"),
        ("bound_action_type", "external_write"),
        ("request_id", "other-request"),
    ],
)
def test_grant_for_another_subject_is_refused(
    document_root: Path,
    field: str,
    value: str,
) -> None:
    args = _Args(execute_granted_capability=True, document_root=document_root)
    execution = operator_cli._honour_grant(args, _result(_grant(**{field: value})))

    assert execution["performed"] is False
    assert execution["reason_code"] == "execution_grant_binding_mismatch"


def test_expired_grant_is_refused(document_root: Path) -> None:
    args = _Args(execute_granted_capability=True, document_root=document_root)
    stale = _grant(
        expires_at=(NOW - timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
    )
    execution = operator_cli._honour_grant(args, _result(stale))

    assert execution["performed"] is False
    assert execution["reason_code"] == "execution_grant_expired"
