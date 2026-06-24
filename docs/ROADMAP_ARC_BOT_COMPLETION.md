# Arc Bot Completion Roadmap

Date: 2026-06-20
Status: phased build plan

Goal: deliver an Arc Bot shell that runs on a local PC with a local AI model,
connects into LIMA Office, and performs guarded office document intake/output
work for small-business workflows such as insurance-office intake, review, and
drafting.

## Phase 0 - Scope Lock And Base Contracts

- Keep target deployment to one Supervisor Server and 1-8 Arc worker PCs.
- Keep Arc Bot single-tenant for MVP.
- Keep local model only; no cloud fallback by default.
- Keep all actions Guardian-gated.
- Preserve LIMA AI OS proof packets as evidence, not product runtime.
- Lock no-execution boundaries for:
  - connector reads/writes,
  - customer-system mutation,
  - external sends,
  - file writes,
  - local model calls,
  - network egress.
- Maintain existing proof packets, fixture contracts, and scope-lock tests.
- Completion gate:
  - all current tests pass,
  - `git diff --check` passes,
  - Arc Guardian/Spine base emits read-only projection.

## Phase 1 - Arc Guardian/Spine Minimum Runtime Shape

- Expand `arc_guardian_spine` from projection-only base into typed contracts for:
  - `ArcActionRequest`,
  - `ArcGuardianDecision`,
  - `ArcSpineEvent`,
  - `ArcApprovalRequest`,
  - `ArcEvidenceRef`,
  - `ArcLocalModelSeat`.
- Add a deterministic policy classifier for Arc action categories:
  - document intake preview,
  - document extraction preview,
  - document draft generation,
  - document export request,
  - connector request,
  - customer record mutation,
  - external send,
  - admin/remediation.
- Add a read-only local Spine ledger interface:
  - append planned event,
  - list recent events,
  - list blocked actions,
  - list approval-required actions.
- Do not use Sparkbot runtime modules directly.
- Use Sparkbot as the behavior reference and LIMA-Guardian-Suite as extraction context.
- Completion gate:
  - import-only tests pass,
  - every non-preview action returns blocked or approval-required,
  - every decision has policy, evidence, and runbook refs,
  - approval requests are non-reusable and grant no runtime execution,
  - local Spine ledger helpers are projection-only,
  - basic operator UI can display Local Model, LIMA Office, upload, training,
    self-learning review, and chat controls without live execution.

## Phase 2 - Local Model Seat Readiness

- Define the local model install contract:
  - runtime choice: Ollama for this phase,
  - model family: Qwen,
  - default planning model tag: `qwen2.5:7b`,
  - localhost endpoint label: `http://127.0.0.1:11434`,
  - hardware profile,
  - memory/CPU/GPU posture,
  - LIMA Office attachment status.
- Add health-check projection:
  - model installed,
  - model reachable,
  - model not invoked,
  - network egress disabled,
  - no provider credentials required.
- Add operator-visible readiness output for Runtime Settings.
- Keep model calls blocked until Guardian approval path exists.
- Completion gate:
  - local model readiness can be displayed without invoking the model,
  - no secrets or provider tokens are introduced,
  - tests prove no network/provider calls occur,
  - LIMA Office handoff request identifies the fields Arc Bot needs from the
    control plane,
  - LIMA Office handoff packet can be consumed as read-only metadata and fails
    closed for missing/mismatched fields or blocked statuses.

## Phase 3 - Document Intake Contract

- Define `DocumentIntakeRequest` for local files and manual upload metadata:
  - document ID,
  - source path or upload ref,
  - document type,
  - tenant ID,
  - sensitivity class,
  - intake operator,
  - allowed processing mode.
- Define supported MVP document types:
  - PDF,
  - text,
  - image scan placeholder,
  - Word document placeholder.
- Define raw content handling:
  - no raw customer data in proof packets,
  - redacted summary refs only,
  - local-only temporary processing,
  - evidence refs for intake and redaction.
- Add preview-only parser stubs:
  - validate metadata,
  - classify document type,
  - return blocked/ready-for-review status.
- Completion gate:
  - document intake metadata validates,
  - raw content is not persisted in repo/project state,
  - no OCR/model/parser side effects beyond metadata preview,
  - basic console can surface the document intake metadata preview contract.

## Phase 4 - Local Document Extraction Preview

Status: completed as a deterministic, projection-only contract. Runtime model
execution remains blocked for later approved phases.

- Add first guarded local extraction path behind Guardian:
  - classify action,
  - require approval if local model invocation is needed,
  - create evidence refs,
  - emit Spine event,
  - return preview artifact.
- Start with deterministic non-model extraction where possible:
  - filename metadata,
  - file type,
  - page count placeholder,
  - checksum placeholder,
  - operator-supplied document category.
- Add local model call interface as an injectable provider, not hardwired runtime.
- Block actual model invocation unless:
  - local model seat is healthy,
  - approval token is present,
  - redaction policy is attached,
  - output handling policy is attached.
- Completion gate:
  - extraction preview works without live connectors,
  - local model call remains impossible without explicit gate data,
  - tests cover missing approval, missing evidence, and blocked runtime.

## Phase 5 - Office Workflow Templates

Status: completed as schema-backed, fixture-backed, draft/preview-only workflow
templates. Runtime mutation and external action authority remain blocked.

- Add MVP office workflows:
  - intake note summary,
  - insurance claim packet triage,
  - policy document summary,
  - missing information checklist,
  - customer-service draft reply,
  - internal follow-up task draft.
