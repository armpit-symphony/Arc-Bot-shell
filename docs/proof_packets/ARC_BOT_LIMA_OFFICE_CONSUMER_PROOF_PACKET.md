# Arc Bot / LIMA Office Consumer Proof Packet

## 1) Current Arc-Bot-shell status

### Scope and repo posture
- `Arc-Bot-shell` is currently a **documentation and contract-planning shell** repository.
- There is no production runtime implementation, no operator UI, and no Arc-worker execution backend checked into this repo.
- The branch lineage confirms this: prior static proof packets and operator-console foundations already framed Arc Bot as:
  - LIMA-ready only
  - not LIMA-integrated
  - no live office action execution
  - no provider/connector/device/browser/network side effects
- The repo presently exports the following evidence posture:
  - operator-console surface definitions
  - static normalized task examples
  - capability and approval boundary expectations
  - readiness/static proof docs
  - no runnable Arc-LIMA runtime adapter

### Current status line
- `READY_FOR_ARC_READINESS_DOCS_AND_STATIC_PROOF_ONLY`
- `NOT_READY_FOR_RUNTIME_INTEGRATION`
- `NOT_READY_FOR_LIMA_IMPORTS_IN_PRODUCT_CODE`
- `NOT_READY_FOR_LIVE_OFFICE_ACTIONS_THROUGH_LIMA`
- `NOT_READY_FOR_CONNECTORS_OR_CUSTOMER_DATA_THROUGH_LIMA`
- `NOT_READY_FOR_HUMANINPUT_BRIDGE_BEHAVIOR`
- `NOT_READY_FOR_DEVICE_OR_AUTOMATION_ACTIONS`

## 2) What works today

- Proven documentation artifacts for the Arc shell boundary:
  - `README.md` product intent and fail-closed posture
  - `OPERATOR_CONSOLE_FOUNDATION` operator surface map
  - `ARC_BOT_OPERATOR_CONSOLE_STATE` contract-shaped server-state envelope
  - LIMA Office contract references for console/task/worker/approval/evidence/connector/model route alignment
  - LIMA readiness proof documents and normalized static examples
- Static proof artifacts already model intent for:
  - preview generation
  - approvals-as-metadata
  - evidence/audit reference chaining
  - blocked/fail-closed handling for high-risk actions
- Explicitly documented ownership boundary:
  - Arc owns approval/guardian policy and execution authority posture during this phase
  - LIMA surfaces remain future runtime seams only

## 3) What is mocked, placeholder, incomplete, or missing

### Mocked / placeholder
- Readiness examples and pseudo-code call shapes are static and non-executable.
- Capability and approval boundary examples are **policy-only** and not runtime-enforced.
- `candidate`/`preview` language is planning language only.
- All connector, model-provider, and worker dispatch semantics are placeholders until contracts and threat model are approved.

### Incomplete / missing
- No code-backed parser for `ConsumerRequest` intake.
- No `HumanInput` adapter or compiler wiring.
- No `TypedIntentEnvelope`/`TaskIntent` compiler or normalization in product code.
- No `CandidatePreview` engine or runtime state projection integration.
- No `RuntimeStateSnapshot` ingestion and no LIMA Office supervisor pull.
- No live approval workflow engine; only metadata expectations.
- No evidence persistence, no audit persistence, no Spine publication service.
- No health checker, no diagnostics executor, no connector bridge.
- No model routing, no token/provider/session integration, no device/tool invocation.
- No persistence layer; no queueing, scheduling, or worker dispatch.

## 4) Intended office-worker shell role

- Arc Bot Shell role: **operator-facing office-worker console layer** for a small-business deployment.
- Focused on:
  - task intake, triage, classification, and routing review
  - preview generation for non-authoritative outputs
  - evidence-oriented operator decision support
  - explicit blocked/fail-closed behavior for all high-risk actions
- Not intended to be:
  - direct connector executor
  - free-running assistant with hidden autonomy
  - personal workstation assistant
  - device/terminal/browser automation shell

## 5) Task intake needs

### Minimum intake schema (future shape, static now)
- `tenant_id`: single tenant context
- `customer_context_id`: one business context only
- `operator_id`
- `request_text` + `request_source` + optional `request_channel`
- `requested_capability` list
- `urgency` + `risk_hint`
- `tool_pack_hint` (e.g., helpdesk, scheduling, diagnostics)
- `session_id` / `client_session_nonce` (for replay and correlation)
- `provenance`: source of intake (manual upload, queue handoff, operator input)

