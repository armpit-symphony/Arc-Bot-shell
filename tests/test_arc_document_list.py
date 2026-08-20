"""Security proofs for the bounded Arc document listing capability."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from arc_bot_shell.control_plane.execution import (
    MAX_DOCUMENT_LIST_ENTRIES,
    ArcExecutionDenied,
    ArcGrantExecutor,
    expected_capability_for,
)

NOW = datetime(2026, 8, 20, 12, 0, 0, tzinfo=timezone.utc)
SUBJECT = {
    "request_id": "request-list-001",
    "tenant_id": "tenant-lab-001",
    "worker_id": "arc-worker-001",
    "action_type": "safe_list",
    "capability": "document_list",
}


def _grant(**overrides: Any) -> dict[str, Any]:
    grant = {
        "grant_contract": "lima.governed_execution_grant",
        "grant_version": "v0.1",
        "grant_mode": "single_use_operator_gated",
        "grant_id": "grant:list-001",
        "decision_id": "decision:list-001",
        "request_id": SUBJECT["request_id"],
        "guardian_decision_id": "guardian:list-001",
        "policy_version": "guardian-policy-lab-v1",
        "policy_snapshot_hash": "sha256:" + "a" * 64,
        "guardian_binding_hash": "sha256:" + "b" * 64,
        "granted_capability": SUBJECT["capability"],
        "bound_tenant_id": SUBJECT["tenant_id"],
        "bound_worker_id": SUBJECT["worker_id"],
        "bound_action_type": SUBJECT["action_type"],
        "scope_hash": "sha256:" + "c" * 64,
        "nonce": "nonce-list-001",
        "issued_at": NOW.isoformat().replace("+00:00", "Z"),
        "expires_at": (NOW + timedelta(seconds=120)).isoformat().replace("+00:00", "Z"),
        "execution_allowed": True,
        "side_effects_allowed": False,
        "requires_operator_opt_in": True,
    }
    grant.update(overrides)
    return grant


def _executor(root: Path) -> ArcGrantExecutor:
    return ArcGrantExecutor(
        execution_opt_in=True,
        document_root=root,
        clock=lambda: NOW,
    )


def _honour(root: Path, resource_id: str = ".") -> dict[str, Any]:
    return _executor(root).honour(
        _grant(),
        resource_id=resource_id,
        **SUBJECT,
    )


def test_safe_list_maps_to_document_list() -> None:
    assert expected_capability_for("safe_list") == "document_list"


def test_root_listing_is_sorted_bounded_metadata_only(tmp_path: Path) -> None:
    (tmp_path / "zeta.txt").write_text("do not expose this", encoding="utf-8")
    (tmp_path / "Alpha.txt").write_text("a", encoding="utf-8")
    (tmp_path / "team").mkdir()
    (tmp_path / ".env").write_text("SECRET=value", encoding="utf-8")

    result = _honour(tmp_path)

    assert result["executed"] is True
    assert result["capability"] == "document_list"
    assert result["resource_id"] == "."
    assert result["side_effects_performed"] is False
    assert result["truncated"] is False
    assert [entry["name"] for entry in result["entries"]] == [
        "Alpha.txt",
        "team",
        "zeta.txt",
    ]
    assert result["entries"][0] == {
        "name": "Alpha.txt",
        "relative_path": "Alpha.txt",
        "kind": "file",
        "byte_count": 1,
    }
    assert result["entries"][1]["byte_count"] is None
    rendered = repr(result)
    assert "do not expose this" not in rendered
    assert "SECRET=value" not in rendered
    assert str(tmp_path) not in rendered
    assert ".env" not in rendered


def test_nested_listing_returns_root_relative_paths(tmp_path: Path) -> None:
    team = tmp_path / "team"
    team.mkdir()
    (team / "plan.txt").write_text("plan", encoding="utf-8")

    result = _honour(tmp_path, "team")

    assert result["entries"] == [
        {
            "name": "plan.txt",
            "relative_path": "team/plan.txt",
            "kind": "file",
            "byte_count": 4,
        }
    ]


def test_listing_is_capped_and_reports_truncation(tmp_path: Path) -> None:
    for index in range(MAX_DOCUMENT_LIST_ENTRIES + 5):
        (tmp_path / f"item-{index:03}.txt").write_bytes(b"x")

    result = _honour(tmp_path)

    assert result["entry_count"] == MAX_DOCUMENT_LIST_ENTRIES
    assert result["entry_limit"] == MAX_DOCUMENT_LIST_ENTRIES
    assert result["truncated"] is True


@pytest.mark.parametrize(
    ("resource_id", "reason_code"),
    [
        ("../outside", "document_outside_root"),
        ("team/../../outside", "document_outside_root"),
        (".private", "document_directory_hidden"),
        ("missing", "document_directory_not_found"),
    ],
)
def test_unsafe_or_missing_directories_are_refused(
    tmp_path: Path,
    resource_id: str,
    reason_code: str,
) -> None:
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(tmp_path, resource_id)
    assert excinfo.value.reason_code == reason_code


def test_absolute_directory_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(tmp_path, str(tmp_path))
    assert excinfo.value.reason_code == "document_outside_root"


def test_symlink_entries_are_not_projected(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-listing.txt"
    outside.write_text("outside", encoding="utf-8")
    link = tmp_path / "shortcut.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are unavailable for this test account")

    result = _honour(tmp_path)

    assert "shortcut.txt" not in [entry["name"] for entry in result["entries"]]


def test_requested_symlink_directory_is_refused(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "shortcut"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable for this test account")

    with pytest.raises(ArcExecutionDenied) as excinfo:
        _honour(tmp_path, "shortcut")
    assert excinfo.value.reason_code == "document_directory_symlink"
