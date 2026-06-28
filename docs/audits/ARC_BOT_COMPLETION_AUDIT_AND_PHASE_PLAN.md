# Arc Bot Completion Audit And Phase Plan

Date: 2026-06-21
Status: current-state audit and completion roadmap
Repository: `armpit-symphony/Arc-Bot-shell`
Branch audited: `v1-g56-consumer-fake-executor-provider-sdk-network-egress-smoke`

## Executive Summary

Arc Bot Shell is a strong Phase-0 through Phase-5 contract-first scaffold. The
repo currently contains a guarded, preview-only worker-bot shell foundation with
documentation, fixtures, pure projection modules, proof packets, a static basic
console, local model readiness metadata, document intake/extraction previews,
and office workflow templates.

It is not yet a runnable business automation product. There is no authoritative
server, no durable state, no live LIMA Office integration, no signed approval
lifecycle, no local model invocation, no connector action path, and no field
pilot evidence. A read-only field deployment package now exists, but it is
setup/runbook/smoke planning only and does not grant runtime or production
deployment authority. That is correct for the current safety posture, but the
next completion work needs to shift from proof packets into a small guarded
runtime without weakening the Guardian boundary.

## Audit Basis

- `git fetch origin` completed cleanly.
- `git status --short --branch` showed a clean working tree before edits.
- File inventory observed:
  - 46 docs files.
  - 29 Python files.
  - 87 test/fixture files.
  - 1 static UI file.
- Validation:
  - `python -m pytest -q`: 281 passed.
  - `git diff --check`: passed.

## What Exists Now

1. Product boundary and governance docs are in place:
   - `README.md`
   - `ARCHITECTURE.md`
   - `MVP_SCOPE.md`
   - `CONTRACTS.md`
   - `SECURITY_MODEL.md`
   - `THREAT_MODEL.md`
   - `AUTONOMY_BOUNDARIES.md`
   - `WORKER_NODE_SPEC.md`
   - `SUPERVISOR_SPEC.md`
   - `DECISIONS.md`
   - `OPEN_QUESTIONS.md`

2. Phase-0 runtime UI scaffold exists as deterministic, read-only projections:
   - adapter payloads,
   - read-feed seam,
   - runtime consumer seam,
   - runtime-control handoff,
   - runtime-control consumer,
   - phase-chain continuity.

3. Arc Guardian/Spine base exists as a projection-only contract layer:
   - action request metadata,
   - Guardian decision metadata,
   - non-reusable approval request metadata,
   - evidence refs,
   - Spine event projection,
   - local model seat readiness metadata.

4. Business shell inventory and client configuration contracts exist:
   - schemas,
   - fixtures,
   - no-execution packets,
   - runtime authority gating packet,
   - readiness bundle.

5. Phase-2 through Phase-5 feature contracts are covered:
   - Ollama/Qwen local model readiness projection,
   - document intake metadata preview,
   - deterministic document extraction preview,
   - schema-backed office workflow templates and role profiles.

6. Static operator UI exists:
   - `ui/arc_bot_basic_console.html`
   - preview/pending states only,
   - no model call,
   - no LIMA Office connector call,
   - no upload processing,
   - no training or memory write.

## Current Safety Posture

The repo remains aligned with the required SparkPit Labs/LIMA posture:

- One Supervisor Server and 1-8 Arc workers remain the target deployment shape.
- Single-tenant MVP assumptions are explicit.
- Guardian remains the required gate for future model, tool, connector, file,
  network, approval, and mutation paths.
- No customer connector, external send, customer-system mutation, provider SDK,
  live local model call, cloud fallback, or production deployment path is active.
- Tests assert no-execution behavior across the current projection modules.

## Gaps And Risks

### Gap 1: README Artifact Drift

Status: resolved in the Phase A repo-hygiene pass on 2026-06-21.

At audit start, the README referenced paths that were not present in this
checkout:

- `docs/ROADMAP_SCOPE_LOCK_PHASE0_PUNCH_LIST.md`
- `docs/ROADMAP_PHASE1_HANDOFF_PUNCH_LIST.md`
- `docs/LIMA_OFFICE_LIMA_AI_OS_CONTRACT_ASSUMPTIONS.md`
- `phase0_runtime_ui_scaffold/runtime_control_renderer.py`
- `phase0_runtime_ui_scaffold/runtime_control_execution.py`
- `scripts/scope_lock_guardrails.ps1`
- `scripts/refresh_scope_lock_artifacts.ps1`
- `scripts/phase0_phase1_handoff_guardrails.ps1`
- `scripts/phase1_handoff_guardrails.ps1`
- `scripts/phase2_handoff_guardrails.ps1`
- `scripts/emit_arc_bot_artifacts.py`
- `scripts/emit_arc_bot_artifacts.ps1`
- `.github/workflows/guardrails.yml`

