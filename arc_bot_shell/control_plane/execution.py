"""Honour a Supervisor execution grant for one bounded read-only capability.

This is the only place in Arc that performs a real side effect, and it is
narrow on purpose:

* Arc keeps its own opt-in, independent of the Supervisor's. Both must be on.
  Either side alone is sufficient to stop execution, so a single
  misconfiguration or a compromised Supervisor is not enough to cause a read.
* Only ``document_read`` is honoured. Anything that writes, sends, or deletes
  has no code path here at all.
* Reads are confined to an explicitly configured root. There is no default
  root, so an unconfigured Arc cannot read anything.

A grant is necessary but never sufficient: ``requires_operator_opt_in`` must be
true on the grant, and Arc's own opt-in must also be on.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HONOURED_CAPABILITIES = frozenset({"document_read"})
# Arc's own view of which capability an action implies. Kept here so Arc can
# check the grant against the action the operator actually asked for, rather
# than against the grant's own claim about itself.
ACTION_CAPABILITIES = {
    "safe_read": "document_read",
    "status": "it_diagnostics_read_only",
    "external_write": "draft_workspace",
    "file_mutation": "file_organize",
}


def expected_capability_for(action: str) -> str | None:
    """Capability Arc expects for an action, or None if the action is unknown."""

    return ACTION_CAPABILITIES.get(action)
MAX_DOCUMENT_BYTES = 1024 * 1024
GRANT_CONTRACT = "lima.governed_execution_grant"
GRANT_VERSION = "v0.1"


class ArcExecutionDenied(RuntimeError):
    """Raised whenever Arc refuses to act. Carries a fixed reason code."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


class ArcGrantExecutor:
    """Validate a Supervisor grant and, if everything holds, perform the read."""

    def __init__(
        self,
        *,
        execution_opt_in: bool = False,
        document_root: Path | str | None = None,
        clock: Any = None,
    ) -> None:
        # Default off. Arc refuses to honour any grant until an operator turns
        # this on for this machine, regardless of what the Supervisor sends.
        self.execution_opt_in = bool(execution_opt_in)
        self.document_root = (
            Path(document_root).resolve() if document_root is not None else None
        )
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def honour(
        self,
        grant: Mapping[str, Any] | None,
        *,
        request_id: str,
        tenant_id: str,
        worker_id: str,
        action_type: str,
        capability: str,
        resource_id: str,
    ) -> dict[str, Any]:
        """Perform the granted capability, or raise ArcExecutionDenied."""

        if not self.execution_opt_in:
            raise ArcExecutionDenied("arc_execution_opt_in_disabled")
        if grant is None:
            raise ArcExecutionDenied("execution_grant_absent")
        if not isinstance(grant, Mapping):
            raise ArcExecutionDenied("execution_grant_malformed")

        self._validate_grant_shape(grant)
        self._validate_grant_binding(
            grant,
            request_id=request_id,
            tenant_id=tenant_id,
            worker_id=worker_id,
            action_type=action_type,
            capability=capability,
        )
        self._validate_grant_window(grant)

        if grant["granted_capability"] not in HONOURED_CAPABILITIES:
            raise ArcExecutionDenied("capability_not_honoured")

        return self._read_document(resource_id, grant)

    # ------------------------------------------------------------------

    @staticmethod
    def _validate_grant_shape(grant: Mapping[str, Any]) -> None:
        if grant.get("grant_contract") != GRANT_CONTRACT:
            raise ArcExecutionDenied("execution_grant_contract_mismatch")
        if grant.get("grant_version") != GRANT_VERSION:
            raise ArcExecutionDenied("execution_grant_version_mismatch")
        if grant.get("execution_allowed") is not True:
            raise ArcExecutionDenied("execution_grant_does_not_allow_execution")
        # A grant that claims it needs no operator opt-in is refused outright.
        # v0.1 grants cannot waive the gate, so anything that says otherwise is
        # not a grant this Arc will act on.
        if grant.get("requires_operator_opt_in") is not True:
            raise ArcExecutionDenied("execution_grant_waives_operator_opt_in")
        if grant.get("side_effects_allowed") is not False:
            raise ArcExecutionDenied("execution_grant_permits_side_effects")
        for field in ("grant_id", "nonce", "request_id", "decision_id"):
            value = grant.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ArcExecutionDenied("execution_grant_malformed")

    @staticmethod
    def _validate_grant_binding(
        grant: Mapping[str, Any],
        *,
        request_id: str,
        tenant_id: str,
        worker_id: str,
        action_type: str,
        capability: str,
    ) -> None:
        expected = {
            "request_id": request_id,
            "bound_tenant_id": tenant_id,
            "bound_worker_id": worker_id,
            "bound_action_type": action_type,
            "granted_capability": capability,
        }
        actual = {key: grant.get(key) for key in expected}
        if actual != expected:
            raise ArcExecutionDenied("execution_grant_binding_mismatch")

    def _validate_grant_window(self, grant: Mapping[str, Any]) -> None:
        expires_at = grant.get("expires_at")
        if not isinstance(expires_at, str) or not expires_at:
            raise ArcExecutionDenied("execution_grant_malformed")
        try:
            expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ArcExecutionDenied("execution_grant_malformed") from exc
        if expires.tzinfo is None:
            raise ArcExecutionDenied("execution_grant_malformed")
        now = self.clock().astimezone(timezone.utc)
        if expires.astimezone(timezone.utc) <= now:
            raise ArcExecutionDenied("execution_grant_expired")

    def _read_document(
        self,
        resource_id: str,
        grant: Mapping[str, Any],
    ) -> dict[str, Any]:
        if self.document_root is None:
            raise ArcExecutionDenied("document_root_not_configured")
        if not isinstance(resource_id, str) or not resource_id.strip():
            raise ArcExecutionDenied("document_resource_invalid")

        candidate = (self.document_root / resource_id.strip()).resolve()
        # Containment is checked after resolution so symlinks and ".." cannot
        # escape the configured root.
        if candidate != self.document_root and self.document_root not in candidate.parents:
            raise ArcExecutionDenied("document_outside_root")
        if not candidate.is_file():
            raise ArcExecutionDenied("document_not_found")
        size = candidate.stat().st_size
        if size > MAX_DOCUMENT_BYTES:
            raise ArcExecutionDenied("document_too_large")

        content = candidate.read_text(encoding="utf-8", errors="replace")
        return {
            "capability": "document_read",
            "grant_id": grant["grant_id"],
            "request_id": grant["request_id"],
            "resource_id": resource_id,
            "byte_count": size,
            "content": content,
            "executed": True,
            "side_effects_performed": False,
        }
