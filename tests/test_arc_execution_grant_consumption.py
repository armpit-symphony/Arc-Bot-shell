"""Arc-side proofs for honouring a Supervisor execution grant."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from arc_bot_shell.control_plane.execution import (
    HONOURED_CAPABILITIES,
    MAX_DOCUMENT_BYTES,
    ArcExecutionDenied,
    ArcGrantExecutor,
)


NOW = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
SUBJECT = {
    "request_id": "request-grant-001",
    "tenant_id": "tenant-lab-001",
    "worker_id": "arc-worker-001",
    "action_type": "safe_read",
    "capability": "document_read",
}


def _grant(**overrides: Any) -> dict[str, Any]:
    grant = {
        "grant_contract": "lima.governed_execution_grant",
        "grant_version": "v0.1",
        "grant_mode": "single_use_operator_gated",
        "grant_id": "grant:abc123",
        "decision_id": "decision:abc123",
        "request_id": "request-grant-001",
        "guardian_decision_id": "gd-safe-read",
        "policy_version": "guardian-policy-lab-v1",
        "policy_snapshot_hash": "sha256:" + "a" * 64,
        "guardian_binding_hash": "sha256:" + "b" * 64,
        "granted_capability": "document_read",
        "bound_tenant_id": "tenant-lab-001",
        "bound_worker_id": "arc-worker-001",
        "bound_action_type": "safe_read",
        "scope_hash": "sha256:" + "c" * 64,
        "nonce": "nonce-001",
        "issued_at": NOW.isoformat().replace("+00:00", "Z"),
        "expires_at": (NOW + timedelta(seconds=120)).isoformat().replace("+00:00", "Z"),
        "execution_allowed": True,
        "side_effects_allowed": False,
        "requires_operator_opt_in": True,
    }
    grant.update(overrides)
    return grant


@pytest.fixture
def document_root(tmp_path: Path) -> Path:
    (tmp_path / "notes.txt").write_text("quarterly report body", encoding="utf-8")
    nested = tmp_path / "team"
    nested.mkdir()
    (nested / "plan.txt").write_text("team plan", encoding="utf-8")
    return tmp_path


def _executor(document_root: Path, **kwargs: Any) -> ArcGrantExecutor:
    params: dict[str, Any] = {
        "execution_opt_in": True,
        "document_root": document_root,
        "clock": lambda: NOW,
    }
    params.update(kwargs)
    return ArcGrantExecutor(**params)


def _honour(executor: ArcGrantExecutor, grant: Any, resource_id: str = "notes.txt"):
    return executor.honour(grant, resource_id=resource_id, **SUBJECT)


# ---------------------------------------------------------------------------
# Happy path: this is the only place Arc performs a real side effect.
# ---------------------------------------------------------------------------


def test_valid_grant_reads_the_document(document_root: Path) -> None:
    result = _honour(_executor(document_root), _grant())

    assert result["executed"] is True
    assert result["side_effects_performed"] is False
    assert result["capability"] == "document_read"
    assert result["content"] == "quarterly report body"
    assert result["grant_id"] == "grant:abc123"


def test_nested_paths_inside_the_root_are_readable(document_root: Path) -> None:
    result = _honour(_executor(document_root), _grant(), resource_id="team/plan.txt")
    assert result["content"] == "team plan"


# ---------------------------------------------------------------------------
# Arc's own opt-in is independent of the Supervisor's.
# ---------------------------------------------------------------------------


def test_arc_opt_in_defaults_to_off() -> None:
    assert ArcGrantExecutor().execution_opt_in is False


def test_arc_refuses_a_perfectly_valid_grant_when_its_own_opt_in_is_off(
    document_root: Path,
) -> None:
    executor = _executor(document_root, execution_opt_in=False)
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(executor, _grant())
    assert excinfo.value.reason_code == "arc_execution_opt_in_disabled"


def test_absent_grant_is_denied(document_root: Path) -> None:
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(_executor(document_root), None)
    assert excinfo.value.reason_code == "execution_grant_absent"


# ---------------------------------------------------------------------------
# Grant shape.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"grant_contract": "something.else"}, "execution_grant_contract_mismatch"),
        ({"grant_version": "v9"}, "execution_grant_version_mismatch"),
        ({"execution_allowed": False}, "execution_grant_does_not_allow_execution"),
        (
            {"requires_operator_opt_in": False},
            "execution_grant_waives_operator_opt_in",
        ),
        ({"side_effects_allowed": True}, "execution_grant_permits_side_effects"),
        ({"grant_id": ""}, "execution_grant_malformed"),
        ({"nonce": ""}, "execution_grant_malformed"),
    ],
)
def test_unacceptable_grants_are_refused(
    document_root: Path,
    overrides: dict[str, Any],
    expected: str,
) -> None:
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(_executor(document_root), _grant(**overrides))
    assert excinfo.value.reason_code == expected


# ---------------------------------------------------------------------------
# Binding: a grant is only good for its own subject.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field",
    [
        "request_id",
        "bound_tenant_id",
        "bound_worker_id",
        "bound_action_type",
        "granted_capability",
    ],
)
def test_substituted_binding_is_refused(document_root: Path, field: str) -> None:
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(_executor(document_root), _grant(**{field: "substituted"}))
    assert excinfo.value.reason_code in {
        "execution_grant_binding_mismatch",
        "capability_not_honoured",
    }


def test_only_document_read_is_honoured() -> None:
    assert HONOURED_CAPABILITIES == frozenset({"document_read"})


# ---------------------------------------------------------------------------
# Expiry.
# ---------------------------------------------------------------------------


def test_expired_grant_is_refused(document_root: Path) -> None:
    executor = _executor(document_root, clock=lambda: NOW + timedelta(seconds=121))
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(executor, _grant())
    assert excinfo.value.reason_code == "execution_grant_expired"


def test_grant_valid_right_up_to_expiry(document_root: Path) -> None:
    executor = _executor(document_root, clock=lambda: NOW + timedelta(seconds=119))
    assert _honour(executor, _grant())["executed"] is True


@pytest.mark.parametrize("expires_at", ["", "not-a-date", "2026-08-01T12:02:00"])
def test_malformed_expiry_is_refused(document_root: Path, expires_at: str) -> None:
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(_executor(document_root), _grant(expires_at=expires_at))
    assert excinfo.value.reason_code == "execution_grant_malformed"


# ---------------------------------------------------------------------------
# Filesystem containment.
# ---------------------------------------------------------------------------


def test_unconfigured_root_cannot_read_anything(tmp_path: Path) -> None:
    executor = ArcGrantExecutor(execution_opt_in=True, clock=lambda: NOW)
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(executor, _grant())
    assert excinfo.value.reason_code == "document_root_not_configured"


@pytest.mark.parametrize(
    "resource_id",
    ["../outside.txt", "../../outside.txt", "team/../../outside.txt"],
)
def test_traversal_outside_the_root_is_refused(
    document_root: Path,
    resource_id: str,
) -> None:
    (document_root.parent / "outside.txt").write_text("secret", encoding="utf-8")
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(_executor(document_root), _grant(), resource_id=resource_id)
    assert excinfo.value.reason_code == "document_outside_root"


def test_absolute_path_outside_the_root_is_refused(document_root: Path) -> None:
    outside = document_root.parent / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(_executor(document_root), _grant(), resource_id=str(outside))
    assert excinfo.value.reason_code == "document_outside_root"


def test_missing_document_is_refused(document_root: Path) -> None:
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(_executor(document_root), _grant(), resource_id="nope.txt")
    assert excinfo.value.reason_code == "document_not_found"


def test_directory_is_not_readable_as_a_document(document_root: Path) -> None:
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(_executor(document_root), _grant(), resource_id="team")
    assert excinfo.value.reason_code == "document_not_found"


@pytest.mark.parametrize("resource_id", ["", "   "])
def test_blank_resource_is_refused(document_root: Path, resource_id: str) -> None:
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(_executor(document_root), _grant(), resource_id=resource_id)
    assert excinfo.value.reason_code == "document_resource_invalid"


def test_oversized_document_is_refused(document_root: Path) -> None:
    big = document_root / "big.txt"
    big.write_text("x" * (MAX_DOCUMENT_BYTES + 1), encoding="utf-8")
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(_executor(document_root), _grant(), resource_id="big.txt")
    assert excinfo.value.reason_code == "document_too_large"


def test_no_write_occurs_during_a_read(document_root: Path) -> None:
    before = {p.name: p.read_bytes() for p in document_root.rglob("*") if p.is_file()}
    _honour(_executor(document_root), _grant())
    after = {p.name: p.read_bytes() for p in document_root.rglob("*") if p.is_file()}
    assert before == after
