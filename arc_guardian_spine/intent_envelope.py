"""Arc intent envelope contract for future Guardian/LIMA Office handoff.

The envelope is a metadata contract only. It does not sign, verify, dispatch,
persist, call models, call connectors, or grant runtime authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from .base import (
    ARC_POLICY_REFS,
    ARC_RUNBOOK_REFS,
    ArcActionRequest,
    evaluate_arc_action,
)


SignatureStatus = Literal["missing", "reference_attached", "verified_later_by_guardian"]


class ArcIntentEnvelopeError(ValueError):
    """Raised when an Arc intent envelope is malformed or unsafe."""


@dataclass(frozen=True)
class ArcIntentEnvelope:
    """Signed-request boundary shape for future LIMA Office acceptance.

    `signature_ref` is a reference only. Arc Bot Shell does not create or verify
    cryptographic signatures in this phase.
    """

    envelope_id: str
    action_request: ArcActionRequest
    signature_ref: str
    signature_status: SignatureStatus = "reference_attached"
    envelope_version: str = "arc.intent.envelope.v1"
    policy_refs: tuple[str, ...] = ARC_POLICY_REFS
    runbook_refs: tuple[str, ...] = ARC_RUNBOOK_REFS
    redaction_policy_ref: str = "policy://arc-bot/redaction/default"
    output_policy_ref: str = "policy://arc-bot/output/preview-only"
    replay_protection_ref: str = "replay://arc-bot/guardian-owned-later"
    runtime_authority_blocked: bool = True
    runtime_execution_blocked: bool = True
    signature_verified_by_arc_shell: bool = False
    requires_guardian_verification: bool = True


def build_arc_intent_envelope(
    action_request: ArcActionRequest,
    *,
    envelope_id: str | None = None,
    signature_ref: str = "signature://guardian-lima-office/pending",
    signature_status: SignatureStatus = "reference_attached",
) -> ArcIntentEnvelope:
    """Build and validate a future signed-request envelope contract."""

    envelope = ArcIntentEnvelope(
        envelope_id=envelope_id or f"arc-intent-envelope:{action_request.action_id}",
        action_request=action_request,
        signature_ref=signature_ref,
        signature_status=signature_status,
    )
    validate_arc_intent_envelope(envelope)
    return envelope


def validate_arc_intent_envelope(envelope: ArcIntentEnvelope) -> None:
    """Validate required metadata without granting execution authority."""

    request = envelope.action_request
    required_fields = {
        "envelope_id": envelope.envelope_id,
        "action_id": request.action_id,
        "tenant_id": request.tenant_id,
        "worker_id": request.worker_id,
        "operator_id": request.operator_id,
        "task_ref": request.task_ref,
        "signature_ref": envelope.signature_ref,
        "redaction_policy_ref": envelope.redaction_policy_ref,
        "output_policy_ref": envelope.output_policy_ref,
        "replay_protection_ref": envelope.replay_protection_ref,
    }
    missing = [name for name, value in required_fields.items() if not str(value).strip()]
    if missing:
        raise ArcIntentEnvelopeError(
            f"Arc intent envelope missing required fields: {', '.join(sorted(missing))}"
        )

    if envelope.signature_status == "missing":
        raise ArcIntentEnvelopeError("Arc intent envelope requires a signature reference")
    if not envelope.policy_refs:
        raise ArcIntentEnvelopeError("Arc intent envelope requires policy refs")
    if not envelope.runbook_refs:
        raise ArcIntentEnvelopeError("Arc intent envelope requires runbook refs")
    if not request.evidence_refs:
        raise ArcIntentEnvelopeError("Arc intent envelope requires action evidence refs")
    if envelope.runtime_authority_blocked is not True:
        raise ArcIntentEnvelopeError("Arc intent envelope cannot grant runtime authority")
    if envelope.runtime_execution_blocked is not True:
        raise ArcIntentEnvelopeError("Arc intent envelope cannot grant runtime execution")
    if envelope.signature_verified_by_arc_shell is not False:
        raise ArcIntentEnvelopeError("Arc shell cannot claim signature verification")
    if envelope.requires_guardian_verification is not True:
        raise ArcIntentEnvelopeError("Arc intent envelope must require Guardian verification")


def build_arc_intent_envelope_projection(
    action_request: ArcActionRequest | None = None,
) -> dict[str, Any]:
    """Build a deterministic read-only envelope projection."""

    request = action_request or ArcActionRequest(
        action_id="arc-action-local-doc-preview-001",
        action_kind="document_intake_preview",
    )
    envelope = build_arc_intent_envelope(request)
    guardian_decision = evaluate_arc_action(request)

    return {
        "artifact_type": "arc_intent_envelope_projection",
        "artifact_id": envelope.envelope_id,
        "phase": "phase-2-contract",
        "projection_scope": "planning_read_only",
        "source_access_mode": "read_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "envelope": asdict(envelope),
        "guardian_decision_preview": asdict(guardian_decision),
        "handoff_requirements": {
            "future_authority_owner": "LIMA Office / Guardian",
            "signature_verification_required": True,
            "approval_token_lineage_required": guardian_decision.approval_required,
            "execution_allowed": False,
        },
    }
