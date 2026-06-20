# Arc Bot Shell Contracts (Phase-0)

Date: 2026-06-18
Status: Foundation contracts and invariants

## Contract Families

- `arc_bot_console_state_envelope.schema.json`
- `arc_bot_client_configuration.schema.json`
- `arc_bot_phase1_client_configuration.json`
- `arc_bot_work_queue_state.schema.json`
- `arc_bot_runtime_settings_state.schema.json`
- `arc_bot_overview_state.schema.json`
- `arc_guardian_spine_base_projection`
- fixture contracts under `tests/fixtures/*`
- proof packets under `docs/proof_packets/*`

## Required Contract Invariants

- Client configuration contracts must remain `docs_only` and phase-gated.
- Client configuration contracts must not contain secret values, provider tokens, API keys, OAuth client secrets, or credential material.
- Client configuration contracts must keep single-tenant assumptions explicit and cross-tenant memory disabled.
- `projection_scope` must remain `read_only` for Phase-0 runtime UI scaffold modules.
- `runtime_authority_blocked` must be `true` for all seam outputs.
- Arc Guardian/Spine base projections must remain local-model-only, single-tenant, and connector-disabled.
- Arc Guardian/Spine base projections must not invoke the local model; they may only emit approval-required or preview-only decisions.
- `source_access_mode` must be `read_only`.
- `projection_gate.required` must be `true` and gate checks enforced in builders.
- `contract_refs`, `policy_refs`, `evidence_refs`, `runbook_refs` must be present and non-empty where applicable.

## Surface Contracts

### Overview
- Display-only supervisor, queue, approval, incident, and connector health summaries.
- No worker control, model-route mutation, connector write, or customer system mutation authority.

### Work Queue
- Display-only snapshot status and readiness.
- No `customer_system_mutation_allowed`, no `external_message_send_allowed`, no `tool_execution_allowed`.

### Runtime Settings
- Metadata and readiness posture only.
- No model/provider/connector mutation or execution paths.

### Arc Guardian/Spine Base
- Minimal contract/stub layer for Arc-local Guardian decisions and Spine events.
- Source-of-truth references are Sparkbot for working Guardian/Spine behavior and LIMA-Guardian-Suite for extraction context.
- No direct import of Sparkbot runtime modules, no direct import of LIMA-Guardian-Suite runtime modules, and no model/connector/file/network execution.
- Local model seat metadata is allowed only as readiness posture for a PC attached to LIMA Office.
- Approval requests must be non-reusable and must not grant runtime or local-model execution in Phase-1.
- Evidence refs must be redacted-reference metadata only; raw office/customer content must not be persisted.
- Local Spine ledger helpers must remain projection-only and must not write to disk.

### Client Configuration
- Static planning contract for tenant boundary, deployment topology, operator roles, connector posture, policy posture, and evidence requirements.
- No persistence, connector live I/O, OAuth, webhook handling, credential access, customer-system mutation, tenant switching, or production deployment authority.

### Overview
- Operator-level summary and health snapshot preview.
- No runtime execution control.
- No model/tool/connector/worker-dispatch authority.

## Change Discipline

- Contract changes require proof packet updates.
- Proof packet changes require test coverage in `tests/test_arc_bot_runtime_ui_scaffold_*`.
- Fail-closed test checks must block missing fields and unexpected runtime authority.
