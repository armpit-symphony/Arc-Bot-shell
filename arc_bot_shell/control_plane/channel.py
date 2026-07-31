"""Replay-resistant HMAC channel for the lab Supervisor-to-Arc boundary.

The channel authenticates metadata messages only. It does not grant runtime
authority, execute an assignment, or carry provider/tool credentials.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from pathlib import Path
import re
import sqlite3
import threading
from typing import Any
from uuid import uuid4


CHANNEL_CONTRACT = "worker.channel.envelope"
CHANNEL_VERSION = "1.0.0"
MESSAGE_TYPES = {
    "registration_challenge",
    "registration",
    "heartbeat_challenge",
    "heartbeat",
    "assignment_preview",
    "assignment_acknowledgement",
}
SENDER_COMPONENTS = {"supervisor", "worker"}
HASH_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")
SIGNATURE_PATTERN = re.compile(r"^[a-f0-9]{64}$")


class ArcChannelAuthenticationError(RuntimeError):
    """Raised when a control-plane message cannot be authenticated."""


def canonical_json(payload: Mapping[str, Any]) -> bytes:
    """Return the one canonical encoding used by both channel peers."""

    return json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def payload_hash(payload: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(payload)).hexdigest()


class ArcChannelReplayStore:
    """Persist authenticated message identities without persisting channel keys."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.RLock()
        if not self.path.parent.is_dir():
            raise ArcChannelAuthenticationError(
                f"channel replay-store directory does not exist: {self.path.parent}"
            )
        try:
            self._connection = sqlite3.connect(
                self.path,
                check_same_thread=False,
            )
            with self._lock, self._connection:
                self._connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS authenticated_messages (
                        tenant_id TEXT NOT NULL,
                        worker_id TEXT NOT NULL,
                        key_id TEXT NOT NULL,
                        message_id TEXT NOT NULL,
                        nonce TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        PRIMARY KEY (tenant_id, worker_id, key_id, message_id),
                        UNIQUE (tenant_id, worker_id, key_id, nonce)
                    )
                    """
                )
        except sqlite3.Error as exc:
            raise ArcChannelAuthenticationError(
                "channel replay store is unavailable"
            ) from exc

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def reserve(self, envelope: Mapping[str, Any]) -> None:
        try:
            with self._lock, self._connection:
                self._connection.execute(
                    """
                    INSERT INTO authenticated_messages (
                        tenant_id, worker_id, key_id, message_id, nonce, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        envelope["tenant_id"],
                        envelope["worker_id"],
                        envelope["key_id"],
                        envelope["message_id"],
                        envelope["nonce"],
                        envelope["expires_at"],
                    ),
                )
        except (KeyError, sqlite3.IntegrityError) as exc:
            raise ArcChannelAuthenticationError(
                "authenticated channel replay rejected"
            ) from exc
        except sqlite3.Error as exc:
            raise ArcChannelAuthenticationError(
                "channel replay reservation failed closed"
            ) from exc


