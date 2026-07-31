"""Arc operator-to-Supervisor preflight client tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from typing import Any

import pytest

from arc_bot_shell.control_plane.operator_cli import _parser, _read_operator_key
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


def test_operator_key_is_stdin_only_and_parser_requires_bound_inputs() -> None:
    assert _read_operator_key(StringIO("11" * 32 + "\n")) == bytes.fromhex(
        "11" * 32
    )
    with pytest.raises(SystemExit):
        _read_operator_key(StringIO(""))
    with pytest.raises(SystemExit):
        _parser().parse_args([])


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
