# Arc Bot Shell Contracts (Phase-0)

Date: 2026-06-18
Status: Foundation contracts and invariants

## Approved Arc Harness Runtime Contract

Legacy Phase-0/readiness projections remain non-executing. Arc Harness Shell
v0.10 adds one approved runtime contract for `arc.local_model_preview`:

- real Guardian allow with a non-empty unchanged `decision_id` is mandatory;
- the installed public LIMA entrypoint validates
  `executor_kind=loopback_ollama` before invoking the executor;
- only HTTP `127.0.0.1` or `localhost` with an explicit port is allowed;
- credentials, external side effects, redirects, cloud fallback, and alternate
  model fallback are forbidden;
- evidence and state are written for success, controlled unavailability, and
  denied actions;
- external email and every non-preview action remain blocked before LIMA and
  Ollama.

## Contract Families

- `arc_bot_console_state_envelope.schema.json`
- `arc_bot_client_configuration.schema.json`
- `arc_bot_phase1_client_configuration.json`
- `arc_bot_work_queue_state.schema.json`
- `arc_bot_runtime_settings_state.schema.json`
- `arc_bot_overview_state.schema.json`
- `arc_guardian_spine_base_projection`
- `arc_intent_envelope_projection`
- `arc_lima_office_read_adapter_projection`
- `arc_phase_d_approval_evidence_dependency_projection`
- `arc_remaining_implementation_gate_response_projection`
- `arc_remaining_implementation_gate_response.schema.json`
- `arc_field_deployment_readiness_projection`
- `arc_narrow_pilot_readiness_projection`
- `arc_mvp_completion_gate_projection`
- `arc_bot_basic_guardian_console_projection`
- `phase2_ollama_qwen_readiness_projection`
- `phase3_document_intake_preview`
- `phase4_document_extraction_preview`
- `phase5_office_workflow_template_catalog`
- `phase5_office_workflow_preview`
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
- Phase-4 document extraction previews must remain deterministic metadata
  previews unless a later approved phase grants runtime authority. The local
  model provider interface is injectable only and must not call a model.
- Phase-5 office workflow templates must remain draft/preview-only. Saving
  final output, sending external messages, updating customer records,
  submitting forms, and connector writes require approval and remain blocked in
  this phase.
- Phase-G field deployment package projections must remain planning/read-only.
  They must not install software, start services, register workers, probe
  sockets, invoke models, call connectors, write durable evidence, or claim
  production deployment readiness.
- Phase-H narrow pilot readiness projections must remain sanitized,
  planning/read-only, and blocked from live pilot execution. They must use
  Phase-5 draft-preview workflows only and must not process raw customer data,
  invoke models, call connectors, send external messages, write durable
  evidence, or mutate customer systems.
- Phase-12 MVP completion gate projections must not claim MVP completion or
  production readiness while runtime, Guardian, approval, evidence-writer,
  operator-console, local-model, connector, or field deployment gates remain
  unresolved.
- Lima Office external answer packets may be consumed only as contract
  metadata. `approval_token_id`, `approval.token:<approval_token_id>`,
  `approval.binding`, verifier result refs, and read-only supervisor
  projection refs do not grant approval issuance, verification, durable
  evidence writing, local-model execution, connector I/O, or runtime authority.
- Remaining implementation-gate response schemas and templates are intake aids only.
  Blank template values remain incomplete, and a shape-complete response still
  cannot grant runtime authority, local-model invocation, operator-console state
  authority, durable evidence writes, or production deployment.
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

### Phase-4 Document Extraction Preview
- Extraction previews must reuse the Phase-3 intake metadata boundary.
- Deterministic preview output may include filename metadata, classified file
  type, page-count placeholder, checksum placeholder, and operator-supplied
  document category.
- Every extraction preview must include Guardian decision metadata, evidence
  refs, policy refs, runbook refs, and a projection-only Spine event.
- If local model assistance is requested, the projection must require gate data:
  local model seat health, approval token ref, redaction policy ref, and output
  policy ref.
- Even when gate data is present, Phase 4 must not grant local model execution;
  the provider interface remains projection-only until a later approved runtime
  gate.
- File reads/writes, OCR, parser calls, local/cloud model calls, provider SDKs,
  network egress, connector actions, raw content persistence, and
  customer-system mutation remain blocked.

### Phase-5 Office Workflow Templates
- The MVP workflow catalog includes:
  - intake note summary,
  - insurance claim packet triage,
  - policy document summary,
  - missing information checklist,
  - customer-service draft reply,
  - internal follow-up task draft.
- Each workflow must have schema coverage, fixture coverage, proof tests, and a
  blocked-action matrix.
- Workflow output mode is `draft_preview_only`; every output remains pending
  operator review.
- Role profiles are:
  - Document Processing Bot,
  - Customer Support Draft Bot,
  - Billing Intake Assistant,
  - Compliance Review Assistant.
- Role profiles cannot send external messages, update customer records, submit
  forms, write connectors, or grant runtime execution.
- Workflow templates may reference Phase-3 intake and Phase-4 extraction
  preview artifacts, but they must not read files, persist raw content, invoke
  models, use provider SDKs, call connectors, send messages, submit forms, or
  mutate customer systems.

