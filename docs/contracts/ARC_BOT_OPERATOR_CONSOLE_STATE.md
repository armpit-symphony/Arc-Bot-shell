# Arc Bot Operator Console State Contract

Date: 2026-06-07

Status: contract-bound foundation only. This document defines the future server-side state shape for Arc Bot operator-console work. It does not implement persistence, adapters, UI code, backend routes, execution, dispatch, approvals, provider calls, connector calls, scheduler jobs, workers, or LIMA runtime wiring.

## Source References

- `docs/audits/ARC_BOT_RECONSTRUCTION_DOCS_AND_SOURCE_MAP.md`
- `docs/OPERATOR_CONSOLE_FOUNDATION.md`
- LIMA Office `docs/ux/OPERATOR_CONSOLE_SPEC.md`
- LIMA Office `docs/ux/OPERATOR_WORKFLOWS.md`
- LIMA Office `contracts/v1/console.view.schema.json`
- LIMA Office `contracts/v1/task.execution.schema.json`
- LIMA Office `contracts/v1/worker.lifecycle.schema.json`
- LIMA Office `contracts/v1/worker.heartbeat.schema.json`
- LIMA Office `contracts/v1/guardian.decision.schema.json`
- LIMA Office approval, evidence, connector, model-route, governance, and audit contracts

## State Authority Rule

Arc Bot product state must be server-side when implementation begins.

Frontend localStorage, sessionStorage, IndexedDB, cookies, URL hash, or React component state may never be the source of truth for product state. They may only hold transient interface state such as selected tab, sort order, or an unsaved display-only draft.

## Console State Envelope

Every future console state response should carry this envelope:

| Field | Required | Meaning |
| --- | --- | --- |
| `tenant_id` | yes | One customer/tenant context. |
| `customer_context_id` | yes | Customer workspace/context ref. |
| `environment` | yes | `phase0_lab`, `mock`, `dry_run`, or `blocked_mvp`. |
| `operator_role` | yes | Role such as owner/operator, approver, field IT, security reviewer, auditor. |
| `view_id` | yes | Stable console view ID. |
| `view_type` | yes | One of the operator-console surfaces. |
| `view_mode` | yes | `readonly`, `review_only`, or future `approval_capable`. |
| `status` | yes | Rendered, review-required, degraded, or blocked state. |
| `policy_refs` | yes | Policy refs required for any non-empty operational view. |
| `evidence_refs` | yes | Evidence refs or blocked-missing-evidence status. |
| `related_contract_refs` | yes | LIMA Office contract refs backing the view. |
| `blocked_reason` | required when blocked | Concrete fail-closed reason. |
| `runbook_refs` | yes | Human review/runbook links. |
| `future_lima_office_supervisor_seam` | yes | Supervisor-owned state source expected later. |
| `future_lima_ai_os_seam` | yes | LIMA Runtime contract seam expected later. |

Schema-aligned validation artifacts for Phase-0 snapshots:

- `docs/contracts/schemas/arc_bot_console_state_envelope.schema.json`
- `docs/contracts/schemas/arc_bot_work_queue_state.schema.json`
- `docs/contracts/schemas/arc_bot_runtime_settings_state.schema.json`
- `docs/contracts/schemas/arc_bot_overview_state.schema.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_contract_pack.json`
- `tests/fixtures/arc_bot_phase0_overview_state_snapshot.json`

## Surface State Groups

### Overview State

Server-side source of truth when implemented:

- supervisor health summary
- worker fleet counters
- task queue counters
- approval counters
- Guardian decision counters
- evidence writer posture
- connector readiness summary
- model-route posture summary
- governance/audit posture
- incident count
- active blocked states

Aligned contracts:

- `console.view`
- `console.alert`
- `supervisor.health`
- `guardian.decision`
- `evidence.failure`
- `incident.ops`
- `sla.slo`

Blocked if missing:

- tenant/customer context
- policy refs
- evidence refs where required
- Guardian decision refs for consequential status
- runbook refs for blocked states