### Intake behavior requirements (now)
- Allowed now: collect normalized static request metadata.
- Not allowed now: execute or dispatch based on intake.
- Required immediate result states:
  - `preview_only`
  - `explain_plan`
  - `blocked`
  - `deferred`

## 6) Operator approval UX needs

- Operator UI must support:
  - explicit approval posture per request
  - reason-bound blocking with runbook links
  - explicit expiry/validity and review window visibility
  - one-way preview lane (`preview_only` / `explain_plan`)
  - deferred lane with remediation checklist
  - manual override requiring operator authentication
- Approval artifacts that must be displayed when surfaced:
  - `approval_ref`
  - `guardian_decision_ref`
  - `evidence_ref`
  - `audit_ref`
  - `policy_ref`
  - `risk_tier`
  - `required_action`
  - `session_boundaries`
- Operator cannot promote preview artifacts to execution in this phase.

## 7) Evidence trail needs

Arc must keep an explicit evidence lineage for every reviewed flow:

- Intake evidence: evidence request and intake metadata refs.
- Decision evidence: reasoned classification/routing + operator notes.
- Approval evidence: guardian-bound approval + token metadata.
- Safety evidence: block reason, missing input checks, boundary violations.
- Event evidence: Spine-compatible event references for future cross-system correlation.

Evidence requirements:
- evidence refs and audit refs are mandatory for all non-deferred, non-blocked request states.
- no raw secrets/credentials in evidence payloads.
- redaction policy and tenant separation must be preserved in all reference IDs and artifacts.

## 8) Health check needs

- Supervisor/overall health posture (read-only preview):
  - worker reachability posture
  - queue backlog posture
  - approval backlog posture
  - connector readiness posture
  - model-route availability posture
  - incident/degradation posture
  - evidence/egress posture
- Runtime health checks are:
  - currently **not live**
  - expected to consume read-only snapshots in future via `RuntimeStateSnapshot`
  - blocked when required snapshot components are absent
- Any missing health contract must force blocked/blocked_mvp equivalent `blocked` state.

## 9) Helpdesk / diagnostic flow needs

- Intake to triage flow exists only as paper/plan today.
- Required future flow:
1. Ingest helpdesk/IT request as `ConsumerRequest`.
2. Convert to `HumanInput`.
3. Emit `TaskIntent` / `TypedIntentEnvelope`.
4. Generate `CandidatePreview` in one of:
   - `preview_only`
   - `explain_plan`
   - `deferred`
5. Surface for operator confirmation and explicit Guardian gate before any next step.
6. Runbook-guided diagnostic planning only (no execution).
7. If approved in future runtime, produce `ConsequentialActionRequest` and execute through separate, explicit seam.
- Any execution-oriented diagnostic automation is **blocked** until explicit runtime authority is approved.

## 10) Small-business workflow needs

- Intake lanes to support:
  - customer request classification
  - billing/operations note handling
  - scheduling proposal drafts
  - escalation routing to owner/fleet
  - connector-setup visibility (read-only)
  - owner briefing preparation
- Small-business constraints:
  - one customer context at a time
  - 1 Supervisor Server and 1-8 Arc workers
  - low-autonomy posture by default
  - human confirmation at approval boundaries
- Workflow outputs in this phase are draft, planned, and read-only.

## 11) Office role / user / session / device trust needs

### Office role
- Operator role is primary authority for visibility and approval.
- Worker roles exist as reviewed targets, not execution owners in this repo.

### User trust posture
- Session-scoped role + tenant checks required before any decision surface is trusted.
- No cross-tenant state access.
- No hidden background actions.

### Device trust posture
- Worker/shell identity references must be surfaced as snapshots only.
- No endpoint/software install/update/remediation behavior is implemented or allowed in this phase.
- Future: device trust data must be treated as read-only until separately approved.

## 12) Future tool-pack needs (future only; not implemented)

The following are explicitly future requirements and not implemented:

- Connector adapter tool packs
- Calendar tool pack
- Helpdesk platform tool pack
- Diagnostic workflow tool pack
- File/knowledge retrieval tool pack
- Device operation tool pack
- Messaging tool pack
- Runbook automation tool pack
- Evidence writer tool pack
- LLM model/provider route tooling

All above are **deferred to runtime branches** and must remain blocked until:
- contract approval is complete
- guardian policy is defined
- approval + evidence contracts are live
- session/device trust and tenant boundaries are enforced

## 13) Surfaces that must stay Guardian-gated