### Arc Guardian/Spine Base
- Minimal contract/stub layer for Arc-local Guardian decisions and Spine events.
- Source-of-truth references are Sparkbot for working Guardian/Spine behavior and LIMA-Guardian-Suite for extraction context.
- No direct import of Sparkbot runtime modules, no direct import of LIMA-Guardian-Suite runtime modules, and no model/connector/file/network execution.
- Local model seat metadata is allowed only as readiness posture for a PC attached to LIMA Office.
- Approval requests must be non-reusable and must not grant runtime or local-model execution in Phase-1.
- Evidence refs must be redacted-reference metadata only; raw office/customer content must not be persisted.
- Local Spine ledger helpers must remain projection-only and must not write to disk.

### Arc Intent Envelope
- Defines the future signed request boundary for Arc-to-LIMA Office handoff.
- Requires action, tenant, worker, operator, task, policy, evidence, runbook,
  redaction policy, output policy, replay-protection, and signature refs.
- Signature refs are metadata only. Arc Bot Shell must not create signatures,
  verify signatures, issue approval tokens, or claim runtime authority.
- Envelope projections must keep `runtime_authority_blocked` and
  `runtime_execution_blocked` true.
- Future verification and replay protection must be owned by LIMA Office /
  Guardian before execution is enabled.

### Arc LIMA Office Read Adapter
- Exports Arc worker shell metadata in a LIMA Office-readable
  `RuntimeStateSnapshot` style shape.
- May include worker posture, local model readiness metadata, preview queue,
  blocked queue, approval-required queue, preview artifact refs, policy refs,
  and evidence refs.
- Must not import LIMA runtime modules, open sockets, persist state, dispatch
  workers, issue approvals, call models, call connectors, mutate customer
  systems, or send external messages.
- Must preserve one Supervisor Server, 1-8 Arc workers, and single-tenant MVP
  assumptions.
- Must keep runtime authority and runtime execution blocked.

### Arc Approval And Evidence Dependency
- Records the Guardian/LIMA Office answers required before approval token
  lineage, replay protection, durable evidence writing, or execution-adjacent
  approval paths can be implemented.
- Must remain `external_answers_recorded_runtime_still_blocked` after the Lima
  Office handoff until remaining owner/runtime gates are approved.
- Records `approval_token_id`, `approval.token:<approval_token_id>`,
  `approval.binding`, LIMA Office Guardian/Supervisor verifier ownership,
  read-only runtime state projection sources, and LIMA Office Supervisor
  evidence-plane ownership as metadata only.
- Must keep operator-console server-state ownership, Guardian-owned
  local-model executor authority, approval issuance/verification
  implementation, verifier-result ingestion, supervisor projection ingestion,
  and durable evidence implementation blocked until later gates.
- Must not issue approval tokens, verify signatures, write durable evidence,
  publish audit/Spine events, or grant runtime authority.

### Arc Remaining Implementation-Gate Response
- Defines the local JSON response shape requested from LIMA Office / Guardian
  owners for the two remaining Phase-D external dependencies.
- The schema requires owner, canonical contract family, authoritative/required
  field lists, Arc-consumable refs, and explicit Arc Bot prohibitions.
- The blank template is intentionally incomplete until an external owner fills
  every required field.
- Complete response-shape inspection still keeps `runtime_authority_blocked` and
  `runtime_execution_blocked` true and must not start implementation by itself.
- Must not assign ownership locally, invoke models, issue or verify approvals,
  write durable evidence, attach to a live Supervisor Server, mutate operator
  console state, or claim MVP completion.

### Arc Field Deployment Package
- Defines the Phase-G setup guides, support runbooks, and read-only smoke
  commands for one Supervisor Server, 1-8 Arc workers, and a single tenant.
- Must keep `runtime_authority_blocked`, `runtime_execution_blocked`,
  `production_ready`, and `production_deployment_allowed` fail-closed.
- Smoke commands may run local projections and tests only.
- Must not install/update software, start services, attach to a live
  Supervisor Server, register with LIMA Office, probe local model sockets,
  invoke local/cloud models, call connectors, send external messages, mutate
  customer systems, write durable evidence, or issue/verify approvals.

### Arc Narrow Pilot Readiness
- Defines the first Phase-H/Phase-11 pilot package for insurance intake
  summary and missing-information checklist.
- Must use sanitized local sample metadata only.
- Must reuse Phase-5 draft-preview workflow IDs:
  `insurance_claim_packet_triage` and `missing_information_checklist`.
- Must keep `runtime_authority_blocked`, `runtime_execution_blocked`,
  `production_ready`, and `pilot_execution_allowed` fail-closed.
- Must not process raw customer documents, invoke local/cloud models, call
  connectors, update customer records, submit forms, send external messages,
  write durable evidence, or claim live pilot/production readiness.

### Arc MVP Completion Gate
- Evaluates Arc Bot against the Phase-12 MVP completion criteria using repo
  artifacts only.
- Must keep `mvp_complete`, `production_ready`, `runtime_authority_blocked`,
  and `runtime_execution_blocked` fail-closed while any criterion lacks direct
  runtime evidence.
- Must identify blocked criteria and missing evidence for supervisor
  attachment, local model execution, approval/evidence lineage, durable
  Spine/audit publication, operator approval workflow, and LIMA Office worker
  state intake.
- Must not grant runtime authority, invoke models, call connectors, write
  evidence, mutate customer systems, or claim completion.

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

## Windows operator contract v0.11

The launcher may enqueue task packets and invoke only the selected release's public harness. It must pass local previews through real Guardian and published LIMA with `executor_kind=loopback_ollama`; denied work must remain `execution_allowed=false`. Install, startup, upgrade, rollback, and uninstall events are logged. Upgrade and rollback preserve `data/`, `logs/`, and `config/`; default uninstall preserves them as well.