### Worker State

Server-side source of truth when implemented:

- worker ID and role
- deployment ID
- lifecycle state
- heartbeat age and missed count
- capability manifest version/hash
- tool-pack scope
- model options and local model status
- identity verification
- attestation refs
- quarantine/revoke/re-enrollment state
- evidence refs

Aligned contracts:

- `worker.lifecycle`
- `worker.heartbeat`
- `worker.deployment`
- `worker.attestation`
- `governance.device_trust`
- `console.action`

Blocked if missing:

- worker identity
- tenant match
- capability manifest
- Guardian decision ref for lifecycle change
- evidence ref for quarantine/revoke/re-enrollment

### Task State

Server-side source of truth when implemented:

- task ID
- task class
- assigned worker
- status
- risk tier
- data classification
- execution mode
- task scope
- required tool packs
- Guardian decision ID
- approval refs
- model route refs
- evidence refs
- blocked reason and runbook

Aligned contracts:

- `task.execution`
- `guardian.decision`
- `approval.request`
- `approval.result`
- `approval.token`
- `token.verification`
- `evidence.artifact`

Blocked if missing:

- Guardian decision ID
- policy refs
- evidence refs for terminal/high-risk states
- token verification where approval is required
- model-route status for high-risk task paths

### Work Program State

Server-side source of truth when implemented:

- work program ID and title
- work objective and detail summary
- assigned worker role/class
- worker type tags and status (`draft`, `ready`, `active`, `completed`)
- training memo and safety notes
- attached SOP/work file references
- required model route posture for dispatch readiness
- local model-seat readiness reference
- operator-created evidence refs and blocked reason

Aligned contracts:

- `task.execution`
- `model.route`
- `guardian.decision`
- `evidence.artifact`

Blocked if missing:

- tenant context and operator role for program scope
- policy refs for local dispatch preparation
- evidence refs where program state gates high-risk or external work
- model-route readiness refs before active/deployment transition
- task or worker mapping references for assignment

### Approval State

Server-side source of truth when implemented:

- approval request ID
- approval result ID
- approval token ID
- approval binding ID
- token verification ID
- decision ID
- scope hash
- expiry
- replay state
- separation-of-duty posture
- evidence refs

Aligned contracts:

- `approval.request`
- `approval.result`
- `approval.token`
- `approval.binding`
- `token.verification`
- `guardian.replay`
- `guardian.decision`

Blocked if missing:

- policy refs
- evidence refs
- matching Guardian decision
- valid token verification for approval-required work
- separation-of-duty confirmation for high-risk work

### Guardian State

Server-side source of truth when implemented:

- decision ID
- request ID
- subject
- action class
- resource ref
- risk tier
- decision
- approval required
- denial reason
- replay status
- expiry
- prompt-injection posture
- evidence refs
- policy refs

Aligned contracts:

- `guardian.decision`
- `guardian.replay`
- `taint.ref`
- `evidence.artifact`

Blocked if missing:

- policy refs
- evidence refs
- bound tenant/task/worker refs when applicable
- unexpired decision for any future execution path

### Evidence State

Server-side source of truth when implemented:

- artifact ID
- failure ID
- hash/integrity refs
- redaction profile
- retention class
- export eligibility
- pre-action and post-action refs
- parent chain refs
- access control refs

Aligned contracts:

- `evidence.artifact`
- `evidence.failure`
- `evidence.ledger.entry`
- `evidence.export_manifest`
- `governance.audit_export`

Blocked if missing:

- evidence required but absent
- raw content would be exposed
- secret material would be exposed
- retention/export/delete policy is missing

### Connector State

Server-side source of truth when implemented:

- connector readiness ID
- connector trust ref
- consent ref
- scope review ref
- provider risk profile
- revocation/disable drill posture
- ownership and escalation refs
- live access flag, default false

Aligned contracts:

- `connector.trust`
- `connector.readiness`
- `connector.scope_review`
- `connector.provider_profile`
- `connector.revocation_drill`
- `connector.reconciliation`
- `governance.connector_consent`