Resolution:

- Added compatibility handoff docs for the advertised roadmap/contract paths.
- Added preview-only renderer and execution-planning projection modules.
- Added guardrail scripts and CI workflow metadata.
- Added proof packets and a runbook for the advertised handoff artifacts.
- Added tests that fail if README local links, advertised Python modules, or
  guardrail artifact paths drift again.

Residual risk: future README changes can still add stale references, but
`tests/test_arc_bot_readme_artifact_drift.py` now catches that drift.

### Gap 2: No Authoritative Runtime Boundary Yet

The current repo has pure functions, fixtures, and projection helpers. It does
not yet have the signed request/envelope boundary needed before any real local
model call or connector-adjacent action.

Impact: this prevents unsafe execution today, but completion depends on turning
the contract surface into a minimal Guardian-owned runtime boundary.

### Gap 3: No Durable State Or LIMA Office Adapter

The shell can emit and consume fixture-backed metadata, but it does not yet
publish a stable Arc-to-LIMA Office worker state envelope from a running worker.

Impact: LIMA Office cannot yet treat Arc Bot as a live local worker.

### Gap 4: Approval And Evidence Are Metadata Only

Approval requests and evidence refs are modeled, but there is no signed,
non-replayable approval lifecycle and no immutable evidence packet writer.

Impact: any move to controlled execution must wait until approval and evidence
lineage become enforceable, not just displayable.

### Gap 5: Operator Console Is Static

The static HTML console is useful for shape and state language, but it is not a
real operator workflow. There is no backend state source, session model, live
refresh, or Guardian-mediated action request flow.

Impact: the product cannot be piloted until the console becomes a bounded app
over server-side state.

### Gap 6: No Field Deployment Package

Status: planning package added on 2026-06-21.

Resolution:

- Added a local worker PC setup guide.
- Added a field deployment package guide.
- Added read-only support runbooks for worker offline, model not reachable,
  approval queue stuck, evidence missing, and document preview failed.
- Added a read-only smoke wrapper and deterministic field-deployment projection.

Residual risk: Arc Bot still cannot be placed on a mini PC for live
small-business trial work until Guardian/LIMA Office approves execution,
approval/evidence lineage, supervisor attachment, local model invocation, and
field pilot boundaries.

## Completion Phase Plan

### Phase A: Audit Cleanup And Repo Hygiene

Goal: make the repo self-consistent before new runtime work.

Status: completed for the README-advertised artifact drift found in this audit.

Deliverables:

- Either add the missing guardrail scripts/CI files referenced by README or
  remove/defer those references.
- Add tests that verify documented command references resolve to real files.
- Keep `python -m pytest -q` and `git diff --check` green.

Exit gate:

- README current-status section has no dead local links or phantom commands.
- `tests/test_arc_bot_readme_artifact_drift.py` passes.

### Phase B: Signed Arc Request Boundary

Goal: introduce the smallest runtime-neutral request envelope that can later be
accepted by Guardian/LIMA Office.

Status: contract scaffold added on 2026-06-21. Cryptographic signing,
signature verification, replay protection, and approval token issuance remain
external Guardian/LIMA Office responsibilities.

Deliverables:

- `ArcIntentEnvelope` or equivalent signed/typed request shape.
- Stable IDs for task, worker, tenant, operator, action, policy, evidence, and
  runbook refs.
- Explicit blocked defaults for every missing or stale authority field.
- Import-only tests and fixture-backed validation.

Exit gate:

- Every consequential request can be represented without becoming executable.
- `ArcIntentEnvelope` projections keep runtime authority and runtime execution
  blocked.

### Phase C: Arc-To-LIMA Office Read Adapter

Goal: let LIMA Office read Arc worker status without granting action authority.

Status: read-only contract scaffold added on 2026-06-21. There is still no live
supervisor pull service or LIMA runtime import path.

Deliverables:

- Read-only export envelope for:
  - worker heartbeat posture,
  - local model readiness,
  - blocked queue,
  - approval-required queue,
  - preview artifacts,
  - evidence refs.
- Fixture-backed consumer tests against the expected LIMA Office shape.
- No live connector, no socket probe, no customer mutation.

Exit gate:

- Arc Bot can emit a LIMA Office-readable state packet from local data only.
- `arc_lima_office_read_adapter_projection` keeps runtime authority and runtime
  execution blocked.

### Phase D: Approval And Evidence Lineage

Goal: make approval/evidence enforceable before any model execution.

Status: owner answers recorded; runtime implementation remains blocked. Implementation of approval token lineage, replay protection, signature verification, durable evidence writing, and execution-adjacent approvals is blocked pending explicit runtime implementation gate approval.

Deliverables:

- Approval lifecycle:
  - requested,
  - pending,
  - approved,
  - denied,
  - expired,
  - revoked.
