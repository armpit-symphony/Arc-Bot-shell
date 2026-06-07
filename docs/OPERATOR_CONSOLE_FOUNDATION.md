# Arc Bot Operator Console Foundation

Date: 2026-06-07

Branch: `port-arc-bot-operator-console-foundation`

Status: foundation specification only. This document does not implement UI code, backend code, persistence, provider/model calls, connector access, worker execution, scheduling, browser automation, terminal/process execution, file mutation, or robotics/device control.

## Purpose

Arc Bot Shell is the operator-facing office-worker shell for a future LIMA Office deployment. The first console foundation must make office work visible, scoped, and fail-closed before any automation exists.

This foundation follows the previous reconstruction audit:

- Arc-Bot-shell currently has product doctrine and no implemented product behavior.
- LIMA Office is the strongest source of truth for office-worker operator flows and contracts.
- LIMA AI OS is future kernel/runtime contract vocabulary and integration seam, not a finished drop-in runtime.
- Sparkbot and Sparkbot_shell are references for lessons and UX vocabulary only; Sparkbot Workstation must not be cloned as Arc Bot.

## Product Frame

Deployment target:

- 1 Supervisor Server.
- 1-8 Arc Bot worker mini PCs.
- 1 customer/tenant at a time.
- Guardian-gated model, tool, file, network, connector, outbound, scheduled, and privileged actions.
- Human approval for high-risk or privileged work.
- Evidence for important decisions and actions.

Current branch posture:

- Display/state foundation only.
- Metadata-only action descriptions.
- No live execution or runtime wiring.
- No frontend localStorage source of truth.
- No secrets in repo tree.

## Console Navigation

The Arc Bot operator console foundation contains these top-level surfaces:

| Surface | Operator purpose | Current state | Primary LIMA Office alignment | Future LIMA AI OS seam |
| --- | --- | --- | --- | --- |
| Overview | Show supervisor health, blocked states, queue posture, worker status, approvals, evidence, connector readiness, and model-route posture | Documented foundation only | `console.view`, `console.alert`, `supervisor.health`, `sla.slo`, `incident.ops` | Shell summary emits read-only state snapshot; no runtime authority |
| Workers | Show Arc worker lifecycle, heartbeat, deployment, capability scope, quarantine/revoke posture | Documented foundation only | `worker.lifecycle`, `worker.heartbeat`, `worker.deployment`, `worker.attestation` | Worker identity/capability metadata maps to future Shell/Driver boundaries |
| Tasks | Show task intake, assignment, status, approval need, evidence refs, model-route posture, and blocked reasons | Documented foundation only | `task.execution`, `guardian.decision`, `approval.request`, `evidence.artifact` | Task requests become future `HumanInput`/`IntentEnvelope`/candidate preview |
| Approvals | Show approval requests, result posture, token binding, expiry, separation checks, and denied states | Documented foundation only | `approval.request`, `approval.result`, `approval.token`, `approval.binding`, `token.verification` | Approval metadata maps to future LIMA `ApprovalMetadata` and Guardian decision refs |
| Guardian | Show Guardian decisions, risk tier, policy refs, taint refs, replay/expiry posture, and denied/blocked states | Documented foundation only | `guardian.decision`, `guardian.replay`, `taint.ref` | Consequential actions require future `ConsequentialActionRequest` and `GuardianDecision` |
| Evidence | Show evidence refs, hashes, redaction, retention, export posture, evidence failures | Documented foundation only | `evidence.artifact`, `evidence.failure`, `evidence.ledger.entry` | Evidence/lineage maps to future LIMA Spine events and storage refs |
| Connectors | Show mock connector readiness, consent/scope/revocation, provider risk, setup blockers | Documented foundation only | `connector.readiness`, `connector.trust`, `connector.scope_review`, `connector.provider_profile`, `governance.connector_consent` | Future tool-pack/adapter boundary; connector writes remain blocked |
| Model / Local AI Readiness | Show model-route posture, local model status, fallback/denial reason codes, worker model bundle refs | Documented foundation only | `model.route`, `supervisor.health`, `worker.lifecycle` model fields | Future Harness seam; no provider/model/local calls in this branch |
| Governance / Audit | Show access review, identity/MFA placeholders, breakglass posture, retention/export/delete posture | Documented foundation only | `governance.identity`, `governance.access_review`, `governance.breakglass`, `governance.audit_export` | Future auth/policy/storage seam; no secret or breakglass runtime |
| Runbooks / Blocked Guidance | Show next safe manual review lane for blocked actions | Documented foundation only | `docs/runbooks/*`, `console.action`, `console.alert` | Human control surface guidance before future governed runtime |

## Required Page Frame

Every future surface must show:

