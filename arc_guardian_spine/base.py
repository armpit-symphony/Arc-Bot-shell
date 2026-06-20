"""Minimal Arc Guardian/Spine shell base.

This module is a contract/stub layer only. It does not call a model, connector,
filesystem adapter, network adapter, LIMA Office service, or Guardian Suite
runtime. It gives Arc Bot a stable shape for the first local-PC worker shell.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


ARC_ALLOWED_TOOL_PACKS = ("office_docs", "local_model_preview", "spine_readiness")
ARC_BLOCKED_ACTIONS = (
    "connector_live_read",
    "connector_live_write",
    "customer_system_mutation",
    "external_message_send",
    "file_write",
    "local_model_execution",
    "network_egress",
    "production_deployment",
    "tool_execution",
)
ARC_POLICY_REFS = (
    "policy://arc-bot/local-model-only",
    "policy://arc-bot/guardian-required",
    "policy://arc-bot/no-connectors-no-customer-mutation",
)
ARC_RUNBOOK_REFS = (
    "runbook://arc-bot/local-model-seat-readiness",
    "runbook://arc-bot/document-intake-preview",
)
ARC_EVIDENCE_TYPES = (
    "local_model_seat_readiness",
    "document_intake_contract",
    "guardian_decision",
    "approval_request",
    "spine_event",
)

ActionKind = Literal[
    "document_intake_preview",
    "document_extract_preview",
    "document_draft_generation",
    "document_export_request",
    "connector_request",
    "local_model_call",
    "connector_action",
    "customer_record_mutation",
    "external_send",
    "runtime_tool_execution",
    "admin_remediation",
]

Decision = Literal["allow_preview", "approval_required", "deny"]
ApprovalStatus = Literal["not_required", "pending", "approved", "denied", "expired", "revoked"]


@dataclass(frozen=True)
class ArcLocalModelSeat:
    """Readiness metadata for one local model installed on an Arc worker PC."""

    provider_kind: str = "local_model"
    runtime: str = "ollama"
    model_id: str = "qwen2.5:7b"
    endpoint_label: str = "http://127.0.0.1:11434"
    installed_on: str = "arc_worker_pc"
    lima_office_attached: bool = True
    cloud_fallback_allowed: bool = False
    network_egress_allowed: bool = False
    credential_required: bool = False


@dataclass(frozen=True)
class ArcActionRequest:
    """Guardian input envelope for an Arc office-worker action."""

    action_id: str
    action_kind: ActionKind
    tenant_id: str = "single_tenant_local"
    worker_id: str = "arc-worker-001"
    operator_id: str = "operator-local"
    task_ref: str = "task://arc/local/document-intake-preview"
    data_sensitivity: str = "office_internal"
    requested_tool_pack: str = "office_docs"
    evidence_refs: tuple[str, ...] = (
        "evidence://arc-bot/local-model-seat-readiness",
        "evidence://arc-bot/document-intake-preview-contract",
    )
    payload_summary: str = "metadata-only office document preview request"


@dataclass(frozen=True)
class ArcEvidenceRef:
    """Evidence reference metadata without storing raw office content."""

    ref_id: str
    evidence_type: str
    required: bool = True
    sensitivity: str = "office_internal"
    raw_content_persisted: bool = False
    redacted_summary_only: bool = True


@dataclass(frozen=True)
class ArcGuardianDecision:
    """Fail-closed decision projection for Arc's stripped Guardian shell."""

    decision_id: str
    action_id: str
    decision: Decision
    reason_code: str
    runtime_authority_blocked: bool = True
    runtime_execution_blocked: bool = True
    local_model_execution_blocked: bool = True
    approval_required: bool = True
    policy_refs: tuple[str, ...] = ARC_POLICY_REFS
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    runbook_refs: tuple[str, ...] = ARC_RUNBOOK_REFS
    blocked_actions: tuple[str, ...] = ARC_BLOCKED_ACTIONS


@dataclass(frozen=True)
class ArcApprovalRequest:
    """Approval request contract for actions that may later become consequential."""

    approval_id: str
    action_id: str
    guardian_decision_ref: str
    status: ApprovalStatus = "pending"
    operator_id: str = "operator-local"
    reusable: bool = False
    grants_runtime_execution: bool = False
    grants_local_model_execution: bool = False
    policy_refs: tuple[str, ...] = ARC_POLICY_REFS
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    runbook_refs: tuple[str, ...] = ARC_RUNBOOK_REFS


@dataclass(frozen=True)
class ArcSpineEvent:
    """Read-only event projection for future LIMA Office spine ingestion."""

    event_id: str
    event_type: str
    action_id: str
    task_ref: str
    worker_id: str
    tenant_id: str
    source_shell: str = "arc_bot_shell"
    source_access_mode: str = "read_only"
    persistence_mode: str = "projection_only"
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    guardian_decision_ref: str = ""
    guardian_decision_result: Decision = "deny"
    reason_code: str = ""


@dataclass(frozen=True)
class ArcSpineLedger:
    """Projection-only local Spine ledger helper.

    The ledger keeps events in memory and never writes to disk. It is a contract
    shape for the future LIMA Office handoff, not a persistence implementation.
    """

    events: tuple[ArcSpineEvent, ...] = ()

    def append_planned_event(self, event: ArcSpineEvent) -> "ArcSpineLedger":
        return ArcSpineLedger(events=(*self.events, event))

    def list_recent_events(self, limit: int = 10) -> tuple[ArcSpineEvent, ...]:
        if limit <= 0:
            return ()
        return self.events[-limit:]

    def list_blocked_actions(self) -> tuple[ArcSpineEvent, ...]:
        return tuple(event for event in self.events if event.guardian_decision_result == "deny")

    def list_approval_required_actions(self) -> tuple[ArcSpineEvent, ...]:
        return tuple(
            event
            for event in self.events
            if event.guardian_decision_result == "approval_required"
        )