- Keep all outputs as drafts/previews.
- Require approval for:
  - saving final output,
  - sending external messages,
  - updating customer records,
  - submitting forms,
  - connector writes.
- Add role profiles:
  - Document Processing Bot,
  - Customer Support Draft Bot,
  - Billing Intake Assistant,
  - Compliance Review Assistant.
- Completion gate:
  - each workflow has schema, fixture, proof test, and blocked-action matrix,
  - no workflow can mutate external/customer systems.

## Phase 6 - LIMA Office Integration Boundary

- Define Arc-to-LIMA Office handoff contract:
  - task ID,
  - worker ID,
  - tenant ID,
  - Guardian decision ref,
  - Spine event ref,
  - local model seat ref,
  - evidence refs,
  - output artifact refs.
- Add read-only consumer adapter for LIMA Office:
  - export preview state,
  - export blocked queue,
  - export approval-required queue,
  - export model readiness metadata.
- Keep LIMA Office as the control plane.
- Keep Arc Bot as the local worker shell.
- Completion gate:
  - Arc can emit LIMA Office-readable state,
  - no live customer connector is required,
  - integration tests use fixtures only.

## Phase 7 - Approval And Evidence Path

- Add approval request lifecycle:
  - requested,
  - pending,
  - approved,
  - denied,
  - expired,
  - revoked.
- Bind approval to:
  - operator ID,
  - action ID,
  - policy refs,
  - evidence refs,
  - redaction policy,
  - output policy.
- Add immutable evidence packet shape for:
  - document intake,
  - local model prompt summary,
  - model output summary,
  - blocked action reason,
  - operator decision.
- Completion gate:
  - approval cannot be reused across actions,
  - approval cannot bypass policy,
  - every consequential action has an evidence chain.
  - remaining implementation-gate questions are tracked in
    `docs/requests/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_REQUEST.md`.

## Phase 8 - Controlled Local Model Execution

- Enable the first real local model call only for approved preview work.
- Keep model runtime local to the Arc worker PC.
- Disable:
  - cloud fallback,
  - provider credentials,
  - network egress,
  - connector action,
  - external send,
  - customer-system mutation.
- Add local model execution record:
  - model ID,
  - local endpoint label,
  - prompt summary ref,
  - redacted input ref,
  - redacted output ref,
  - token/latency metadata if available,
  - no raw prompt persistence.
- Completion gate:
  - approved local model preview works,
  - denied/missing approval fails closed,
  - raw content is not written to repo state,
  - test suite proves no cloud/provider path exists.

## Phase 9 - Operator Console MVP

- Build the usable Arc operator console screens:
  - Work Queue,
  - Document Intake,
  - Task Preview,
  - Approval Queue,
  - Evidence Panel,
  - Local Model Readiness,
  - Runtime Settings.
- Keep UI state non-authoritative.
- Server-side state remains the source of truth.
- Add clear operator states:
  - ready,
  - blocked,
  - approval required,
  - preview generated,
  - needs human review.
- Completion gate:
  - operator can intake a document and see a guarded preview,
  - operator can approve or deny preview-only local model processing,
  - no hidden background action exists.

## Phase 10 - Field Deployment Package

Status: Phase-G planning package added. Runtime deployment remains blocked.

- Add local PC setup guide:
  - identify local Arc worker PC,
  - confirm tenant/workspace label,
  - confirm operator/approval owner labels,
  - verify Guardian/Spine health through projections only,
  - run read-only smoke tests.
- Add small-business deployment profile:
  - one supervisor,
  - 1-8 Arc workers,
  - one tenant,
  - local data directory,
  - backup/export policy.
- Add support runbooks:
  - model not reachable,
  - document preview failed,
  - approval queue stuck,
  - evidence packet missing,
  - worker offline.
- Completion gate:
  - package docs and read-only smoke tests pass,
  - rollback posture is documented as docs-only for this phase,
  - software install/update, live supervisor attachment, model invocation,
    connector action, and durable evidence writing remain blocked,
  - no production-readiness claim until field pilot succeeds.

## Phase 11 - Pilot Readiness

Status: Phase-H planning package added. Live pilot execution remains blocked.

- Select one narrow pilot workflow:
  - insurance intake summary and missing-information checklist.
- Use sanitized/local sample documents first.
- Run with human approval for every model-generated output.
- Track:
  - false extraction,
  - missing evidence,
  - approval friction,
  - model latency,
  - operator correction rate.
- Completion gate:
  - sanitized pilot workflow previews render,
  - pilot execution remains blocked until Phase-D/E/F/G gates are approved,
  - operator can inspect every action,
  - all failures produce evidence,
  - no autonomous external/customer mutation occurs.

## Phase 12 - MVP Completion Criteria

Status: completion-readiness gate added. MVP completion remains blocked.

- Arc Bot runs locally on a PC attached to LIMA Office.
- Arc Bot uses only a local model for approved preview work.
- Arc Bot can intake office documents and produce guarded previews/drafts.
- Guardian gates every model call and every consequential action.
- Spine records task, decision, approval, and evidence lineage.
- LIMA Office can read Arc worker status and task/evidence state.
- Operators can approve, deny, or block work.
- No hidden background actions.
- No live connector writes without a later approved phase.
- No production claims until field deployment evidence exists.
- Completion gate:
  - `python -m phase12_mvp_completion.completion --compact` reports
    `mvp_complete = true` only when every criterion has direct runtime evidence,
  - no Phase-D/E/F/G/H blocker remains,
  - full tests, smoke, guardrails, and `git diff --check` pass.
  - current open questions are tracked in
    `docs/requests/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_REQUEST.md`.