- tenant/customer context
- environment label: `phase0_lab`, `mock`, `dry_run`, or `blocked_mvp`
- operator role
- last refreshed record time
- source contracts
- evidence refs or blocked-missing-evidence state
- policy refs or blocked-missing-policy state
- active blocked states
- runbook links or blocked-action guidance
- future LIMA Office Supervisor seam
- future LIMA AI OS seam

If any required field is missing, the surface renders blocked or review-required. Missing data must not be softened into a ready state.

## Surface Details

### Overview

Available as display/state:

- Supervisor health summary.
- Worker count, stale workers, quarantined workers.
- Queue depth, blocked tasks, tasks needing approval.
- Guardian allow/deny/approval-required counts.
- Evidence writer posture.
- Connector readiness summary.
- Model-route degraded/blocked summary.
- Open incident count.

Metadata-only:

- Acknowledge-review intent.
- Link to runbook.
- Open related record.

Blocked/fail-closed:

- Clear alert without evidence.
- Restart services.
- Start daemons.
- Trigger health collection.
- Dispatch task.
- Execute remediation.

Future seams:

- LIMA Office Supervisor provides the authoritative summary.
- LIMA AI OS may supply read-only candidate/runtime-state snapshots and Guardian lineage.

### Workers

Available as display/state:

- Worker ID, role, lifecycle state, health state.
- Heartbeat age and missed heartbeat count.
- Capability manifest version/hash.
- Tool-pack scope.
- Model options and local model status.
- Quarantine/revoke/re-enrollment posture.
- Deployment and attestation refs.

Metadata-only:

- Request enrollment review.
- Request quarantine review.
- Request re-enrollment review.
- Link evidence or field checklist.

Blocked/fail-closed:

- Install/update software.
- Start/stop worker service.
- Release quarantined worker without review.
- Enable live connector.
- Broaden worker tool pack.
- Touch endpoint or production server.

Future seams:

- LIMA Office Supervisor owns worker registry and lifecycle state.
- LIMA AI OS shell/driver contracts may consume worker capabilities only after Guardian approval.

### Tasks

Available as display/state:

- Task ID, task class, status, assigned worker, risk tier.
- Execution mode: `plan_only`, `read_only`, `draft_only`, `mock_only`, or `blocked_mvp`.
- Required tool packs.
- Guardian decision ID.
- Approval refs when required.
- Evidence refs and failure posture.
- Model route ID/status/reason codes.
- Blocked reason and runbook ref.

Metadata-only:

- Inspect task.
- Filter by blocked/needs approval/draft ready.
- Open Guardian/evidence/approval records.
- Draft operator note for future review.

Blocked/fail-closed:

- Force run task.
- Edit task payload as source of truth.
- Dispatch to worker.
- External sends.
- File mutation.
- Customer record mutation.
- Software update/remediation.

Future seams:

- LIMA Office `task.execution` remains authoritative.
- Future Arc intake maps to LIMA AI OS `HumanInput` and `IntentEnvelope` before Guardian evaluation.

### Approvals

Available as display/state:

- Pending approval request metadata.
- Approval result state.
- Approval token and token verification refs.
- Expiry, replay, scope, separation-of-duty posture.
- Denied, expired, revoked, token-mismatch, and blocked-MVP states.

Metadata-only:

- Review approval context.
- Record intended approve/deny metadata only when future policy allows.
- Link evidence and runbook.

Blocked/fail-closed:

- Self-approve high-risk work.
- Approve blocked-MVP actions.
- Broaden scope.
- Issue live approval tokens.
- Execute the approved action.

Future seams:

- LIMA Office approval contracts bind human approval metadata.
- LIMA AI OS `ApprovalMetadata` and `GuardianDecision` carry runtime linkage when separately approved.

### Guardian

Available as display/state:

- Decision ID, request ID, subject, action class, resource ref.
- Risk tier, decision, policy refs, denial reason.
- Replay policy/status, expiry, token binding, evidence refs.
- Prompt-injection and taint posture.

Metadata-only:

- Inspect decision.
- Link to task, approval, evidence, or runbook.
- Record blocked-review note.

Blocked/fail-closed:

- Override Guardian decision from UI.
- Reuse expired decision.
- Treat tainted content as trusted instruction.
- Reveal Vault or secret material.
- Convert planning labels into runtime authority.

Future seams:

- Future consequential actions must become LIMA AI OS `ConsequentialActionRequest` and receive a durable `GuardianDecision`.

### Evidence

Available as display/state:

- Evidence artifact refs, hashes, chain position, redaction profile.
- Evidence failure state.
- Retention/export eligibility.
- Pre-action and post-action evidence refs.

Metadata-only:

- Inspect redacted evidence metadata.
- Link evidence to task, worker, Guardian decision, incident, or export review.

