# Arc Guardian/Spine Base

Date: 2026-06-20
Status: Phase-1 planning/read-only base

This document defines the first stripped-down Guardian Suite and Spine shell
needed by Arc Bot. It is intentionally smaller than Sparkbot Guardian/Spine and
does not copy Sparkbot runtime modules.

## Source Repos

- Sparkbot is the working source of truth for Guardian/Spine behavior.
- LIMA-Guardian-Suite is a reference extraction, but it is not treated as a
  standalone runtime dependency for Arc Bot yet.
- Arc Bot owns only the shell boundary needed for a local model PC connected to
  LIMA Office.

## Minimal Arc Stack

Arc Bot starts with these pieces only:

- `ArcActionRequest`: metadata-only office action request.
- `ArcGuardianDecision`: fail-closed decision record.
- `ArcApprovalRequest`: non-reusable approval request metadata.
- `ArcEvidenceRef`: redacted evidence reference metadata.
- `ArcSpineEvent`: read-only event projection for future LIMA Office ingestion.
- `ArcSpineLedger`: projection-only local Spine helper with no disk writes.
- `ArcLocalModelSeat`: local model readiness metadata for one worker PC.

The implementation lives in `arc_guardian_spine/` and is import-only safe.

## Local Model Boundary

The first target is a local model installed on an Arc worker PC. The base
records local model readiness only:

- local model only,
- localhost endpoint label only,
- no cloud fallback,
- no provider credentials,
- no network egress,
- no model invocation in this phase.

Future local model calls must pass through Guardian before execution.

## Blocked By Default

The following remain blocked:

- connector live reads and writes,
- customer-system mutation,
- external sends,
- file writes,
- local model execution,
- network egress,
- production deployment,
- unrestricted tool execution.

## Preview Command

```powershell
python -m arc_guardian_spine.preview
python -m arc_guardian_spine.preview --action-kind document_extract_preview
```

The preview emits JSON only and performs no runtime action.

## Phase-1 Contract Shape

The Phase-1 base supports the minimum Arc Guardian/Spine runtime shape without
runtime execution:

- deterministic action classification,
- structured policy/evidence/runbook refs,
- non-reusable approval request projection,
- projection-only Spine events,
- in-memory/projection-only local Spine ledger helpers for recent, blocked, and
  approval-required actions.

The local Spine ledger is not persistence. It is a contract surface for a later
LIMA Office handoff.

## Next Gate

Before any real local model call is enabled, Arc Bot needs:

- signed `ArcActionRequest` / `IntentEnvelope` shape,
- Guardian approval token lineage,
- local model seat health proof,
- raw document redaction policy,
- evidence and rollback refs,
- LIMA Office handoff contract for the resulting preview artifact.
