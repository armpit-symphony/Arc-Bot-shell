"""Installed LIMA v0.1 RC consumer compatibility proof for Arc."""

from __future__ import annotations

import importlib.metadata
import json
import socket
import threading
from typing import Any

import pytest

from arc_guardian_spine import ArcActionRequest
from arc_guardian_spine.lima_preflight import (
    call_lima_governed_preflight_for_arc_action,
)
from lima.runtime import run_governed_request


LIMA_VERSION = "0.1.0rc1"
LIMA_COMMIT = "4e7c648349f0a5a19694ac5f0c57b5cb14dc2b17"


def _request(action_id: str, action_kind: str) -> ArcActionRequest:
    return ArcActionRequest(
        action_id=action_id,
        action_kind=action_kind,
        operator_id="operator-rc1-proof",
        worker_id="arc-worker-rc1-proof",
        tenant_id="tenant-rc1-proof",
        task_ref="task://arc/rc1-proof",
        payload_summary=f"Arc governed preflight for {action_kind}",
        evidence_refs=("evidence://arc/rc1-proof",),
    )


def test_installed_lima_rc1_uses_exact_commit_and_public_api() -> None:
    matching_distributions = []
    for distribution in importlib.metadata.distributions():
        name = str(distribution.metadata.get("Name", "")).lower()
        if name != "lima-runtime" or distribution.version != LIMA_VERSION:
            continue
        direct_url_text = distribution.read_text("direct_url.json")
        if direct_url_text is None:
            continue
        direct_url = json.loads(direct_url_text)
        if direct_url.get("vcs_info", {}).get("commit_id") == LIMA_COMMIT:
            matching_distributions.append((distribution, direct_url))

    assert len(matching_distributions) == 1
    distribution, direct_url = matching_distributions[0]
    assert not (distribution.requires or [])
    assert callable(run_governed_request)
    assert direct_url["url"] == "https://github.com/armpit-symphony/LIMA-AI-OS.git"
    assert direct_url["vcs_info"]["requested_revision"] == LIMA_COMMIT


@pytest.mark.parametrize(
    ("action_kind", "expected_status"),
    [
        ("status_read", "allowed_dry_run"),
        ("send_email", "confirm_required"),
        ("shell_command_execute", "denied"),
        ("file_write", "confirm_required"),
        ("credential_access", "privileged_required"),
        ("unmapped_future_action", "denied"),
    ],
)
def test_arc_uses_real_lima_rc1_without_side_effects(
    monkeypatch: pytest.MonkeyPatch,
    action_kind: str,
    expected_status: str,
) -> None:
    counters = {
        "provider": 0,
        "model": 0,
        "tool": 0,
        "connector": 0,
        "external_send": 0,
        "credential": 0,
        "file_mutation": 0,
        "network": 0,
        "background": 0,
        "robotics": 0,
        "iot": 0,
        "physical_world": 0,
    }

    def block_network(*args: object, **kwargs: object) -> None:
        counters["network"] += 1
        raise AssertionError("Arc governed preflight attempted network access")

    def block_thread(
        self: threading.Thread, *args: object, **kwargs: object
    ) -> None:
        counters["background"] += 1
        raise AssertionError("Arc governed preflight attempted a background job")

    monkeypatch.setattr(socket.socket, "connect", block_network)
    monkeypatch.setattr(socket.socket, "connect_ex", block_network)
    monkeypatch.setattr(socket, "create_connection", block_network)
    monkeypatch.setattr(socket, "getaddrinfo", block_network)
    monkeypatch.setattr(threading.Thread, "start", block_thread)

    result = call_lima_governed_preflight_for_arc_action(
        _request(f"arc-rc1-{action_kind}", action_kind)
    )

    assert result.lima_available is True
    assert result.decision.status == expected_status
    assert result.decision.executable is False
    assert result.decision.execution_allowed is False
    assert result.decision.side_effects_allowed is False
    assert result.response["runtime_authority_blocked"] is True
    assert result.response["executable"] is False
    assert result.response["execution_allowed"] is False
    assert result.response["side_effects_allowed"] is False
    assert result.response["provider_model_routed"] is False
    assert result.response["tool_executed"] is False
    assert result.response["connector_invoked"] is False
    assert result.response["file_mutation_executed"] is False
    assert result.response["network_action_executed"] is False
    assert all(value == 0 for value in counters.values())


def test_arc_lima_unavailable_fails_closed() -> None:
    def unavailable(_: dict[str, Any]) -> Any:
        raise RuntimeError("LIMA unavailable for compatibility proof")

    result = call_lima_governed_preflight_for_arc_action(
        _request("arc-rc1-unavailable", "status_read"),
        lima_runner=unavailable,
    )

    assert result.lima_available is False
    assert result.decision.status == "denied"
    assert "lima_unavailable" in result.decision.reason_codes
    assert result.response["runtime_authority_blocked"] is True
    assert result.response["executable"] is False
    assert result.response["execution_allowed"] is False
    assert result.response["side_effects_allowed"] is False