Blocked/fail-closed:

- Show raw secrets or customer payloads.
- Alter evidence.
- Delete evidence without conflict review.
- Continue privileged action when pre-action evidence is missing.

Future seams:

- LIMA Office evidence ledger remains source of truth.
- LIMA AI OS Spine events may later carry lineage refs and sanitized summaries.

### Connectors

Available as display/state:

- Mock readiness status.
- Consent, scope review, provider risk, revocation drill, ownership refs.
- Live access false by default.

Metadata-only:

- Inspect setup blocker.
- Record revocation review intent.
- Link least-privilege scope review.

Blocked/fail-closed:

- OAuth/provider wiring.
- Token entry.
- Live read/write.
- Connector send.
- Webhook handling.
- Private recall from connector data.

Future seams:

- Future connector adapters require Guardian-gated tool-pack scope and LIMA Office consent/scope/revocation records.

### Model / Local AI Readiness

Available as display/state:

- Model-route posture: `mock_only`, `local_planned`, `subscription_planned`, `blocked_mvp`.
- Route status: selected, degraded, denied, blocked, unavailable.
- Route reason codes.
- Worker local model status.
- Policy/model bundle refs.

Metadata-only:

- Inspect route decision.
- Link model-route evidence.
- Record setup-required note.

Blocked/fail-closed:

- External model provider calls.
- Local model calls.
- Subscription CLI/session bridges.
- Provider key entry.
- Model fallback dispatch.
- Treat selected route as execution approval.

Future seams:

- LIMA Office model-route posture governs office deployment state.
- LIMA AI OS Harness may later classify model calls and plan tool calls only after Guardian decision linkage.

### Governance / Audit

Available as display/state:

- Identity/MFA/access review posture.
- Breakglass denial or placeholder state.
- Retention/redaction/export/delete posture.
- Audit/export/delete request state.

Metadata-only:

- Inspect access review.
- Link export/delete scope.
- Record finding or review request metadata.

Blocked/fail-closed:

- Runtime breakglass.
- Secret reveal/write.
- Automatic export/delete.
- Cross-tenant memory sharing.
- Privileged role self-review.

Future seams:

- LIMA Office governance contracts remain source of truth.
- LIMA AI OS auth, policy, storage, and privacy contracts may become kernel seams only after approval.

### Runbooks / Blocked Guidance

Available as display/state:

- Runbook links for worker, approval, evidence, prompt injection, connector, LIMA IT, health, and audit/export/delete flows.
- Blocked action reason.
- Next safe manual review lane.

Metadata-only:

- Open runbook.
- Attach runbook ref to a blocked record.

Blocked/fail-closed:

- Execute runbook steps automatically.
- Run diagnostics.
- Remediate systems.
- Schedule background checks.

Future seams:

- Runbooks remain human control-surface guidance.
- Any future runbook automation must become Guardian-gated action requests with evidence.

## Foundation State Boundary

No frontend or backend implementation exists in this repo in this branch. Therefore no persistence is introduced.

If a future UI is added, all product state must be server-side. Frontend state may only hold transient UI state such as selected tab, expanded row, or local form draft, and must not become source of truth for:

- tasks
- approvals
- Guardian decisions
- worker lifecycle
- evidence
- connector readiness
- model routing
- governance/audit state
- secrets
- memory/context
- shell/worker handoff records

The future server-side state boundary is defined in [Arc Bot Operator Console State Contract](contracts/ARC_BOT_OPERATOR_CONSOLE_STATE.md).

## Secrets Policy

Arc-Bot-shell must not store runtime secrets inside the repo tree by default.

Future default:

- `$XDG_DATA_HOME/arc-bot-shell/...` when `XDG_DATA_HOME` is set.
- Otherwise `~/.local/share/arc-bot-shell/...`.

Future override:

- `ARC_BOT_SECRETS_DIR`

This branch stores no secrets and adds no secret-loading code.

## Explicit No-Runtime Boundary

This foundation does not add:

- provider calls
- local model calls
- connector reads or writes
- external sends
- file mutation
- terminal/process execution
- browser automation
- scheduler/background execution
- worker daemon or worker execution
- device/robotics control
- LIMA runtime wiring
- Guardian/Vault internals
- CLI/session/token bridges
- localStorage/sessionStorage product state

## Acceptance Criteria For This Foundation

- Operator surfaces are named and aligned to LIMA Office contracts.
- Each surface distinguishes display/state, metadata-only, blocked/fail-closed, and future seams.
- No Sparkbot Workstation behavior is copied as Arc Bot product code.
- No UI/frontend/backend stack is invented.
- No runtime execution path is added.
- Future state boundary is server-side.
- Secrets policy remains outside the repo tree.
