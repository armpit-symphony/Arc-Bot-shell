"""Arc operator-to-Supervisor preflight client tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from typing import Any

import pytest

from arc_bot_shell.control_plane.operator_cli import _parser, _read_operator_key
from arc_bot_shell.control_plane.evidence_cli import (
    _parser as _evidence_parser,
)
from arc_bot_shell.control_plane.worker_inventory_cli import (
    _parser as _inventory_parser,
)
from arc_bot_shell.control_plane.operator_client import (
    ArcOperatorAuthenticationError,
    ArcSupervisorPreflightClient,
    OperatorResponseReplayStore,
    SupervisorOperatorChannel,
)
from arc_bot_shell.control_plane.channel import payload_hash


NOW = datetime(2026, 7, 26, 1, 0, tzinfo=timezone.utc)


@pytest.fixture
def channel(
    tmp_path: Path,
) -> tuple[SupervisorOperatorChannel, OperatorResponseReplayStore]:
    store = OperatorResponseReplayStore(tmp_path / "responses.db")
    channel = SupervisorOperatorChannel(
        tenant_id="tenant-lab-001",
        customer_context_id="customer-context-main",
        actor_id="operator-lab-001",
        key_id="operator-key-001",
        shared_key=b"o" * 32,
        replay_store=store,
        clock=lambda: NOW,
    )
    yield channel, store
    store.close()


def _result() -> dict[str, Any]:
    return {
        "contract_name": "operator.control_plane.response",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "taxonomy_version": "taxonomy-recon-v1",
        "tenant_id": "tenant-lab-001",
        "customer_context_id": "customer-context-main",
        "environment": "phase0_lab",
        "correlation_id": "corr:request-001",
        "causation_id": "request-001",
        "idempotency_key": "response:idem-001",
        "producer": {
            "component": "supervisor",
            "produced_at": "2026-07-26T01:00:00Z",
        },
        "policy_version": "guardian-policy-lab-v1",
        "request_id": "request-001",
        "actor_id": "operator-lab-001",
        "worker_id": "arc-worker-001",
        "status": "acknowledged",
        "classification_authority": "supervisor_server_derived",
        "action_category": "informational",
        "guardian": {"decision_id": "guardian-decision-001"},
        "lima": {
            "decision_id": "lima-decision-001",
            "source_policy": "guardian_core.policy",
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        },
        "assignment_id": "assignment-001",
        "assignment_status": "acknowledged",
        "evidence": [{"event_id": "event-001"}],
        "reason_codes": [],
        "runtime_authority_blocked": True,
        "executable": False,
        "execution_allowed": False,
        "side_effects_allowed": False,
    }


def _response_envelope(
    channel: SupervisorOperatorChannel,
    payload: dict[str, Any],
) -> dict[str, Any]:
    issued = channel._utc(NOW)
    envelope = {
        "contract_name": "operator.channel.envelope",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "taxonomy_version": "taxonomy-recon-v1",
        "tenant_id": "tenant-lab-001",
        "customer_context_id": "customer-context-main",
        "environment": "phase0_lab",
        "correlation_id": "corr:response-message-001",
        "causation_id": None,
        "idempotency_key": "operator-channel:response-message-001",
        "producer": {"component": "supervisor", "produced_at": issued},
        "policy_version": "guardian-policy-lab-v1",
        "message_id": "response-message-001",
        "actor_id": "operator-lab-001",
        "message_type": "operator_response",
        "key_id": "operator-key-001",
        "nonce": "00112233445566778899aabbccddeeff",
        "payload_hash": payload_hash(payload),
        "signature_algorithm": "hmac-sha256",
        "issued_at": issued,
        "expires_at": channel._utc(NOW + timedelta(seconds=60)),
    }
    envelope["signature"] = channel._signature(envelope)
    return envelope


def _inventory_result(worker_count: int = 1) -> dict[str, Any]:
    workers = []
    for index in range(1, worker_count + 1):
        workers.append(
            {
                "worker_id": f"arc-worker-{index:03d}",
                "role": "general_office_arc_worker",
                "capabilities": ["document_read"],
                "state": "healthy",
                "authenticated": True,
                "eligible": True,
                "worker_version": "arc-bot-shell-0.1.0",
                "last_heartbeat_at": "2026-07-26T01:00:00Z",
                "control_plane_status": "acknowledged",
                "guardian_decision_id": f"guardian-decision-{index:03d}",
                "lima_decision_id": f"lima-decision-{index:03d}",
                "lima_status": "allowed_dry_run",
                "assignment_status": "acknowledged",
                "evidence_refs": [f"event-{index:03d}"],
                "reason_codes": [],
                "runtime_authority_blocked": True,
                "executable": False,
                "execution_allowed": False,
                "side_effects_allowed": False,
            }
        )
    return {
        "contract_name": "operator.worker_inventory.response",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "taxonomy_version": "taxonomy-recon-v1",
        "tenant_id": "tenant-lab-001",
        "customer_context_id": "customer-context-main",
        "environment": "phase0_lab",
        "correlation_id": "corr:worker-inventory-001",
        "causation_id": "worker-inventory-001",
        "idempotency_key": "response:idem:worker-inventory-001",
        "producer": {
            "component": "supervisor",
            "produced_at": "2026-07-26T01:00:00Z",
        },
        "policy_version": "guardian-policy-lab-v1",
        "request_id": "worker-inventory-001",
        "actor_id": "operator-lab-001",
        "status": "healthy",
        "classification_authority": "supervisor_server_derived",
        "worker_count": worker_count,
        "workers": workers,
        "evidence_refs": [f"event-{index:03d}" for index in range(1, worker_count + 1)],
        "reason_codes": [],
        "runtime_authority_blocked": True,
        "executable": False,
        "execution_allowed": False,
        "side_effects_allowed": False,
    }


def _evidence_result(
    *,
    status: str = "available",
    include_event: bool = True,
) -> dict[str, Any]:
    events = (
        [
            {
                "event_id": "target-event-001",
                "event_type": "request_received",
                "actor_id": "operator-lab-001",
                "worker_id": "arc-worker-001",
                "request_id": "operator-request-target-001",
                "decision_id": None,
                "guardian_decision_id": None,
                "parent_event_id": None,
                "payload_hash": "sha256:" + "4" * 64,
                "redacted_summary": "Operator request received and normalized.",
                "outcome": "received",
                "reason_codes": [],
                "created_at": "2026-07-26T01:00:00Z",
                "runtime_authority_blocked": True,
                "executable": False,
                "execution_allowed": False,
                "side_effects_allowed": False,
            }
        ]
        if include_event
        else []
    )
    return {
        "contract_name": "operator.evidence_trace.response",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "taxonomy_version": "taxonomy-recon-v1",
        "tenant_id": "tenant-lab-001",
        "customer_context_id": "customer-context-main",
        "environment": "phase0_lab",
        "correlation_id": "corr:evidence-query-001",
        "causation_id": "evidence-query-001",
        "idempotency_key": "response:idem:evidence-query-001",
        "producer": {
            "component": "supervisor",
            "produced_at": "2026-07-26T01:00:00Z",
        },
        "policy_version": "guardian-policy-lab-v1",
        "request_id": "evidence-query-001",
        "target_request_id": "operator-request-target-001",
        "actor_id": "operator-lab-001",
        "status": status,
        "classification_authority": "supervisor_server_derived",
        "worker_id": "arc-worker-001",
        "guardian_decision_id": "guardian-decision-001",
        "lima_decision_id": "lima-decision-001",
        "authorization_evidence_refs": [
            "authorization-event-001",
            "authorization-event-002",
        ],
        "event_count": len(events),
        "events": events,
        "reason_codes": ["missing_ref"] if status == "not_found" else [],
        "runtime_authority_blocked": True,
        "executable": False,
        "execution_allowed": False,
        "side_effects_allowed": False,
    }


def test_operator_key_is_stdin_only_and_parser_requires_bound_inputs() -> None:
    assert _read_operator_key(StringIO("11" * 32 + "\n")) == bytes.fromhex(
        "11" * 32
    )
    with pytest.raises(SystemExit):
        _read_operator_key(StringIO(""))
    with pytest.raises(SystemExit):
        _parser().parse_args([])
    with pytest.raises(SystemExit):
        _inventory_parser().parse_args([])
    with pytest.raises(SystemExit):
        _evidence_parser().parse_args([])


def test_signed_request_contains_no_classification_or_execution_authority(
    channel: tuple[SupervisorOperatorChannel, OperatorResponseReplayStore],
) -> None:
    operator_channel, _ = channel
    request = {
        "contract_name": "operator.control_plane.request",
        "action": "safe_read",
        "runtime_authority_blocked": True,
        "executable": False,
        "execution_allowed": False,
        "side_effects_allowed": False,
    }
    envelope = operator_channel.sign_request(request)
    assert envelope["actor_id"] == "operator-lab-001"
    assert envelope["payload_hash"] == payload_hash(request)
    assert "action_category" not in request
    assert "actor_role" not in request


def test_supervisor_response_signature_and_replay_fail_closed(
    channel: tuple[SupervisorOperatorChannel, OperatorResponseReplayStore],
) -> None:
    operator_channel, _ = channel
    result = _result()
    envelope = _response_envelope(operator_channel, result)
    operator_channel.verify_response(envelope, result)
    with pytest.raises(ArcOperatorAuthenticationError, match="replay"):
        operator_channel.verify_response(envelope, result)


def test_result_cannot_enable_execution_or_use_static_lima_policy(
    channel: tuple[SupervisorOperatorChannel, OperatorResponseReplayStore],
) -> None:
    operator_channel, _ = channel
    client = ArcSupervisorPreflightClient(
        base_url="http://127.0.0.1:8123",
        channel=operator_channel,
    )
    result = _result()
    client._validate_result(result, expected_request_id="request-001")

    result["execution_allowed"] = True
    with pytest.raises(ArcOperatorAuthenticationError):
        client._validate_result(result, expected_request_id="request-001")

    result = _result()
    result["unexpected_authority"] = True
    with pytest.raises(ArcOperatorAuthenticationError):
        client._validate_result(result, expected_request_id="request-001")

    result = _result()
    result["lima"]["source_policy"] = "static_default"  # type: ignore[index]
    with pytest.raises(ArcOperatorAuthenticationError):
        client._validate_result(result, expected_request_id="request-001")


@pytest.mark.parametrize(
    "url",
    [
        "http://0.0.0.0:8123",
        "http://192.168.1.10:8123",
        "https://127.0.0.1:8123",
        "http://user:pass@127.0.0.1:8123",
    ],
)
def test_operator_client_rejects_non_loopback_or_credentialed_url(
    channel: tuple[SupervisorOperatorChannel, OperatorResponseReplayStore],
    url: str,
) -> None:
    operator_channel, _ = channel
    with pytest.raises(ArcOperatorAuthenticationError):
        ArcSupervisorPreflightClient(base_url=url, channel=operator_channel)


def test_inventory_refresh_contains_no_client_worker_or_authority_selection(
    channel: tuple[SupervisorOperatorChannel, OperatorResponseReplayStore],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    operator_channel, _ = channel
    client = ArcSupervisorPreflightClient(
        base_url="http://127.0.0.1:8123",
        channel=operator_channel,
    )
    captured: dict[str, Any] = {}
    result = _inventory_result()

    def fake_post(
        body: dict[str, Any],
        *,
        path: str = "/v1/operator/preflight",
    ) -> dict[str, Any]:
        captured["body"] = body
        captured["path"] = path
        return {
            "envelope": _response_envelope(operator_channel, result),
            "payload": result,
        }

    monkeypatch.setattr(client, "_post", fake_post)
    actual = client.refresh_workers(
        request_id="worker-inventory-001",
        idempotency_key="idem:worker-inventory-001",
    )
    payload = captured["body"]["payload"]
    assert captured["path"] == "/v1/operator/workers"
    assert actual["worker_count"] == 1
    assert payload["operation"] == "refresh_non_executing_worker_status"
    for forbidden in (
        "worker_id",
        "worker_ids",
        "role",
        "capabilities",
        "eligible",
        "action",
        "action_category",
        "classification_authority",
        "actor_role",
    ):
        assert forbidden not in payload


@pytest.mark.parametrize("worker_count", [1, 2, 8])
def test_inventory_validates_one_to_eight_governed_workers(
    channel: tuple[SupervisorOperatorChannel, OperatorResponseReplayStore],
    worker_count: int,
) -> None:
    operator_channel, _ = channel
    client = ArcSupervisorPreflightClient(
        base_url="http://127.0.0.1:8123",
        channel=operator_channel,
    )
    result = _inventory_result(worker_count)
    client._validate_inventory_result(
        result,
        expected_request_id="worker-inventory-001",
    )
    assert all(worker["eligible"] for worker in result["workers"])
    assert all(
        worker["runtime_authority_blocked"]
        and not worker["executable"]
        and not worker["execution_allowed"]
        and not worker["side_effects_allowed"]
        for worker in result["workers"]
    )


def test_inventory_tampering_fails_closed(
    channel: tuple[SupervisorOperatorChannel, OperatorResponseReplayStore],
) -> None:
    operator_channel, _ = channel
    client = ArcSupervisorPreflightClient(
        base_url="http://127.0.0.1:8123",
        channel=operator_channel,
    )
    tampered = _inventory_result(2)
    tampered["workers"][1]["worker_id"] = tampered["workers"][0]["worker_id"]
    with pytest.raises(ArcOperatorAuthenticationError):
        client._validate_inventory_result(
            tampered,
            expected_request_id="worker-inventory-001",
        )


def test_evidence_read_contains_no_client_worker_or_authority_selection(
    channel: tuple[SupervisorOperatorChannel, OperatorResponseReplayStore],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    operator_channel, _ = channel
    client = ArcSupervisorPreflightClient(
        base_url="http://127.0.0.1:8123",
        channel=operator_channel,
    )
    captured: dict[str, Any] = {}
    result = _evidence_result()

    def fake_post(
        body: dict[str, Any],
        *,
        path: str = "/v1/operator/preflight",
    ) -> dict[str, Any]:
        captured["body"] = body
        captured["path"] = path
        return {
            "envelope": _response_envelope(operator_channel, result),
            "payload": result,
        }

    monkeypatch.setattr(client, "_post", fake_post)
    actual = client.read_evidence(
        target_request_id="operator-request-target-001",
        request_id="evidence-query-001",
        idempotency_key="idem:evidence-query-001",
    )
    payload = captured["body"]["payload"]
    assert captured["path"] == "/v1/operator/evidence"
    assert actual["status"] == "available"
    assert payload["operation"] == "read_redacted_evidence_trace"
    assert payload["target_request_id"] == "operator-request-target-001"
    for forbidden in (
        "worker_id",
        "worker_ids",
        "role",
        "capabilities",
        "action",
        "action_category",
        "classification_authority",
        "actor_role",
        "authority",
    ):
        assert forbidden not in payload


def test_evidence_trace_validates_available_and_not_found_results(
    channel: tuple[SupervisorOperatorChannel, OperatorResponseReplayStore],
) -> None:
    operator_channel, _ = channel
    client = ArcSupervisorPreflightClient(
        base_url="http://127.0.0.1:8123",
        channel=operator_channel,
    )
    client._validate_evidence_result(
        _evidence_result(),
        expected_request_id="evidence-query-001",
        expected_target_request_id="operator-request-target-001",
    )
    client._validate_evidence_result(
        _evidence_result(status="not_found", include_event=False),
        expected_request_id="evidence-query-001",
        expected_target_request_id="operator-request-target-001",
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("execution_allowed", True),
        ("classification_authority", "client_supplied"),
        ("target_request_id", "other-target"),
        ("actor_id", "operator-other"),
    ],
)
def test_evidence_trace_top_level_tampering_fails_closed(
    channel: tuple[SupervisorOperatorChannel, OperatorResponseReplayStore],
    field: str,
    value: Any,
) -> None:
    operator_channel, _ = channel
    client = ArcSupervisorPreflightClient(
        base_url="http://127.0.0.1:8123",
        channel=operator_channel,
    )
    result = _evidence_result()
    result[field] = value
    with pytest.raises(ArcOperatorAuthenticationError):
        client._validate_evidence_result(
            result,
            expected_request_id="evidence-query-001",
            expected_target_request_id="operator-request-target-001",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("request_id", "other-target"),
        ("actor_id", "operator-other"),
        ("payload_hash", "sha256:not-a-hash"),
        ("execution_allowed", True),
        ("unexpected_secret", "must-not-appear"),
    ],
)
def test_evidence_event_tampering_fails_closed(
    channel: tuple[SupervisorOperatorChannel, OperatorResponseReplayStore],
    field: str,
    value: Any,
) -> None:
    operator_channel, _ = channel
    client = ArcSupervisorPreflightClient(
        base_url="http://127.0.0.1:8123",
        channel=operator_channel,
    )
    result = _evidence_result()
    result["events"][0][field] = value
    with pytest.raises(ArcOperatorAuthenticationError):
        client._validate_evidence_result(
            result,
            expected_request_id="evidence-query-001",
            expected_target_request_id="operator-request-target-001",
        )


def test_evidence_query_self_target_and_missing_target_fail_closed(
    channel: tuple[SupervisorOperatorChannel, OperatorResponseReplayStore],
) -> None:
    operator_channel, _ = channel
    client = ArcSupervisorPreflightClient(
        base_url="http://127.0.0.1:8123",
        channel=operator_channel,
    )
    with pytest.raises(ArcOperatorAuthenticationError):
        client.read_evidence(target_request_id="")
    with pytest.raises(ArcOperatorAuthenticationError):
        client.read_evidence(
            target_request_id="evidence-query-self",
            request_id="evidence-query-self",
        )

    tampered = _inventory_result()
    tampered["workers"][0]["execution_allowed"] = True
    with pytest.raises(ArcOperatorAuthenticationError):
        client._validate_inventory_result(
            tampered,
            expected_request_id="worker-inventory-001",
        )

    tampered = _inventory_result()
    tampered["workers"][0]["state"] = "offline"
    with pytest.raises(ArcOperatorAuthenticationError):
        client._validate_inventory_result(
            tampered,
            expected_request_id="worker-inventory-001",
        )

    tampered = _inventory_result()
    tampered["producer"]["component"] = "worker"
    with pytest.raises(ArcOperatorAuthenticationError):
        client._validate_inventory_result(
            tampered,
            expected_request_id="worker-inventory-001",
        )