class ArcWorkerChannel:
    """Sign and verify one worker's short-lived control-plane messages."""

    def __init__(
        self,
        *,
        tenant_id: str,
        customer_context_id: str,
        worker_id: str,
        key_id: str,
        shared_key: bytes,
        replay_store: ArcChannelReplayStore,
        policy_version: str = "policy-phase0-v1",
        clock: Callable[[], datetime] | None = None,
        ttl_seconds: int = 60,
    ) -> None:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (tenant_id, customer_context_id, worker_id, key_id)
        ):
            raise ArcChannelAuthenticationError(
                "tenant, customer context, worker, and key identities are required"
            )
        if not isinstance(shared_key, bytes) or len(shared_key) < 32:
            raise ArcChannelAuthenticationError(
                "lab channel key must contain at least 32 bytes"
            )
        if ttl_seconds < 1 or ttl_seconds > 120:
            raise ArcChannelAuthenticationError(
                "channel message TTL must be between 1 and 120 seconds"
            )
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id
        self.worker_id = worker_id
        self.key_id = key_id
        self._shared_key = shared_key
        self.replay_store = replay_store
        self.policy_version = policy_version
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.ttl_seconds = ttl_seconds

    def sign(
        self,
        payload: Mapping[str, Any],
        *,
        message_type: str,
        sender_component: str,
        message_id: str | None = None,
        nonce: str | None = None,
    ) -> dict[str, Any]:
        if message_type not in MESSAGE_TYPES:
            raise ArcChannelAuthenticationError("unsupported channel message type")
        if sender_component not in SENDER_COMPONENTS:
            raise ArcChannelAuthenticationError("unsupported channel sender")
        issued = self._utc(self.clock())
        expires = self._utc(self.clock() + timedelta(seconds=self.ttl_seconds))
        message_identity = message_id or f"msg:{uuid4().hex}"
        envelope = {
            "contract_name": CHANNEL_CONTRACT,
            "contract_version": CHANNEL_VERSION,
            "schema_version": CHANNEL_VERSION,
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr:{message_identity}",
            "causation_id": None,
            "idempotency_key": f"channel:{message_identity}",
            "producer": {
                "component": sender_component,
                "produced_at": issued,
            },
            "policy_version": self.policy_version,
            "message_id": message_identity,
            "worker_id": self.worker_id,
            "message_type": message_type,
            "key_id": self.key_id,
            "nonce": nonce or uuid4().hex,
            "payload_hash": payload_hash(payload),
            "signature_algorithm": "hmac-sha256",
            "issued_at": issued,
            "expires_at": expires,
        }
        envelope["signature"] = self._signature(envelope)
        return envelope

    def verify(
        self,
        envelope: Mapping[str, Any],
        payload: Mapping[str, Any],
        *,
        expected_message_type: str,
        expected_sender_component: str,
    ) -> dict[str, Any]:
        candidate = dict(envelope)
        self._validate_shape(candidate)
        expected_identity = {
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "worker_id": self.worker_id,
            "key_id": self.key_id,
            "message_type": expected_message_type,
        }
        if any(candidate.get(key) != value for key, value in expected_identity.items()):
            raise ArcChannelAuthenticationError(
                "channel tenant, worker, key, or message binding mismatch"
            )
        producer = candidate["producer"]
        if producer.get("component") != expected_sender_component:
            raise ArcChannelAuthenticationError("channel sender binding mismatch")
        if candidate["payload_hash"] != payload_hash(payload):
            raise ArcChannelAuthenticationError("channel payload hash mismatch")

        issued = self._parse_time(candidate["issued_at"])
        expires = self._parse_time(candidate["expires_at"])
        now = self.clock().astimezone(timezone.utc)
        if expires <= now:
            raise ArcChannelAuthenticationError("channel message expired")
        if issued > now + timedelta(seconds=5):
            raise ArcChannelAuthenticationError("channel message issued in the future")
        if expires - issued > timedelta(seconds=120):
            raise ArcChannelAuthenticationError("channel message lifetime is too broad")

        supplied_signature = candidate.pop("signature")
        expected_signature = self._signature(candidate)
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise ArcChannelAuthenticationError("channel signature mismatch")
        candidate["signature"] = supplied_signature
        self.replay_store.reserve(candidate)
        return candidate

    def _signature(self, envelope: Mapping[str, Any]) -> str:
        unsigned = {key: value for key, value in envelope.items() if key != "signature"}
        return hmac.new(
            self._shared_key,
            canonical_json(unsigned),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _validate_shape(envelope: Mapping[str, Any]) -> None:
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
            "worker_id",
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
            raise ArcChannelAuthenticationError("channel envelope shape is invalid")
        if envelope.get("contract_name") != CHANNEL_CONTRACT:
            raise ArcChannelAuthenticationError("channel contract identity mismatch")
        if envelope.get("contract_version") != CHANNEL_VERSION:
            raise ArcChannelAuthenticationError("channel contract version mismatch")
        if envelope.get("schema_version") != CHANNEL_VERSION:
            raise ArcChannelAuthenticationError("channel schema version mismatch")
        if envelope.get("environment") != "phase0_lab":
            raise ArcChannelAuthenticationError("channel environment mismatch")
        if envelope.get("message_type") not in MESSAGE_TYPES:
            raise ArcChannelAuthenticationError("unsupported channel message type")
        if envelope.get("signature_algorithm") != "hmac-sha256":
            raise ArcChannelAuthenticationError("unsupported channel signature algorithm")
        if not HASH_PATTERN.fullmatch(str(envelope.get("payload_hash") or "")):
            raise ArcChannelAuthenticationError("channel payload hash is invalid")
        if not SIGNATURE_PATTERN.fullmatch(str(envelope.get("signature") or "")):
            raise ArcChannelAuthenticationError("channel signature is invalid")
        if not isinstance(envelope.get("producer"), dict):
            raise ArcChannelAuthenticationError("channel producer is invalid")
        for field in (
            "tenant_id",
            "customer_context_id",
            "correlation_id",
            "idempotency_key",
            "policy_version",
            "message_id",
            "worker_id",
            "key_id",
            "nonce",
            "issued_at",
            "expires_at",
        ):
            if not isinstance(envelope.get(field), str) or not envelope[field]:
                raise ArcChannelAuthenticationError(
                    f"channel envelope field is missing: {field}"
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
            raise ArcChannelAuthenticationError(
                "channel timestamp is invalid"
            ) from exc