Blocked if missing:

- consent
- scope review
- revocation posture
- provider risk profile
- ownership source of truth
- prompt-injection containment posture

### Model / Local AI Readiness State

Server-side source of truth when implemented:

- model route ID
- route mode
- route status
- route reason codes
- fallback posture
- local model bundle ref
- worker attestation refs for local planned routes
- policy/model bundle hash refs

Aligned contracts:

- `model.route`
- `supervisor.health`
- `worker.lifecycle`
- `worker.attestation`
- `update.rollback`

Blocked if missing:

- route status
- reason codes for degraded/blocked
- policy refs
- evidence refs
- attestation refs when local route is selected
- provider/local model readiness proof

### Governance / Audit State

Server-side source of truth when implemented:

- identity/MFA posture
- access review state
- breakglass posture
- role and separation checks
- audit/export/delete request state
- retention/redaction conflicts
- connector revocation and cache purge refs

Aligned contracts:

- `governance.identity`
- `governance.rbac_matrix`
- `governance.access_review`
- `governance.breakglass`
- `governance.audit_export`
- `governance.export_delete_review`

Blocked if missing:

- role context
- MFA/session/device posture for privileged views
- retention/export/delete policy
- evidence refs
- separation-of-duty checks

## Display Action Taxonomy

Future UI actions must be classified before implementation:

| Action posture | Meaning | Examples | Runtime status |
| --- | --- | --- | --- |
| `display_only` | Inspect existing server-side metadata | View task, view worker, view decision, view evidence | Allowed for foundation design |
| `metadata_review_only` | Record or prepare review metadata without executing target action | Draft denial note, request review, link runbook | Future server implementation requires contract approval |
| `approval_metadata_only` | Create approval result metadata without executing approved action | Approve/deny record where allowed | Future server implementation requires approval-token contracts |
| `blocked_mvp` | Explicitly denied for MVP/foundation | External sends, connector writes, file mutation, remediation | Must render blocked |
| `future_guardian_gated` | Possible later only through Guardian and evidence | Worker quarantine, connector enablement, model route selection | Not implemented in this branch |

## Fail-Closed Action List

The foundation must render these as blocked unless a later branch explicitly approves, implements, and audits Guardian-gated behavior:

- file mutation
- terminal/process execution
- browser automation
- device/robotics control
- connector writes
- connector live reads
- external sends
- form submissions
- scheduler/background execution
- worker daemon execution
- production server touch
- software install/update/remediation
- provider/model calls
- local model calls
- local CLI auth/session bridges
- token bridges
- private Guardian/Vault internals
- raw secret access
- cross-tenant memory sharing
- automatic export/delete

## Future Persistence Boundary

When persistence is approved, use server-side storage only. The persistence layer should:

- store sanitized state records, not raw prompts or secrets
- link every high-risk state to policy refs and evidence refs
- bind tenant, customer context, worker, task, and decision IDs
- reject cross-tenant state
- record redaction/retention posture
- keep approval and Guardian decision lineage immutable enough for audit review

Secrets storage must remain outside the repo tree:

- `$XDG_DATA_HOME/arc-bot-shell/...` when `XDG_DATA_HOME` is set
- otherwise `~/.local/share/arc-bot-shell/...`
- override: `ARC_BOT_SECRETS_DIR`

## LIMA AI OS Seams

Future integration may use:

- `ShellManifest` for Arc Bot shell identity and tool-pack scope.
- `HumanInput` for operator/task intake.
- `IntentEnvelope` for typed task intent.
- `ConsequentialActionRequest` for anything that could execute, mutate, call out, or expose secrets.
- `GuardianDecision` for mandatory action gating.
- `ApprovalMetadata` for human approval lineage.
- `SpineEvent` for audit/evidence lineage.
- `StorageProtocol` for future persistence interface.
- `candidate_preview` and read-only runtime-state inspection for non-authoritative preview only.

These seams do not exist as live Arc Bot runtime wiring in this branch.
