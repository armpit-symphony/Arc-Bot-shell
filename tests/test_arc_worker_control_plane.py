"""Authenticated Arc worker control-plane boundary tests."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import Any
from urllib import request as urllib_request

import pytest

from arc_bot_shell.control_plane import (
    ArcChannelReplayStore,
    ArcWorkerChannel,
    ArcWorkerPreviewService,
    build_worker_preview_server,
)
from arc_bot_shell.control_plane.channel import ArcChannelAuthenticationError


FIXED_TIME = datetime(2026, 7, 25, 5, 0, tzinfo=timezone.utc)
SHARED_KEY = bytes.fromhex("11" * 32)


@pytest.fixture
def channel_pair() -> tuple[ArcWorkerChannel, ArcWorkerChannel]:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        supervisor_store = ArcChannelReplayStore(root / "supervisor.db")
        worker_store = ArcChannelReplayStore(root / "worker.db")
        common: dict[str, Any] = {
            "tenant_id": "tenant-lab-001",
            "customer_context_id": "customer-context-main",
            "worker_id": "arc-worker-001",
            "key_id": "lab-key-001",
            "shared_key": SHARED_KEY,
            "clock": lambda: FIXED_TIME,
        }
        supervisor = ArcWorkerChannel(
            **common,
            replay_store=supervisor_store,
        )
        worker = ArcWorkerChannel(
            **common,
            replay_store=worker_store,
        )
        try:
            yield supervisor, worker
        finally:
            supervisor_store.close()
            worker_store.close()


def _challenge(challenge_id: str) -> dict[str, object]:
    return {
        "challenge_id": challenge_id,
        "runtime_authority_blocked": True,
        "executable": False,
        "execution_allowed": False,
        "side_effects_allowed": False,
    }


def _assignment() -> dict[str, object]:
    return {
        "contract_name": "worker.assignment.preview",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "taxonomy_version": "taxonomy-recon-v1",
        "tenant_id": "tenant-lab-001",
        "customer_context_id": "customer-context-main",
        "environment": "phase0_lab",
        "correlation_id": "corr:request-001",
        "causation_id": "decision:request-001",
        "idempotency_key": "assignment:request-001",
        "producer": {
            "component": "supervisor",
            "produced_at": "2026-07-25T05:00:00Z",
        },
        "policy_version": "policy-phase0-v1",
        "assignment_id": "assignment:request-001",
        "request_id": "request-001",
        "guardian_decision_id": "guardian:request-001",
        "lima_decision_id": "lima:request-001",
        "worker_id": "arc-worker-001",
        "capability": "document_read",
        "status": "offered",
        "reason_codes": [],
        "evidence_refs": ["evidence:request-001"],
        "runtime_authority_blocked": True,
        "executable": False,
        "execution_allowed": False,
        "side_effects_allowed": False,
        "created_at": "2026-07-25T05:00:00Z",
        "acknowledged_at": None,
    }


def _service(worker_channel: ArcWorkerChannel) -> ArcWorkerPreviewService:
    return ArcWorkerPreviewService(
        channel=worker_channel,
        worker_role="general_office_arc_worker",
        capabilities=("document_read", "it_diagnostics_read_only"),
        worker_version="arc-bot-shell-0.1.0",
        boot_id="boot-lab-001",
    )


def test_channel_authenticates_exact_payload_and_rejects_replay(
    channel_pair: tuple[ArcWorkerChannel, ArcWorkerChannel],
) -> None:
    supervisor, worker = channel_pair
    payload = _challenge("challenge-001")
    envelope = supervisor.sign(
        payload,
        message_type="registration_challenge",
        sender_component="supervisor",
        message_id="message-001",
        nonce="nonce-001",
    )

    verified = worker.verify(
        envelope,
        payload,
        expected_message_type="registration_challenge",
        expected_sender_component="supervisor",
    )
    assert verified["worker_id"] == "arc-worker-001"

    with pytest.raises(
        ArcChannelAuthenticationError,
        match="replay rejected",
    ):
        worker.verify(
            envelope,
            payload,
            expected_message_type="registration_challenge",
            expected_sender_component="supervisor",
        )


def test_channel_rejects_tamper_wrong_tenant_and_execution_claim(
    channel_pair: tuple[ArcWorkerChannel, ArcWorkerChannel],
) -> None:
    supervisor, worker = channel_pair
    payload = _challenge("challenge-002")
    envelope = supervisor.sign(
        payload,
        message_type="heartbeat_challenge",
        sender_component="supervisor",
    )

    tampered = dict(payload)
    tampered["challenge_id"] = "changed"
    with pytest.raises(ArcChannelAuthenticationError, match="payload hash mismatch"):
        worker.verify(
            envelope,
            tampered,
            expected_message_type="heartbeat_challenge",
            expected_sender_component="supervisor",
        )

    wrong_tenant = dict(envelope)
    wrong_tenant["tenant_id"] = "tenant-other"
    with pytest.raises(ArcChannelAuthenticationError, match="binding mismatch"):
        worker.verify(
            wrong_tenant,
            payload,
            expected_message_type="heartbeat_challenge",
            expected_sender_component="supervisor",
        )


def test_registration_heartbeat_and_assignment_acknowledgement_are_non_executing(
    channel_pair: tuple[ArcWorkerChannel, ArcWorkerChannel],
) -> None:
    supervisor, worker = channel_pair
    service = _service(worker)
    paths_and_types = (
        (
            "/v1/registration",
            "registration_challenge",
            "registration",
            _challenge("registration-challenge"),
        ),
        (
            "/v1/heartbeat",
            "heartbeat_challenge",
            "heartbeat",
            _challenge("heartbeat-challenge"),
        ),
        (
            "/v1/assignment-preview",
            "assignment_preview",
            "assignment_acknowledgement",
            _assignment(),
        ),
    )

    for path, request_type, response_type, payload in paths_and_types:
        envelope = supervisor.sign(
            payload,
            message_type=request_type,
            sender_component="supervisor",
        )
        response = service.handle(path, {"envelope": envelope, "payload": payload})
        response_payload = response["payload"]
        supervisor.verify(
            response["envelope"],
            response_payload,
            expected_message_type=response_type,
            expected_sender_component="worker",
        )
        if "runtime_authority_blocked" in response_payload:
            assert response_payload["runtime_authority_blocked"] is True
            assert response_payload["executable"] is False
            assert response_payload["execution_allowed"] is False
            assert response_payload["side_effects_allowed"] is False

    assert service.heartbeat_sequence == 1
    assert service.received_assignments[0]["status"] == "acknowledged"
    assert service.received_assignments[0]["execution_allowed"] is False


def test_assignment_with_execution_claim_fails_before_acknowledgement(
    channel_pair: tuple[ArcWorkerChannel, ArcWorkerChannel],
) -> None:
    supervisor, worker = channel_pair
    service = _service(worker)
    assignment = _assignment()
    assignment["execution_allowed"] = True
    envelope = supervisor.sign(
        assignment,
        message_type="assignment_preview",
        sender_component="supervisor",
    )

    with pytest.raises(
        RuntimeError,
        match="cannot authorize execution",
    ):
        service.handle(
            "/v1/assignment-preview",
            {"envelope": envelope, "payload": assignment},
        )
    assert service.received_assignments == []


def test_foreground_http_endpoint_redacts_authentication_failure(
    channel_pair: tuple[ArcWorkerChannel, ArcWorkerChannel],
) -> None:
    supervisor, worker = channel_pair
    service = _service(worker)
    server = build_worker_preview_server(host="127.0.0.1", port=0, service=service)
    payload = _challenge("http-challenge")
    envelope = supervisor.sign(
        payload,
        message_type="registration_challenge",
        sender_component="supervisor",
    )
    envelope["signature"] = "0" * 64
    encoded = json.dumps({"envelope": envelope, "payload": payload}).encode("utf-8")
    request = urllib_request.Request(
        f"http://127.0.0.1:{server.server_port}/v1/registration",
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    # The production server is foreground-only. A test helper handles exactly
    # one request so this proves the real HTTP adapter without creating a
    # product scheduler or background service.
    import threading

    thread = threading.Thread(target=server.handle_request)
    thread.start()
    try:
        with pytest.raises(Exception) as exc_info:
            urllib_request.urlopen(request, timeout=2)
        thread.join(timeout=2)
    finally:
        server.server_close()

    assert "signature mismatch" not in str(exc_info.value)
    assert service.received_assignments == []


def test_foreground_http_endpoint_serves_authenticated_registration(
    channel_pair: tuple[ArcWorkerChannel, ArcWorkerChannel],
) -> None:
    supervisor, worker = channel_pair
    service = _service(worker)
    server = build_worker_preview_server(host="127.0.0.1", port=0, service=service)
    payload = _challenge("http-registration-challenge")
    envelope = supervisor.sign(
        payload,
        message_type="registration_challenge",
        sender_component="supervisor",
    )
    encoded = json.dumps({"envelope": envelope, "payload": payload}).encode("utf-8")
    request = urllib_request.Request(
        f"http://127.0.0.1:{server.server_port}/v1/registration",
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    import threading

    thread = threading.Thread(target=server.handle_request)
    thread.start()
    try:
        with urllib_request.urlopen(request, timeout=2) as response:
            body = json.loads(response.read())
        thread.join(timeout=2)
    finally:
        server.server_close()

    supervisor.verify(
        body["envelope"],
        body["payload"],
        expected_message_type="registration",
        expected_sender_component="worker",
    )
    assert body["payload"]["worker_id"] == "arc-worker-001"
    assert body["payload"]["runtime_authority_blocked"] is True
    assert body["payload"]["execution_allowed"] is False