Even in future, these must remain guarded and never bypassed by shell preview:
- worker lifecycle transitions (quarantine/release/review)
- connector setup and any connector data writes
- external customer communication sends
- file write or mutation flows
- network calls that alter external state
- model calls and local model execution
- approval token issuance/consumption
- evidence export/delete/re-issue
- device automation and scheduling actions
- production server touch actions

In this branch, all these are represented as blocked status in UI/state planning.

## 14) Proposed future mapping to LIMA vocabulary

This is a non-authoritative mapping for proof and planning:

```text
ConsumerRequest
  -> User/request payload from operator or queue
  -> static-only fields: tenant_id, operator_id, request_text, requested_capabilities, risk_hint
  -> status must be preview_only | explain_plan | blocked | deferred

HumanInput
  -> intake normalization boundary between Arc shell and runtime
  -> includes operator identity and trust/session references

TypedIntentEnvelope | TaskIntent
  -> normalized typed representation consumed by runtime policy gates
  -> includes intent_class, requested_action_set, tool_pack_hints, constraints, correlation IDs

CandidatePreview
  -> static/plan-grade output (no execution authority)
  -> required fields now:
     - preview_id
     - status (preview_only / explain_plan / blocked / deferred only)
     - action_set
     - rationale
     - risk_tier
     - evidence_ref
     - audit_ref
     - guardian_binding_required (bool)
     - embodiment_profile (required; see below)

RuntimeStateSnapshot
  -> future read-only projection from LIMA Office/Supervisor
  -> health, queue, worker, connector, and model-route posture only

GuardianDecision
  -> future mandatory gate for any consequential action
  -> preview-only flows show decision requirement, not auto-grant

Audit / Spine event
  -> immutable lineage for intake, preview, blocked reason, approval path, and snapshot ingestion
```

### CandidatePreview proposals (all with `embodiment_profile`)

1. `customer_reply_draft_preview`
   - `status`: `preview_only`
   - `status`: draft
   - `goal`: prepare redacted draft text for operator send
   - `tool_pack_hint`: `helpdesk_text_template`
   - `embodiment_profile`:
     - `surface`: `operator_task_runner`
     - `risk_class`: `low`
     - `channel`: `text`
     - `requires_operator_send`: `true`

2. `incident_classification_preview`
   - `status`: `explain_plan`
   - `goal`: show triage path and routing suggestion
   - `tool_pack_hint`: `helpdesk_routing`
   - `embodiment_profile`:
     - `surface`: `operator_overview`
     - `risk_class`: `medium`
     - `channel`: `classification`

3. `connector_setup_readiness_preview`
   - `status`: `deferred`
   - `goal`: present connector readiness checklist without writes
   - `tool_pack_hint`: `connector_control`
   - `embodiment_profile`:
     - `surface`: `operator_connectors`
     - `risk_class`: `medium`
     - `channel`: `admin`
     - `operator_confirmation_required`: `true`

4. `health_snapshot_preview`
   - `status`: `preview_only`
   - `goal`: show one-screen health posture
   - `tool_pack_hint`: `supervisor_health`
   - `embodiment_profile`:
     - `surface`: `overview_health`
     - `risk_class`: `low`
     - `channel`: `dashboard`

5. `diagnostic_plan_preview`
   - `status`: `blocked`
   - `goal`: list diagnostic actions that cannot execute in this phase
   - `tool_pack_hint`: `diagnostic_runner`
   - `embodiment_profile`:
     - `surface`: `operator_runbook`
     - `risk_class`: `high`
     - `channel`: `runbook`

## 15) Block classification policy for this phase

Allowed mock-safe status values:
- `preview_only`
- `explain_plan`
- `blocked`
- `deferred`

All other completion-style statuses are currently invalid in this proof packet.

Any path marked as:
- execution
- diagnostics execution
- network action
- connector write
- provider/model call
- file mutation
- browser action
- device action
- external send
- shell command
- automation action
- production runtime

must use `blocked` in this phase and route to runbook/deferred path.

## 16) What LIMA Runtime should provide before Arc Bot integration

- Public, non-secret contract surfaces for:
  - candidate preview
  - run-time snapshot retrieval
  - guardianship decision envelopes
  - approval metadata binding
  - evidence/audit lineage emission
- Strictly typed intake and intent objects
- Tenant-isolated contract references
- Deterministic snapshot freshness and blocked reason model
- Durable event spine for audit lineage
- Stable operator confirmation/approval binding chain