- Non-reusable approval token ref bound to action ID, operator ID, policy refs,
  evidence refs, redaction policy, and output policy.
- Immutable evidence packet shape for document intake, extraction preview,
  blocked action, approval decision, and operator correction.

Exit gate:

- Approval cannot be replayed, reused across actions, or used without matching
  policy/evidence lineage.
- Guardian/LIMA Office has approved the runtime implementation gate in
  `docs/requests/ARC_BOT_RUNTIME_IMPLEMENTATION_GATE_REQUEST.md`.

### Phase E: Controlled Local Model Preview

Goal: allow the first real local-only model preview under Guardian.

Deliverables:

- Local model executor interface owned by Guardian gate.
- Ollama/Qwen local-only adapter with cloud fallback disabled.
- No provider credentials.
- Network egress policy documented and tested.
- Redacted prompt/input/output refs only; no raw customer content in repo,
  logs, fixtures, or proof packets.

Exit gate:

- An approved local model preview can run; denied, missing, stale, or mismatched
  approval fails closed.

### Phase F: Operator Console MVP

Goal: replace the static console with a usable guarded operator workflow.

Deliverables:

- Work Queue.
- Document Intake.
- Task Preview.
- Approval Queue.
- Evidence Panel.
- Local Model Readiness.
- Runtime Settings.
- Server-side state as source of truth; UI remains non-authoritative.

Exit gate:

- Operator can intake a document metadata record, request a guarded preview,
  approve/deny local model processing, and inspect evidence without hidden
  background action.

### Phase G: Field Deployment Package

Goal: make one-supervisor, 1-8-worker deployment repeatable.

Status: planning/read-only package added on 2026-06-21. Runtime field
deployment remains blocked.

Deliverables:

- Local Arc worker PC setup guide.
- Supervisor attachment guide.
- Local model install/readiness guide.
- Smoke tests.
- Backup/export policy.
- Rollback path.
- Support runbooks for model offline, approval stuck, evidence missing,
  document preview failed, and worker offline.

Exit gate:

- Package docs, support runbooks, and read-only smoke commands exist.
- `arc_field_deployment_readiness_projection` keeps runtime authority,
  runtime execution, and production deployment blocked.
- A future fresh mini PC setup can pass approved smoke tests without production
  claims after Guardian/LIMA Office unblocks execution-adjacent dependencies.

### Phase H: Narrow Pilot

Goal: prove one safe business workflow before expanding.

Status: planning/read-only package added on 2026-06-21. Live pilot execution
remains blocked.

Recommended pilot:

- Insurance intake summary and missing-information checklist.

Rules:

- Use sanitized/local sample documents first.
- Human approval required for every model-generated output.
- No external sends.
- No customer-record updates.
- No connector writes.

Exit gate:

- Sanitized pilot workflow previews render.
- Every pilot output remains draft-preview-only and pending operator review.
- Every consequential action remains blocked or approval-required.
- Live pilot execution waits for Guardian/LIMA Office approval/evidence,
  local-model preview, operator-console, and field deployment gates.

### Phase I: MVP Completion

Goal: declare a guarded MVP, not production readiness.

Status: completion-readiness gate added on 2026-06-21. MVP completion remains
blocked pending runtime and Guardian/LIMA Office dependencies.

Completion criteria:

- Arc Bot runs locally on an Arc worker PC attached to LIMA Office.
- Arc Bot uses only local model execution for approved preview work.
- Guardian gates every model call and every consequential action.
- Spine records task, decision, approval, and evidence lineage.
- LIMA Office can read worker status and task/evidence state.
- Operators can approve, deny, or block work.
- No hidden background actions.
- No live connector writes without a later approved phase.
- No production claims until field deployment evidence exists.

Exit gate:

- `arc_mvp_completion_gate_projection` can truthfully set `mvp_complete = true`
  with direct evidence for every criterion.
- No Phase-D approval/evidence, Phase-E local model, Phase-F operator-console,
  Phase-G field deployment, or Phase-H live pilot blocker remains.
- Full tests, smoke, guardrails, and whitespace checks pass.

## Recommended Immediate Next Step

Send `docs/requests/ARC_BOT_RUNTIME_IMPLEMENTATION_GATE_REQUEST.md` to the
LIMA Office Supervisor, Guardian/verifier, evidence-plane, operator-console,
and model-route owners, with the response template
`docs/examples/arc_lima/runtime_implementation_gate_response.template.json` and
schema `docs/contracts/schemas/arc_runtime_implementation_gate_response.schema.json`.
Do not implement real model invocation, supervisor attachment, worker
registration, approval issuance/verification, verifier ingest, operator-console
state mutation, or durable evidence writing before the runtime implementation
gate is explicitly approved and a separate implementation patch is added and
verified.
