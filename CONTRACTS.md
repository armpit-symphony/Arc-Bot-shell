# Arc Bot Shell Contracts (Phase-0)

Date: 2026-06-18
Status: Foundation contracts and invariants

## Contract Families

- `arc_bot_console_state_envelope.schema.json`
- `arc_bot_work_queue_state.schema.json`
- `arc_bot_runtime_settings_state.schema.json`
- `arc_bot_overview_state.schema.json`
- fixture contracts under `tests/fixtures/*`
- proof packets under `docs/proof_packets/*`

## Required Contract Invariants

- `projection_scope` must remain `read_only` for Phase-0 runtime UI scaffold modules.
- `runtime_authority_blocked` must be `true` for all seam outputs.
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

### Overview
- Operator-level summary and health snapshot preview.
- No runtime execution control.
- No model/tool/connector/worker-dispatch authority.

## Change Discipline

- Contract changes require proof packet updates.
- Proof packet changes require test coverage in `tests/test_arc_bot_runtime_ui_scaffold_*`.
- Fail-closed test checks must block missing fields and unexpected runtime authority.
