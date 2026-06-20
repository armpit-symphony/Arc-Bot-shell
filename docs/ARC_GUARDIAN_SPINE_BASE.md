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

The first target is a local model installed on an Arc worker PC. Phase 2 pins
the readiness target to Ollama with Qwen local models. The base records local
model readiness only:

- local model only,
- localhost endpoint label only,
- no cloud fallback,
- no provider credentials,
- no network egress,
- no model invocation in this phase.

Default Phase-2 planning values:

- runtime: `ollama`,
- model family: `qwen`,
- model tag: `qwen2.5:7b`,
- endpoint label: `http://127.0.0.1:11434`.

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

## Phase-3 Document Intake Boundary

Document intake is metadata-only in Phase 3. Arc Bot may classify supported
document types from declared type or upload/source reference labels:

- PDF,
- text,
- image scan placeholder,
- Word document placeholder.

The intake preview may return `ready_for_review` or `blocked`. It must not read
file bytes, persist raw document content, run OCR, invoke parsers, call the
local model, mutate files, call connectors, or update customer systems.

## Phase-4 Document Extraction Preview Boundary

Document extraction preview is deterministic metadata-only in Phase 4. Arc Bot
may return filename metadata, classified document type, page-count placeholder,
checksum placeholder, and operator-supplied document category.

Every extraction preview must remain behind Guardian classification, redacted
evidence refs, policy refs, runbook refs, and a projection-only Spine event. If
a request says local model assistance is needed, the projection requires local
model seat health, approval token, redaction policy, and output policy metadata.
Those fields are gate data only. They do not grant runtime execution in Phase 4.

The local model provider is an injectable interface for later approved runtime
work. The default provider is blocked and performs no local model call, provider
SDK use, socket/network action, parser/OCR action, file read/write, connector
action, raw content persistence, or customer-system mutation.

## Preview Command

```powershell
python -m arc_guardian_spine.preview
python -m arc_guardian_spine.preview --action-kind document_extract_preview
python -m arc_guardian_spine.preview --action-kind document_extract_preview --requested-tool-pack local_model_preview
python -m phase4_document_extraction.extraction
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
