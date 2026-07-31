"""Authenticated Arc operator client for the non-executing Supervisor path."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import ipaddress
import json
from pathlib import Path
import re
import sqlite3
import threading
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlparse
from uuid import uuid4

from .channel import canonical_json, payload_hash


OPERATOR_CHANNEL_CONTRACT = "operator.channel.envelope"
OPERATOR_REQUEST_CONTRACT = "operator.control_plane.request"
OPERATOR_RESPONSE_CONTRACT = "operator.control_plane.response"
WORKER_INVENTORY_REQUEST_CONTRACT = "operator.worker_inventory.request"
WORKER_INVENTORY_RESPONSE_CONTRACT = "operator.worker_inventory.response"
EVIDENCE_TRACE_REQUEST_CONTRACT = "operator.evidence_trace.request"
EVIDENCE_TRACE_RESPONSE_CONTRACT = "operator.evidence_trace.response"
VERSION = "1.0.0"
MAX_RESPONSE_BYTES = 256 * 1024
SIGNATURE_PATTERN = re.compile(r"^[a-f0-9]{64}$")
HASH_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")


class ArcOperatorAuthenticationError(RuntimeError):
    """Raised when the operator-to-Supervisor boundary fails closed."""


class OperatorResponseReplayStore:
    """Persist signed Supervisor response identities without storing the key."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.RLock()
        if not self.path.parent.is_dir():
            raise ArcOperatorAuthenticationError(
                "operator replay-store directory does not exist"
            )
        try:
            self._connection = sqlite3.connect(
                self.path,
                check_same_thread=False,
            )
            with self._lock, self._connection:
                self._connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS supervisor_responses (
                        tenant_id TEXT NOT NULL,
                        actor_id TEXT NOT NULL,
                        key_id TEXT NOT NULL,
                        message_id TEXT NOT NULL,
                        nonce TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        PRIMARY KEY (tenant_id, actor_id, key_id, message_id),
                        UNIQUE (tenant_id, actor_id, key_id, nonce)
                    )
                    """
                )
        except sqlite3.Error as exc:
            raise ArcOperatorAuthenticationError(
                "operator response replay store is unavailable"
            ) from exc

    def reserve(self, envelope: Mapping[str, Any]) -> None:
        try:
            with self._lock, self._connection:
                self._connection.execute(
                    """
                    INSERT INTO supervisor_responses (
                        tenant_id, actor_id, key_id, message_id, nonce, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        envelope["tenant_id"],
                        envelope["actor_id"],
                        envelope["key_id"],
                        envelope["message_id"],
                        envelope["nonce"],
                        envelope["expires_at"],
                    ),
                )
        except (KeyError, sqlite3.IntegrityError) as exc:
            raise ArcOperatorAuthenticationError(
                "authenticated Supervisor response replay rejected"
            ) from exc
        except sqlite3.Error as exc:
            raise ArcOperatorAuthenticationError(
                "Supervisor response replay reservation failed closed"
            ) from exc

    def close(self) -> None:
        with self._lock:
            self._connection.close()


