"""Explicit foreground Arc worker endpoint for metadata-only control-plane previews."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
from typing import Any, Mapping

from .channel import ArcChannelAuthenticationError, ArcWorkerChannel


logger = logging.getLogger(__name__)
MAX_REQUEST_BYTES = 128 * 1024


class ArcWorkerPreviewError(RuntimeError):
    """Raised when a worker preview request violates the non-executing contract."""


class ArcWorkerPreviewService:
    """Answer authenticated registration, heartbeat, and assignment previews."""

    def __init__(
        self,
        *,
        channel: ArcWorkerChannel,
        worker_role: str,
        capabilities: tuple[str, ...],
        worker_version: str,
        boot_id: str,
    ) -> None:
        if not worker_role or not capabilities or not worker_version or not boot_id:
            raise ArcWorkerPreviewError(
                "worker role, capabilities, version, and boot identity are required"
            )
        self.channel = channel
        self.worker_role = worker_role
        self.capabilities = tuple(sorted(set(capabilities)))
        self.worker_version = worker_version
        self.boot_id = boot_id
        self.heartbeat_sequence = 0
        self.received_assignments: list[dict[str, Any]] = []

    def handle(
        self,
        path: str,
        body: Mapping[str, Any],
    ) -> dict[str, Any]:
        if set(body) != {"envelope", "payload"}:
            raise ArcWorkerPreviewError("control-plane request shape is invalid")
        envelope = body.get("envelope")
        payload = body.get("payload")
        if not isinstance(envelope, dict) or not isinstance(payload, dict):
            raise ArcWorkerPreviewError("control-plane envelope and payload are required")
        routes = {
            "/v1/registration": (
                "registration_challenge",
                self._registration,
            ),
            "/v1/heartbeat": (
                "heartbeat_challenge",
                self._heartbeat,
            ),
            "/v1/assignment-preview": (
                "assignment_preview",
                self._acknowledge_assignment,
            ),
        }
        try:
            expected_type, handler = routes[path]
        except KeyError as exc:
            raise ArcWorkerPreviewError("unknown control-plane endpoint") from exc
        self.channel.verify(
            envelope,
            payload,
            expected_message_type=expected_type,
            expected_sender_component="supervisor",
        )
        response_payload = handler(payload)
        response_type = {
            "/v1/registration": "registration",
            "/v1/heartbeat": "heartbeat",
            "/v1/assignment-preview": "assignment_acknowledgement",
        }[path]
        response_envelope = self.channel.sign(
            response_payload,
            message_type=response_type,
            sender_component="worker",
        )
        return {"envelope": response_envelope, "payload": response_payload}

    def _registration(self, challenge: Mapping[str, Any]) -> dict[str, Any]:
        self._validate_challenge(challenge)
        now = self._now()
        return {
            "contract_name": "worker.registration",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.channel.tenant_id,
            "customer_context_id": self.channel.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr:registration:{self.channel.worker_id}",
            "causation_id": challenge["challenge_id"],
            "idempotency_key": f"registration:{self.channel.worker_id}:{self.boot_id}",
            "producer": {"component": "worker", "produced_at": now},
            "policy_version": self.channel.policy_version,
            "registration_id": f"registration:{self.channel.worker_id}:{self.boot_id}",
            "worker_id": self.channel.worker_id,
            "worker_role": self.worker_role,
            "channel_identity_ref": self.channel.key_id,
            "boot_id": self.boot_id,
            "worker_version": self.worker_version,
            "capabilities": list(self.capabilities),
            "registration_state": "requested",
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
            "created_at": now,
        }

    def _heartbeat(self, challenge: Mapping[str, Any]) -> dict[str, Any]:
        self._validate_challenge(challenge)
        self.heartbeat_sequence += 1
        now = self._now()
        return {
            "contract_name": "worker.heartbeat",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "taxonomy_version": "taxonomy-reason-v1",
            "tenant_id": self.channel.tenant_id,
            "customer_context_id": self.channel.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr:heartbeat:{self.channel.worker_id}",
            "causation_id": challenge["challenge_id"],
            "idempotency_key": (
                f"heartbeat:{self.channel.worker_id}:{self.boot_id}:"
                f"{self.heartbeat_sequence}"
            ),
            "heartbeat_id": (
                f"heartbeat:{self.channel.worker_id}:{self.boot_id}:"
                f"{self.heartbeat_sequence}"
            ),
            "worker_id": self.channel.worker_id,
            "producer": {"component": "worker", "produced_at": now},
            "heartbeat_sequence": self.heartbeat_sequence,
            "boot_id": self.boot_id,
            "reported_at": now,
            "supervisor_received_at": now,
            "heartbeat_due_at": now,
            "heartbeat_age_seconds": 0,
            "worker_process_uptime_seconds": 0,
            "lifecycle_state": "healthy",
            "health_state": "healthy",
            "data_classification": "internal",
            "risk_tier": "low",
            "current_task_count": 0,
            "queue_depth": 0,
            "capability_manifest_version": self.worker_version,
            "capability_manifest_hash_ref": self._capability_hash_ref(),
            "tool_pack_scope_version": "arc-preview-only-v1",
            "local_model_status": "not_available",
            "update_version": self.worker_version,
            "rollback_version": None,
            "update_status": "current",
            "attestation_status": "not_required_phase0",
            "trust_root_status": "software_only_placeholder",
            "worker_attestation_ref": None,
            "attestation_result_ref": None,
            "appraisal_policy_ref": None,
            "update_rollback_ref": None,
            "evidence_writer_status": "healthy",
            "evidence_spool_depth": 0,
            "last_evidence_write_at": now,
            "last_evidence_error_code": "none",
            "resource_posture": {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "disk_free_percent": 0.0,
            },
            "network_posture": {
                "supervisor_channel": "authenticated",
                "internet_required": False,
                "clock_skew_ms": 0,
            },
            "model_route_status": "not_routed",
            "network_reachability": "supervisor_only",
            "guardian_reachability": "reachable",
            "missed_heartbeat_count": 0,
            "policy_version": self.channel.policy_version,
            "guardian_decision_id": "guardian:not_invoked_for_heartbeat",
            "evidence_artifact_id": f"heartbeat-evidence:{self.channel.worker_id}",
            "evidence_artifact_ids": [
                f"heartbeat-evidence:{self.channel.worker_id}"
            ],
            "operator_action_required": False,
            "runbook_ref": None,
            "last_task_id": None,
            "last_task_status": None,
            "quarantine_reason": None,
        }

    def _acknowledge_assignment(
        self,
        assignment: Mapping[str, Any],
    ) -> dict[str, Any]:
        required = {
            "assignment_id",
            "request_id",
            "tenant_id",
            "worker_id",
            "capability",
            "status",
            "runtime_authority_blocked",
            "executable",
            "execution_allowed",
            "side_effects_allowed",
            "created_at",
        }
        if not required.issubset(assignment):
            raise ArcWorkerPreviewError("assignment preview is incomplete")
        if assignment["tenant_id"] != self.channel.tenant_id:
            raise ArcWorkerPreviewError("assignment tenant mismatch")
        if assignment["worker_id"] != self.channel.worker_id:
            raise ArcWorkerPreviewError("assignment worker mismatch")
        if assignment["capability"] not in self.capabilities:
            raise ArcWorkerPreviewError("assignment capability mismatch")
        if assignment["status"] != "offered":
            raise ArcWorkerPreviewError("assignment is not an offer")
        self._assert_non_executing(assignment)
        acknowledged = copy.deepcopy(dict(assignment))
        acknowledged["producer"] = {
            "component": "worker",
            "produced_at": self._now(),
        }
        acknowledged["status"] = "acknowledged"
        acknowledged["acknowledged_at"] = self._now()
        self.received_assignments.append(copy.deepcopy(acknowledged))
        return acknowledged

    @staticmethod
    def _validate_challenge(challenge: Mapping[str, Any]) -> None:
        if set(challenge) != {
            "challenge_id",
            "runtime_authority_blocked",
            "executable",
            "execution_allowed",
            "side_effects_allowed",
        }:
            raise ArcWorkerPreviewError("worker challenge shape is invalid")
        if not isinstance(challenge["challenge_id"], str) or not challenge["challenge_id"]:
            raise ArcWorkerPreviewError("worker challenge identity is required")
        ArcWorkerPreviewService._assert_non_executing(challenge)

    @staticmethod
    def _assert_non_executing(payload: Mapping[str, Any]) -> None:
        if payload.get("runtime_authority_blocked") is not True:
            raise ArcWorkerPreviewError("runtime authority must remain blocked")
        if any(
            payload.get(field) is not False
            for field in ("executable", "execution_allowed", "side_effects_allowed")
        ):
            raise ArcWorkerPreviewError(
                "worker control-plane preview cannot authorize execution"
            )

    def _capability_hash_ref(self) -> str:
        from .channel import payload_hash

        return payload_hash({"capabilities": list(self.capabilities)})

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class _WorkerPreviewHandler(BaseHTTPRequestHandler):
    server_version = "ArcWorkerPreview/0.1"

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {
            "/v1/registration",
            "/v1/heartbeat",
            "/v1/assignment-preview",
        }:
            self._reply(HTTPStatus.NOT_FOUND, {"status": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > MAX_REQUEST_BYTES:
                raise ArcWorkerPreviewError("request size is invalid")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ArcWorkerPreviewError("request body must be an object")
            response = self.server.preview_service.handle(self.path, body)  # type: ignore[attr-defined]
        except (
            ArcChannelAuthenticationError,
            ArcWorkerPreviewError,
            json.JSONDecodeError,
            UnicodeDecodeError,
            ValueError,
        ):
            logger.exception("Arc worker preview request failed closed")
            self._reply(
                HTTPStatus.FORBIDDEN,
                {
                    "status": "denied",
                    "runtime_authority_blocked": True,
                    "executable": False,
                    "execution_allowed": False,
                    "side_effects_allowed": False,
                },
            )
            return
        except Exception:
            logger.exception("Arc worker preview request failed closed")
            self._reply(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "status": "unavailable",
                    "runtime_authority_blocked": True,
                    "executable": False,
                    "execution_allowed": False,
                    "side_effects_allowed": False,
                },
            )
            return
        self._reply(HTTPStatus.OK, response)

    def log_message(self, format: str, *args: object) -> None:
        logger.info("Arc worker preview HTTP request: " + format, *args)

    def _reply(self, status: HTTPStatus, payload: Mapping[str, Any]) -> None:
        encoded = json.dumps(dict(payload), sort_keys=True).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)


class ArcWorkerPreviewServer(HTTPServer):
    """Single-threaded foreground HTTP server; it starts no hidden jobs."""

    def __init__(
        self,
        server_address: tuple[str, int],
        preview_service: ArcWorkerPreviewService,
    ) -> None:
        self.preview_service = preview_service
        super().__init__(server_address, _WorkerPreviewHandler)


def build_worker_preview_server(
    *,
    host: str,
    port: int,
    service: ArcWorkerPreviewService,
) -> ArcWorkerPreviewServer:
    """Build, but do not background or start, the explicit worker endpoint."""

    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise ArcWorkerPreviewError(
            "the first lab worker endpoint is intentionally loopback-only"
        )
    if port < 0 or port > 65535:
        raise ArcWorkerPreviewError("worker endpoint port is invalid")
    return ArcWorkerPreviewServer((host, port), service)
