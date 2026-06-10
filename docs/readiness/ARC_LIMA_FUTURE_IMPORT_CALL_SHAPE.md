# Arc Bot Future LIMA Import Call Shape

## Purpose

This document defines a **future** proof-only interaction shape for readiness planning.

It is explicit that this is:

- non-production,
- pseudo-code,
- not imported,
- not executable,
- not wired to Arc runtime,
- dry-run oriented,
- no live actions.

## Future import/call shape (static design only)

```text
# NON-PRODUCTION PSEUDO-CODE ONLY
# - not executed
# - not imported by live Arc runtime
# - not a bridge
# - future design sketch for readiness proofs only

from future_contracts import (
    ShellManifest,          # Arc-defined shell manifest for future mapping
    HumanInput,             # future operator intent envelope input
    IntentEnvelope,         # normalized intention model
    ApprovalMetadata,       # approval binding contract
    GuardianDecision,       # future runtime decision output
    SpineEvent,             # future audit/evidence lineage event
    StorageProtocol         # future persistence boundary contract
)

def arc_build_readiness_intent(input_text: str, tenant_id: str, operator_id: str):
    # Future placeholder only. This function is not called in production today.
    return HumanInput(
        tenant_id=tenant_id,
        operator_id=operator_id,
        channel="arc_readiness_static_review",
        raw_text=input_text,
        intent="office_task_draft",
        safety_intent="dry_run_only"
    )

def arc_prepare_intent_envelope(intent: HumanInput):
    # Future placeholder only.
    # Do not use in live runtime; no execution authority is created here.
    return IntentEnvelope(
        source="arc_shell_readiness",
        tenant_id=intent.tenant_id,
        actor_id=intent.operator_id,
        requested_actions=[
            "classify_request",
            "prepare_reply_draft",
            "prepare_owner_briefing"
        ],
        dry_run=True,
        preview_only=True,
        requires_arc_guardian=True,
        requires_arc_approval=True,
        evidence_refs=["evidence://arc-readiness/static/preview"],
        audit_refs=["audit://arc-readiness/static/preview"]
    )

def arc_build_boundaries(envelope: IntentEnvelope):
    # Future placeholder only.
    # Arc retains authority in this branch; no external calls are sent.
    return {
        "arc_owned_guardian": True,
        "arc_owned_execution_authority": False,
        "lima_import_ready": True,
        "lima_runtime_integration_approved": False,
        "connector_write": "blocked",
        "external_send": "blocked",
        "file_mutation": "blocked",
        "browser_action": "blocked",
        "network_action": "blocked",
        "device_action": "blocked",
        "automation_action": "blocked",
        "worker_dispatch": "blocked"
    }

def arc_preview_record(intent: IntentEnvelope, decision: GuardianDecision):
    # Future placeholder only.
    # This should only create read-only proof telemetry, never execution.
    return SpineEvent(
        event_type="arc_lima_readiness_preview",
        tenant_id=intent.tenant_id,
        actor_id=intent.actor_id,
        dry_run=True,
        preview_only=True,
        decision_id=getattr(decision, "decision_id", "preview"),
        approval_required=getattr(ApprovalMetadata, "required", True),
        evidence_refs=intent.evidence_refs,
        audit_refs=intent.audit_refs,
    )

def arc_readiness_storage(event: SpineEvent):
    # Future placeholder only.
    # StorageProtocol is a future seam contract for server-side persistence.
    # Not implemented in this branch.
    return StorageProtocol.write_if_approved(
        key=f"readiness/{event.event_type}",
        value=event.payload,
        approved=True,
        dry_run=True,
        preview_only=True
    )
```

## Non-production constraints

- No live imports.
- No execution paths.
- No runtime routes.
- No provider/model calls.
- No connector access.
- No file/network/browser/device or scheduler actions.
- No LIMA-authority claims for live office workflows.

## Arc ownership in this branch

- Arc owns approval and execution policy.
- Arc owns proof of authority and audit framing.
- LIMA remains readiness-ready design target, not runtime dependency.