class SupervisorOperatorChannel:
    """Sign requests and verify responses for one bound operator identity."""

    def __init__(
        self,
        *,
        tenant_id: str,
        customer_context_id: str,
        actor_id: str,
        key_id: str,
        shared_key: bytes,
        replay_store: OperatorResponseReplayStore,
        policy_version: str = "guardian-policy-lab-v1",
        clock: Callable[[], datetime] | None = None,
        ttl_seconds: int = 60,
    ) -> None:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (tenant_id, customer_context_id, actor_id, key_id)
        ):
            raise ArcOperatorAuthenticationError(
                "tenant, customer context, actor, and key identities are required"
            )
        if not isinstance(shared_key, bytes) or len(shared_key) < 32:
            raise ArcOperatorAuthenticationError(
                "lab operator key must contain at least 32 bytes"
            )
        if ttl_seconds < 1 or ttl_seconds > 120:
            raise ArcOperatorAuthenticationError(
                "operator message TTL must be between 1 and 120 seconds"
            )
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id
        self.actor_id = actor_id
        self.key_id = key_id
        self._shared_key = shared_key
        self.replay_store = replay_store
        self.policy_version = policy_version
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.ttl_seconds = ttl_seconds

    def sign_request(
        self,
        payload: Mapping[str, Any],
        *,
        message_id: str | None = None,
        nonce: str | None = None,
    ) -> dict[str, Any]:
        issued = self._utc(self.clock())
        expires = self._utc(self.clock() + timedelta(seconds=self.ttl_seconds))
        identity = message_id or f"operator-msg:{uuid4().hex}"
        envelope = {
            "contract_name": OPERATOR_CHANNEL_CONTRACT,
            "contract_version": VERSION,
            "schema_version": VERSION,
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr:{identity}",
            "causation_id": None,
            "idempotency_key": f"operator-channel:{identity}",
            "producer": {
                "component": "operator_client",
                "produced_at": issued,
            },
            "policy_version": self.policy_version,
            "message_id": identity,
            "actor_id": self.actor_id,
            "message_type": "operator_request",
            "key_id": self.key_id,
            "nonce": nonce or uuid4().hex,
            "payload_hash": payload_hash(payload),
            "signature_algorithm": "hmac-sha256",
            "issued_at": issued,
            "expires_at": expires,
        }
        envelope["signature"] = self._signature(envelope)
        return envelope

    def verify_response(
        self,
        envelope: Mapping[str, Any],
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        candidate = dict(envelope)
        self._validate_envelope_shape(candidate)
        expected = {
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "actor_id": self.actor_id,
            "key_id": self.key_id,
            "message_type": "operator_response",
            "policy_version": self.policy_version,
        }
        if any(candidate.get(key) != value for key, value in expected.items()):
            raise ArcOperatorAuthenticationError(
                "Supervisor response identity or message binding mismatch"
            )
        if candidate["producer"]["component"] != "supervisor":
            raise ArcOperatorAuthenticationError(
                "Supervisor response sender binding mismatch"
            )
        if candidate["payload_hash"] != payload_hash(payload):
            raise ArcOperatorAuthenticationError(
                "Supervisor response payload hash mismatch"
            )
        issued = self._parse_time(candidate["issued_at"])
        expires = self._parse_time(candidate["expires_at"])
        now = self.clock().astimezone(timezone.utc)
        if expires <= now:
            raise ArcOperatorAuthenticationError("Supervisor response expired")
        if issued > now + timedelta(seconds=5):
            raise ArcOperatorAuthenticationError(
                "Supervisor response issued in the future"
            )
        if expires - issued > timedelta(seconds=120):
            raise ArcOperatorAuthenticationError(
                "Supervisor response lifetime is too broad"
            )
        if not hmac.compare_digest(
            candidate["signature"],
            self._signature(candidate),
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor response signature mismatch"
            )
        self.replay_store.reserve(candidate)
        return candidate

    def _signature(self, envelope: Mapping[str, Any]) -> str:
        unsigned = {
            key: value for key, value in envelope.items() if key != "signature"
        }
        return hmac.new(
            self._shared_key,
            canonical_json(unsigned),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _validate_envelope_shape(envelope: Mapping[str, Any]) -> None:
        required = {
            "contract_name",
            "contract_version",
            "schema_version",
            "taxonomy_version",
            "tenant_id",
            "customer_context_id",
            "environment",
            "correlation_id",
            "causation_id",
            "idempotency_key",
            "producer",
            "policy_version",
            "message_id",
            "actor_id",
            "message_type",
            "key_id",
            "nonce",
            "payload_hash",
            "signature_algorithm",
            "signature",
            "issued_at",
            "expires_at",
        }
        if set(envelope) != required:
            raise ArcOperatorAuthenticationError(
                "Supervisor response envelope shape is invalid"
            )
        if envelope.get("contract_name") != OPERATOR_CHANNEL_CONTRACT:
            raise ArcOperatorAuthenticationError(
                "Supervisor response contract identity mismatch"
            )
        if envelope.get("contract_version") != VERSION:
            raise ArcOperatorAuthenticationError(
                "Supervisor response contract version mismatch"
            )
        if envelope.get("schema_version") != VERSION:
            raise ArcOperatorAuthenticationError(
                "Supervisor response schema version mismatch"
            )
        if envelope.get("environment") != "phase0_lab":
            raise ArcOperatorAuthenticationError(
                "Supervisor response environment mismatch"
            )
        if envelope.get("signature_algorithm") != "hmac-sha256":
            raise ArcOperatorAuthenticationError(
                "Supervisor response signature algorithm mismatch"
            )
        if not isinstance(envelope.get("producer"), Mapping):
            raise ArcOperatorAuthenticationError(
                "Supervisor response producer is invalid"
            )
        if not HASH_PATTERN.fullmatch(str(envelope.get("payload_hash", ""))):
            raise ArcOperatorAuthenticationError(
                "Supervisor response payload hash is invalid"
            )
        if not SIGNATURE_PATTERN.fullmatch(str(envelope.get("signature", ""))):
            raise ArcOperatorAuthenticationError(
                "Supervisor response signature is invalid"
            )
        nonce = envelope.get("nonce")
        if not isinstance(nonce, str) or not 16 <= len(nonce) <= 128:
            raise ArcOperatorAuthenticationError(
                "Supervisor response nonce is invalid"
            )

    @staticmethod
    def _utc(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _parse_time(value: str) -> datetime:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
        except (TypeError, ValueError) as exc:
            raise ArcOperatorAuthenticationError(
                "Supervisor response timestamp is invalid"
            ) from exc


class ArcSupervisorPreflightClient:
    """Submit one real operator preflight request and stop before execution."""

    def __init__(
        self,
        *,
        base_url: str,
        channel: SupervisorOperatorChannel,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.channel = channel
        self.timeout_seconds = timeout_seconds
        self._validate_url(self.base_url)

    def submit(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str,
        worker_id: str,
        request_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        allowed_actions = {
            "safe_read",
            "status",
            "external_write",
            "shell",
            "credential_access",
            "file_mutation",
            "unknown",
        }
        if action not in allowed_actions:
            raise ArcOperatorAuthenticationError(
                "operator action is not part of the bounded preflight contract"
            )
        if not all(
            isinstance(value, str) and value.strip()
            for value in (resource_type, resource_id, worker_id)
        ):
            raise ArcOperatorAuthenticationError(
                "operator resource and worker identities are required"
            )
        now = self.channel._utc(self.channel.clock())
        identity = request_id or f"operator-request:{uuid4().hex}"
        payload = {
            "contract_name": OPERATOR_REQUEST_CONTRACT,
            "contract_version": VERSION,
            "schema_version": VERSION,
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.channel.tenant_id,
            "customer_context_id": self.channel.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr:{identity}",
            "causation_id": None,
            "idempotency_key": idempotency_key or f"idem:{identity}",
            "producer": {"component": "operator_client", "produced_at": now},
            "policy_version": self.channel.policy_version,
            "request_id": identity,
            "actor_id": self.channel.actor_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "worker_id": worker_id,
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }
        envelope = self.channel.sign_request(payload)
        response = self._post({"envelope": envelope, "payload": payload})
        self.channel.verify_response(response["envelope"], response["payload"])
        result = dict(response["payload"])
        self._validate_result(result, expected_request_id=identity)
        return result

    def refresh_workers(
        self,
        *,
        request_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Explicitly refresh the Supervisor-owned non-executing inventory."""

        now = self.channel._utc(self.channel.clock())
        identity = request_id or f"worker-inventory:{uuid4().hex}"
        payload = {
            "contract_name": WORKER_INVENTORY_REQUEST_CONTRACT,
            "contract_version": VERSION,
            "schema_version": VERSION,
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.channel.tenant_id,
            "customer_context_id": self.channel.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr:{identity}",
            "causation_id": None,
            "idempotency_key": idempotency_key or f"idem:{identity}",
            "producer": {"component": "operator_client", "produced_at": now},
            "policy_version": self.channel.policy_version,
            "request_id": identity,
            "actor_id": self.channel.actor_id,
            "operation": "refresh_non_executing_worker_status",
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }
        envelope = self.channel.sign_request(payload)
        response = self._post(
            {"envelope": envelope, "payload": payload},
            path="/v1/operator/workers",
        )
        self.channel.verify_response(response["envelope"], response["payload"])
        result = dict(response["payload"])
        self._validate_inventory_result(result, expected_request_id=identity)
        return result

    def read_evidence(
        self,
        *,
        target_request_id: str,
        request_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Request one Guardian-bound redacted evidence trace."""

        if not isinstance(target_request_id, str) or not target_request_id.strip():
            raise ArcOperatorAuthenticationError(
                "target evidence request identity is required"
            )
        now = self.channel._utc(self.channel.clock())
        identity = request_id or f"evidence-query:{uuid4().hex}"
        if identity == target_request_id:
            raise ArcOperatorAuthenticationError(
                "evidence query cannot target its own authorization request"
            )
        payload = {
            "contract_name": EVIDENCE_TRACE_REQUEST_CONTRACT,
            "contract_version": VERSION,
            "schema_version": VERSION,
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.channel.tenant_id,
            "customer_context_id": self.channel.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr:{identity}",
            "causation_id": None,
            "idempotency_key": idempotency_key or f"idem:{identity}",
            "producer": {"component": "operator_client", "produced_at": now},
            "policy_version": self.channel.policy_version,
            "request_id": identity,
            "actor_id": self.channel.actor_id,
            "operation": "read_redacted_evidence_trace",
            "target_request_id": target_request_id,
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }
        envelope = self.channel.sign_request(payload)
        response = self._post(
            {"envelope": envelope, "payload": payload},
            path="/v1/operator/evidence",
        )
        self.channel.verify_response(response["envelope"], response["payload"])
        result = dict(response["payload"])
        self._validate_evidence_result(
            result,
            expected_request_id=identity,
            expected_target_request_id=target_request_id,
        )
        return result

    def _post(
        self,
        body: dict[str, Any],
        *,
        path: str = "/v1/operator/preflight",
    ) -> dict[str, Any]:
        encoded = json.dumps(body, sort_keys=True).encode("utf-8")
        request = urllib_request.Request(
            self.base_url + path,
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib_request.urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                content_length = int(
                    response.headers.get("Content-Length", MAX_RESPONSE_BYTES)
                )
                if content_length < 1 or content_length > MAX_RESPONSE_BYTES:
                    raise ArcOperatorAuthenticationError(
                        "Supervisor response size is invalid"
                    )
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except (
            OSError,
            ValueError,
            urllib_error.HTTPError,
            urllib_error.URLError,
        ) as exc:
            raise ArcOperatorAuthenticationError(
                "Supervisor is unavailable; Arc operator request failed closed"
            ) from exc
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ArcOperatorAuthenticationError(
                "Supervisor response is too large"
            )
        try:
            body = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ArcOperatorAuthenticationError(
                "Supervisor response is not valid JSON"
            ) from exc
        if (
            not isinstance(body, dict)
            or set(body) != {"envelope", "payload"}
            or not isinstance(body["envelope"], dict)
            or not isinstance(body["payload"], dict)
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor response shape is invalid"
            )
        return body

    def _validate_inventory_result(
        self,
        result: Mapping[str, Any],
        *,
        expected_request_id: str,
    ) -> None:
        required = {
            "contract_name",
            "contract_version",
            "schema_version",
            "taxonomy_version",
            "tenant_id",
            "customer_context_id",
            "environment",
            "correlation_id",
            "causation_id",
            "idempotency_key",
            "producer",
            "policy_version",
            "request_id",
            "actor_id",
            "status",
            "classification_authority",
            "worker_count",
            "workers",
            "evidence_refs",
            "reason_codes",
            "runtime_authority_blocked",
            "executable",
            "execution_allowed",
            "side_effects_allowed",
        }
        if set(result) != required:
            raise ArcOperatorAuthenticationError(
                "Supervisor worker inventory shape is invalid"
            )
        expected = {
            "contract_name": WORKER_INVENTORY_RESPONSE_CONTRACT,
            "contract_version": VERSION,
            "schema_version": VERSION,
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.channel.tenant_id,
            "customer_context_id": self.channel.customer_context_id,
            "environment": "phase0_lab",
            "actor_id": self.channel.actor_id,
            "request_id": expected_request_id,
            "classification_authority": "supervisor_server_derived",
            "policy_version": self.channel.policy_version,
        }
        if any(result.get(key) != value for key, value in expected.items()):
            raise ArcOperatorAuthenticationError(
                "Supervisor worker inventory identity or policy binding mismatch"
            )
        producer = result.get("producer")
        if (
            not isinstance(producer, Mapping)
            or set(producer) != {"component", "produced_at"}
            or producer.get("component") != "supervisor"
            or not isinstance(producer.get("produced_at"), str)
            or not producer["produced_at"]
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor worker inventory producer is invalid"
            )
        if not self._is_unique_text_list(
            result.get("evidence_refs")
        ) or not self._is_unique_text_list(result.get("reason_codes")):
            raise ArcOperatorAuthenticationError(
                "Supervisor worker inventory evidence is invalid"
            )
        self._assert_blocked_flags(result, "worker inventory")
        workers = result.get("workers")
        worker_count = result.get("worker_count")
        if (
            not isinstance(workers, list)
            or not isinstance(worker_count, int)
            or not 0 <= worker_count <= 8
            or worker_count != len(workers)
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor worker inventory count is invalid"
            )
        worker_ids = [worker.get("worker_id") for worker in workers if isinstance(worker, Mapping)]
        if (
            len(worker_ids) != len(workers)
            or len(set(worker_ids)) != len(worker_ids)
            or worker_ids != sorted(worker_ids)
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor worker inventory identities are invalid"
            )
        for worker in workers:
            self._validate_inventory_worker(worker)
        status = result.get("status")
        if status == "healthy" and (
            not workers or not all(worker["eligible"] is True for worker in workers)
        ):
            raise ArcOperatorAuthenticationError(
                "healthy inventory contains an ineligible worker"
            )
        if status in {"denied", "unavailable"} and workers:
            raise ArcOperatorAuthenticationError(
                "failed-closed inventory exposed ungoverned worker details"
            )
        if status not in {"healthy", "degraded_read_only", "denied", "unavailable"}:
            raise ArcOperatorAuthenticationError(
                "Supervisor worker inventory status is invalid"
            )

    def _validate_evidence_result(
        self,
        result: Mapping[str, Any],
        *,
        expected_request_id: str,
        expected_target_request_id: str,
    ) -> None:
        required = {
            "contract_name",
            "contract_version",
            "schema_version",
            "taxonomy_version",
            "tenant_id",
            "customer_context_id",
            "environment",
            "correlation_id",
            "causation_id",
            "idempotency_key",
            "producer",
            "policy_version",
            "request_id",
            "target_request_id",
            "actor_id",
            "status",
            "classification_authority",
            "worker_id",
            "guardian_decision_id",
            "lima_decision_id",
            "authorization_evidence_refs",
            "event_count",
            "events",
            "reason_codes",
            "runtime_authority_blocked",
            "executable",
            "execution_allowed",
            "side_effects_allowed",
        }
        if set(result) != required:
            raise ArcOperatorAuthenticationError(
                "Supervisor evidence trace shape is invalid"
            )
        expected = {
            "contract_name": EVIDENCE_TRACE_RESPONSE_CONTRACT,
            "contract_version": VERSION,
            "schema_version": VERSION,
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.channel.tenant_id,
            "customer_context_id": self.channel.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr:{expected_request_id}",
            "causation_id": expected_request_id,
            "policy_version": self.channel.policy_version,
            "request_id": expected_request_id,
            "target_request_id": expected_target_request_id,
            "actor_id": self.channel.actor_id,
            "classification_authority": "supervisor_server_derived",
        }
        if any(result.get(key) != value for key, value in expected.items()):
            raise ArcOperatorAuthenticationError(
                "Supervisor evidence trace identity or policy binding mismatch"
            )
        producer = result.get("producer")
        if (
            not isinstance(producer, Mapping)
            or set(producer) != {"component", "produced_at"}
            or producer.get("component") != "supervisor"
            or not isinstance(producer.get("produced_at"), str)
            or not producer["produced_at"]
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor evidence trace producer is invalid"
            )
        self._assert_blocked_flags(result, "evidence trace")
        if not self._is_unique_text_list(
            result.get("authorization_evidence_refs")
        ) or not self._is_unique_text_list(result.get("reason_codes")):
            raise ArcOperatorAuthenticationError(
                "Supervisor evidence trace references are invalid"
            )
        events = result.get("events")
        event_count = result.get("event_count")
        if (
            not isinstance(events, list)
            or not isinstance(event_count, int)
            or not 0 <= event_count <= 128
            or event_count != len(events)
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor evidence trace count is invalid"
            )
        event_ids: list[str] = []
        for event in events:
            self._validate_evidence_event(
                event,
                expected_target_request_id=expected_target_request_id,
            )
            event_ids.append(event["event_id"])
        if len(event_ids) != len(set(event_ids)):
            raise ArcOperatorAuthenticationError(
                "Supervisor evidence trace contains duplicate events"
            )

        status = result.get("status")
        governed_fields = (
            result.get("worker_id"),
            result.get("guardian_decision_id"),
            result.get("lima_decision_id"),
        )
        if status == "available":
            if (
                not events
                or not all(
                    isinstance(value, str) and bool(value)
                    for value in governed_fields
                )
                or not result["authorization_evidence_refs"]
            ):
                raise ArcOperatorAuthenticationError(
                    "available evidence trace lacks governed authority"
                )
        elif status == "not_found":
            if (
                events
                or result.get("reason_codes") != ["missing_ref"]
                or not all(
                    isinstance(value, str) and bool(value)
                    for value in governed_fields
                )
                or not result["authorization_evidence_refs"]
            ):
                raise ArcOperatorAuthenticationError(
                    "not-found evidence trace is not fail-closed"
                )
        elif status in {"denied", "unavailable"}:
            if events:
                raise ArcOperatorAuthenticationError(
                    "failed-closed evidence trace exposed events"
                )
        else:
            raise ArcOperatorAuthenticationError(
                "Supervisor evidence trace status is invalid"
            )

    def _validate_evidence_event(
        self,
        event: Any,
        *,
        expected_target_request_id: str,
    ) -> None:
        required = {
            "event_id",
            "event_type",
            "actor_id",
            "worker_id",
            "request_id",
            "decision_id",
            "guardian_decision_id",
            "parent_event_id",
            "payload_hash",
            "redacted_summary",
            "outcome",
            "reason_codes",
            "created_at",
            "runtime_authority_blocked",
            "executable",
            "execution_allowed",
            "side_effects_allowed",
        }
        if not isinstance(event, Mapping) or set(event) != required:
            raise ArcOperatorAuthenticationError(
                "Supervisor evidence event shape is invalid"
            )
        self._assert_blocked_flags(event, "evidence event")
        if (
            event.get("actor_id") != self.channel.actor_id
            or event.get("request_id") != expected_target_request_id
            or not isinstance(event.get("event_id"), str)
            or not event["event_id"]
            or not HASH_PATTERN.fullmatch(str(event.get("payload_hash", "")))
            or not isinstance(event.get("redacted_summary"), str)
            or not event["redacted_summary"]
            or len(event["redacted_summary"]) > 240
            or not isinstance(event.get("created_at"), str)
            or not event["created_at"]
            or not self._is_unique_text_list(event.get("reason_codes"))
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor evidence event binding is invalid"
            )
        if event.get("event_type") not in {
            "request_received",
            "guardian_request",
            "guardian_decision",
            "lima_decision",
            "assignment_preview",
            "worker_acknowledgement",
            "worker_registration",
            "worker_heartbeat",
            "evidence_read",
            "denial",
            "failure",
            "approval_requested",
            "approval_expired",
            "replay_rejected",
        } or event.get("outcome") not in {
            "received",
            "allowed_dry_run",
            "confirm_required",
            "privileged_required",
            "acknowledged",
            "rejected",
            "denied",
            "blocked",
            "expired",
            "failed_closed",
        }:
            raise ArcOperatorAuthenticationError(
                "Supervisor evidence event taxonomy is invalid"
            )
        for field in (
            "worker_id",
            "decision_id",
            "guardian_decision_id",
            "parent_event_id",
        ):
            value = event.get(field)
            if value is not None and (
                not isinstance(value, str) or not value
            ):
                raise ArcOperatorAuthenticationError(
                    "Supervisor evidence event reference is invalid"
                )

    def _validate_inventory_worker(self, worker: Any) -> None:
        required = {
            "worker_id",
            "role",
            "capabilities",
            "state",
            "authenticated",
            "eligible",
            "worker_version",
            "last_heartbeat_at",
            "control_plane_status",
            "guardian_decision_id",
            "lima_decision_id",
            "lima_status",
            "assignment_status",
            "evidence_refs",
            "reason_codes",
            "runtime_authority_blocked",
            "executable",
            "execution_allowed",
            "side_effects_allowed",
        }
        if not isinstance(worker, Mapping) or set(worker) != required:
            raise ArcOperatorAuthenticationError(
                "Supervisor worker inventory entry shape is invalid"
            )
        self._assert_blocked_flags(worker, "worker inventory entry")
        if not all(
            isinstance(worker.get(field), str) and worker[field]
            for field in (
                "worker_id",
                "role",
                "control_plane_status",
                "guardian_decision_id",
                "lima_decision_id",
                "lima_status",
            )
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor worker inventory authority evidence is incomplete"
            )
        if not isinstance(worker.get("authenticated"), bool) or not isinstance(
            worker.get("eligible"), bool
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor worker eligibility values are invalid"
            )
        if worker.get("state") not in {
            "registered",
            "healthy",
            "degraded",
            "offline",
            "quarantined",
            "revoked",
            "replaced",
        }:
            raise ArcOperatorAuthenticationError(
                "Supervisor worker lifecycle state is invalid"
            )
        if worker.get("control_plane_status") not in {
            "acknowledged",
            "rejected",
            "blocked",
            "denied",
            "confirm_required",
            "privileged_required",
            "unavailable",
        } or worker.get("lima_status") not in {
            "allowed_dry_run",
            "confirm_required",
            "privileged_required",
            "denied",
        }:
            raise ArcOperatorAuthenticationError(
                "Supervisor worker governed status is invalid"
            )
        if worker.get("assignment_status") not in {
            "acknowledged",
            "rejected",
            None,
        }:
            raise ArcOperatorAuthenticationError(
                "Supervisor worker assignment status is invalid"
            )
        if not self._is_unique_text_list(
            worker.get("capabilities")
        ) or not self._is_unique_text_list(
            worker.get("evidence_refs")
        ) or not self._is_unique_text_list(worker.get("reason_codes")):
            raise ArcOperatorAuthenticationError(
                "Supervisor worker inventory lists are invalid"
            )
        if not (
            worker.get("worker_version") is None
            or (
                isinstance(worker.get("worker_version"), str)
                and bool(worker["worker_version"])
            )
        ) or not (
            worker.get("last_heartbeat_at") is None
            or (
                isinstance(worker.get("last_heartbeat_at"), str)
                and bool(worker["last_heartbeat_at"])
            )
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor worker version or heartbeat is invalid"
            )
        if worker["eligible"] and (
            worker["authenticated"] is not True
            or worker.get("state") not in {"registered", "healthy"}
            or worker.get("control_plane_status") != "acknowledged"
            or worker.get("lima_status") != "allowed_dry_run"
            or worker.get("assignment_status") != "acknowledged"
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor marked an unqualified worker eligible"
            )

    @staticmethod
    def _is_unique_text_list(value: Any) -> bool:
        return (
            isinstance(value, list)
            and all(isinstance(item, str) and bool(item) for item in value)
            and len(value) == len(set(value))
        )

    @staticmethod
    def _assert_blocked_flags(
        value: Mapping[str, Any],
        label: str,
    ) -> None:
        if value.get("runtime_authority_blocked") is not True or any(
            value.get(field) is not False
            for field in ("executable", "execution_allowed", "side_effects_allowed")
        ):
            raise ArcOperatorAuthenticationError(
                f"Supervisor {label} cannot authorize execution"
            )

    def _validate_result(
        self,
        result: Mapping[str, Any],
        *,
        expected_request_id: str,
    ) -> None:
        required = {
            "contract_name",
            "contract_version",
            "schema_version",
            "taxonomy_version",
            "tenant_id",
            "customer_context_id",
            "environment",
            "correlation_id",
            "causation_id",
            "idempotency_key",
            "producer",
            "policy_version",
            "request_id",
            "actor_id",
            "worker_id",
            "status",
            "classification_authority",
            "action_category",
            "guardian",
            "lima",
            "assignment_id",
            "assignment_status",
            "evidence",
            "reason_codes",
            "runtime_authority_blocked",
            "executable",
            "execution_allowed",
            "side_effects_allowed",
        }
        if set(result) != required:
            raise ArcOperatorAuthenticationError(
                "Supervisor result shape is invalid"
            )
        if result.get("contract_name") != OPERATOR_RESPONSE_CONTRACT:
            raise ArcOperatorAuthenticationError(
                "Supervisor result contract mismatch"
            )
        expected = {
            "tenant_id": self.channel.tenant_id,
            "customer_context_id": self.channel.customer_context_id,
            "actor_id": self.channel.actor_id,
            "request_id": expected_request_id,
            "classification_authority": "supervisor_server_derived",
            "policy_version": self.channel.policy_version,
        }
        if any(result.get(key) != value for key, value in expected.items()):
            raise ArcOperatorAuthenticationError(
                "Supervisor result identity or policy binding mismatch"
            )
        if result.get("runtime_authority_blocked") is not True:
            raise ArcOperatorAuthenticationError(
                "Supervisor result must block runtime authority"
            )
        if any(
            result.get(field) is not False
            for field in ("executable", "execution_allowed", "side_effects_allowed")
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor result cannot authorize execution"
            )
        lima = result.get("lima")
        if isinstance(lima, Mapping):
            if lima.get("source_policy") != "guardian_core.policy":
                raise ArcOperatorAuthenticationError(
                    "Supervisor result lacks mandatory Guardian-backed LIMA policy"
                )
            if any(
                lima.get(field) is not False
                for field in (
                    "executable",
                    "execution_allowed",
                    "side_effects_allowed",
                )
            ):
                raise ArcOperatorAuthenticationError(
                    "LIMA result cannot authorize execution"
                )

    @staticmethod
    def _validate_url(base_url: str) -> None:
        parsed = urlparse(base_url)
        if (
            parsed.scheme != "http"
            or parsed.username
            or parsed.password
            or not parsed.hostname
            or parsed.query
            or parsed.fragment
        ):
            raise ArcOperatorAuthenticationError(
                "Supervisor lab URL must be credential-free loopback HTTP"
            )
        if parsed.hostname == "localhost":
            return
        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError as exc:
            raise ArcOperatorAuthenticationError(
                "Supervisor lab URL must use a loopback literal"
            ) from exc
        if not address.is_loopback:
            raise ArcOperatorAuthenticationError(
                "Supervisor lab URL must remain loopback-only"
            )