def evaluate_arc_action(request: ArcActionRequest) -> ArcGuardianDecision:
    """Return the fail-closed Guardian decision for an Arc action request."""

    if request.requested_tool_pack not in ARC_ALLOWED_TOOL_PACKS:
        return _decision(
            request,
            decision="deny",
            reason_code="tool_pack_not_allowed_for_arc_bot",
        )

    if request.action_kind == "document_intake_preview":
        return _decision(
            request,
            decision="allow_preview",
            reason_code="metadata_preview_only_no_model_call",
            approval_required=False,
        )

    if request.action_kind == "document_extract_preview":
        if request.requested_tool_pack == "local_model_preview":
            return _decision(
                request,
                decision="approval_required",
                reason_code="local_model_preview_requires_guardian_approval",
            )
        return _decision(
            request,
            decision="allow_preview",
            reason_code="deterministic_extraction_preview_no_model_call",
            approval_required=False,
        )

    if request.action_kind in {
        "document_draft_generation",
        "document_export_request",
    }:
        return _decision(
            request,
            decision="approval_required",
            reason_code="local_model_preview_requires_guardian_approval",
        )

    return _decision(
        request,
        decision="deny",
        reason_code=f"{request.action_kind}_blocked_until_guardian_runtime_gate",
    )


def build_arc_guardian_spine_base(
    request: ArcActionRequest | None = None,
    local_model_seat: ArcLocalModelSeat | None = None,
) -> dict[str, Any]:
    """Build the minimal Arc Guardian/Spine base projection."""

    action_request = request or ArcActionRequest(
        action_id="arc-action-local-doc-preview-001",
        action_kind="document_intake_preview",
    )
    model_seat = local_model_seat or ArcLocalModelSeat()
    decision = evaluate_arc_action(action_request)
    evidence_refs = build_arc_evidence_refs(action_request, decision)
    approval_request = build_arc_approval_request(action_request, decision)
    spine_event = ArcSpineEvent(
        event_id=f"spine-event:{action_request.action_id}",
        event_type="guardian_decision_projected",
        action_id=action_request.action_id,
        task_ref=action_request.task_ref,
        worker_id=action_request.worker_id,
        tenant_id=action_request.tenant_id,
        evidence_refs=action_request.evidence_refs,
        guardian_decision_ref=decision.decision_id,
        guardian_decision_result=decision.decision,
        reason_code=decision.reason_code,
    )
    ledger = ArcSpineLedger().append_planned_event(spine_event)

    return {
        "artifact_id": "arc_guardian_spine_base_v1",
        "artifact_type": "arc_guardian_spine_base_projection",
        "phase": "phase-1",
        "projection_scope": "planning_read_only",
        "source_access_mode": "read_only",
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "local_model_only": True,
        "cloud_fallback_allowed": False,
        "connector_actions_allowed": False,
        "customer_system_mutation_allowed": False,
        "allowed_tool_packs": list(ARC_ALLOWED_TOOL_PACKS),
        "local_model_seat": asdict(model_seat),
        "action_request": asdict(action_request),
        "guardian_decision": asdict(decision),
        "evidence_refs": [asdict(evidence_ref) for evidence_ref in evidence_refs],
        "approval_request": asdict(approval_request) if approval_request else None,
        "spine_event": asdict(spine_event),
        "spine_ledger": {
            "persistence_mode": "projection_only",
            "recent_events": [asdict(event) for event in ledger.list_recent_events()],
            "blocked_actions": [asdict(event) for event in ledger.list_blocked_actions()],
            "approval_required_actions": [
                asdict(event) for event in ledger.list_approval_required_actions()
            ],
        },
        "reference_repos": {
            "sparkbot": "C:/Users/limap/Sparkbot",
            "guardian_suite": "C:/Users/limap/LIMA-Guardian-Suite",
        },
    }


def _decision(
    request: ArcActionRequest,
    *,
    decision: Decision,
    reason_code: str,
    approval_required: bool = True,
) -> ArcGuardianDecision:
    return ArcGuardianDecision(
        decision_id=f"guardian-decision:{request.action_id}",
        action_id=request.action_id,
        decision=decision,
        reason_code=reason_code,
        approval_required=approval_required,
        evidence_refs=request.evidence_refs,
    )


def build_arc_evidence_refs(
    request: ArcActionRequest,
    decision: ArcGuardianDecision,
) -> tuple[ArcEvidenceRef, ...]:
    """Build structured evidence references for an Arc decision projection."""

    evidence = [
        ArcEvidenceRef(
            ref_id=ref,
            evidence_type=(
                "local_model_seat_readiness"
                if "local-model-seat" in ref
                else "document_intake_contract"
            ),
        )
        for ref in request.evidence_refs
    ]
    evidence.append(
        ArcEvidenceRef(
            ref_id=f"evidence://arc-bot/guardian-decision/{decision.action_id}",
            evidence_type="guardian_decision",
        )
    )
    return tuple(evidence)


def build_arc_approval_request(
    request: ArcActionRequest,
    decision: ArcGuardianDecision,
) -> ArcApprovalRequest | None:
    """Build a non-reusable approval request when policy requires one."""

    if not decision.approval_required:
        return None

    return ArcApprovalRequest(
        approval_id=f"approval-request:{request.action_id}",
        action_id=request.action_id,
        guardian_decision_ref=decision.decision_id,
        operator_id=request.operator_id,
        evidence_refs=decision.evidence_refs,
    )
