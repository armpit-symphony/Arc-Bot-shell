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
- `arc_bot_basic_guardian_console_projection`
- `phase2_ollama_qwen_readiness_projection`
- `phase3_document_intake_preview`
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
- Basic Guardian console projections must keep Local Model, LIMA Office, upload,
  training, self-learning, and chat controls Guardian-gated and blocked from
  runtime execution until later approved wiring exists.
- Phase-2 Ollama/Qwen readiness projections must remain operator-attested,
  local-model-only, no-probe, no-model-invocation, no-provider-token, and
  no-cloud-fallback.
- LIMA Office Ollama/Qwen readiness packets may be consumed only as read-only
  metadata. Packet fields are labels/refs, not execution authority.
- Phase-3 document intake previews must validate metadata only and must not
  read, parse, OCR, persist, or model-process raw document content.
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

### Basic Guardian Console
- Static operator-facing UI shell for local model status, LIMA Office status,
  document upload staging, training notes, self-learning review mode, and chat.
- Connection buttons are approval-required placeholders only.
- File selection must not upload, read, persist, or process file content.
- Training and self-learning must not write memory directly.
- Chat must not invoke local or cloud models directly from the page.

### Phase-2 Ollama/Qwen Readiness
- Runtime target is `ollama`.
- Model family target is `qwen`.
- Default planning model tag is `qwen2.5:7b`.
- Endpoint is a label only: `http://127.0.0.1:11434`.
- Readiness status may be displayed as `ready`, `setup_required`, or `blocked`.
- The readiness projection must not open sockets, call Ollama APIs, use provider
  SDKs, invoke local/cloud models, store credentials, or mutate LIMA Office.
- Future live readiness checks must be owned by Guardian/LIMA Office and mapped
  back as evidence refs.
- LIMA Office packet `route_status = degraded` maps to setup-required.
  `denied`, `blocked_mvp`, and `unavailable` map to blocked. `mock_only` never
  maps to live-ready.

### Phase-3 Document Intake
- Intake request metadata must include document ID, source/upload ref, document
  type or auto classification, tenant ID, sensitivity class, intake operator,
  and allowed processing mode.
- Supported MVP document types are PDF, text, image scan, and Word document.
- Only metadata preview and manual-review modes are allowed.
- Intake previews must return ready-for-review or blocked status.
- Raw document content must not appear in projections, proof packets, fixtures,
  logs, or repo state.
- OCR, parser calls, local model calls, file reads/writes, connector actions,
  and customer-system mutation remain blocked.

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
