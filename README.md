# Arc Bot Shell

Customizable guarded business worker-bot shell for LIMA Office deployments.

Arc Bot Shell is the starting point for building role-specific AI worker bots for businesses. Each Arc Bot is designed to intake work, preview tasks, request approval when needed, track evidence, and operate under strict business guardrails.

Arc Bot Shell is proprietary/customizable business infrastructure. It is not Sparkbot, not Sparkbot Lite, not the public open-source hobbyist workstation, and not LIMA AI OS itself.

## System Relationship

- LIMA AI OS = universal reasoning/runtime operating system and safety substrate
- LIMA Office = business automation suite / local control plane
- Arc Bot Shell = customizable worker-bot shell that sits on top of LIMA Office and LIMA AI OS
- LIMA IT = IT/security/service layer over LIMA Office
- Sparkbot Public = open-source hobbyist workstation/buzz product, separate from Arc Bot

## What Arc Bot Is

- A customizable task-oriented business bot shell
- Designed for client/business deployments
- Intended to run locally or on a mini PC/node inside a business
- Connected conceptually to LIMA Office as the business control plane
- Based on LIMA AI OS concepts for preview, safety posture, and runtime contracts
- Built around Guardian-style approval/audit boundaries
- Designed for business workflows, not hobbyist experimentation

## What Arc Bot Is Not

- Not Sparkbot
- Not a public hobbyist workstation
- Not a broad personal computer-control assistant
- Not LIMA AI OS itself
- Not LIMA Office itself
- Not LIMA IT
- Not a robot/IoT controller by default
- Not an unrestricted automation runner
- Not allowed to execute, dispatch, persist, or mutate without future explicit approved wiring

## Product Boundary Decision (Committed)

- Arc Bot is explicitly **not** an execution platform in this repository; it is a
  contract-first shell for guarded office worker workflows.
- The shell is a boundary layer above LIMA Office / LIMA AI OS, with
  runtime authority intentionally delayed to approved downstream phases.
- Runtime decisions are display-first and preview-only until runtime authority
  gates and migration criteria are accepted in later phases.
- This aligns with `DECISIONS.md` ADR-05.

## Core Shell Surfaces

### Task Inbox

- Incoming tasks
- Status filters
- Priority/risk labels
- Assigned bot/persona
- Client/workspace context

### Task Runner Panel

- Task details
- Preview/explain-plan
- Proposed steps
- Blocked/deferred reasons
- Next operator action
- Safe/non-authoritative output

### Approval Queue

- Actions requiring human approval
- Pending approval posture
- Approval owner
- Blocked/PIN/breakglass labels
- No real approval enforcement in shell skeleton yet

### Connector Status

- Configured/missing/disabled connectors
- Setup-required state
- Read/write scope labels
- Business system readiness

### Evidence Panel

- Preview evidence
- Audit references
- Decision notes
- Task history
- Exportable proof later

### Client Config

- Client/business profile
- Department/workflow settings
- Policy posture
- Connector profile
- Local node identity
- Deployment notes

### Bot Role / Persona Template

- Role name
- Purpose
- Allowed task categories
- Forbidden task categories
- Risk tier
- Escalation path
- Kill switch
- Expiration or review date
- Client-specific instructions

## Planned Business Worker Roles

- Office Manager Bot
- Scheduling Bot
- Billing Assistant Bot
- Customer Support Bot
- HR Intake Bot
- Compliance Assistant Bot
- Document Processing Bot
- Sales/CRM Assistant Bot
- IT Helpdesk Frontline Bot
- Operations Coordinator Bot
- Custom Client Worker Bot

## Strict Default Posture

Arc Bot starts from a stricter posture than Sparkbot public. It is task-oriented by default, approval/audit/evidence first, and intentionally avoids broad personal workstation behavior.

Default assumptions:

- Preview first
- Explain-plan before risky work
- External writes require approval posture
- Admin actions require block/PIN/breakglass posture
- Secrets require Guardian/Vault posture
- Scheduled work is planned only until explicitly approved
- Connector writes are gated
- Physical-world/robotics/IoT actions are blocked/deferred unless future proprietary LIMA systems explicitly enable them
- No hidden autonomy
- No background action without policy

## Task Lifecycle

```text
new_task
  -> classified
  -> previewed
  -> explain_plan_ready
  -> approval_required or blocked or draft_ready
  -> approved_by_guardian_later
  -> dispatch_ready_later
  -> completed_later
  -> evidence_recorded_later
```

The current shell roadmap may describe these states, but it must not implement dispatch, approval enforcement, persistence, or live mutation paths until the surrounding LIMA Office/LIMA AI OS contracts are explicitly approved.

## Separation Roadmap

### Phase 0 - Repo Foundation

- README roadmap
- Product boundary
- Proprietary/public split
- License/private distribution decision
- Contribution/internal collaboration placeholder
- Security policy placeholder

### Phase 1 - Business Shell Inventory

- Define default worker-bot shell surfaces
- Define task status model
- Define approval posture labels
- Define evidence/audit display needs
- Define connector readiness display needs
- Define client configuration fields
- Define bot role/persona template fields

### Phase 2 - Contract-First Planning

- Define LIMA Office shell contract assumptions
- Define LIMA AI OS runtime boundary assumptions
- Define Guardian/Vault posture language
- Define no-execution skeleton rules
- Define read/write/admin risk tiers
- Define business workflow classification categories
- Define future deployment/node identity model

### Phase 3 - Shell Skeleton Design

- Task Inbox wireframe
- Task Runner Panel wireframe
- Approval Queue wireframe
- Connector Status wireframe
- Evidence Panel wireframe
- Client Config wireframe
- Bot Role / Persona Template wireframe

### Phase 4 - Sanitized Implementation Planning

- Import only approved shell-safe files when implementation begins
- Do not copy Sparkbot workstation behavior
- Do not copy proprietary LIMA internals
- Do not add live adapters
- Do not add execution, dispatch, approval enforcement, or persistence code
- Run secret scan before any public or client handoff
- Run dependency/license review before implementation grows

### Phase 5 - Business MVP Definition

- Role-specific task inbox
- Preview-only task runner
- Draft/explain-plan output
- Approval queue display state
- Connector readiness display
- Evidence/audit placeholder display
- Client config/profile screen
- Bot role/persona template screen
- No live writes, no hidden autonomy, no hardware control

## Public/Private Boundary

Arc Bot Shell is not the open-source hype bot. Sparkbot Public owns the community workstation story. Arc Bot Shell owns the guarded business worker-bot story.

The shell may use public-facing language in demos, but its roadmap should stay honest about the trust boundary: business actions, connector writes, admin actions, secrets, client workflows, and evidence records belong behind approved LIMA Office, LIMA AI OS, Guardian, and Vault contracts.

### Repo distribution model

- Arc Bot Shell is treated as a **private/internal repository** for phase-0 and phase-1 development in this branch.
- Distribution is limited to approved internal review channels unless a future ADR changes this posture.
- The repo includes an explicit proprietary license file:
  `LICENSE`.

## Repo Status

This repo is currently a roadmap/staging repo for the Arc Bot business worker-bot shell. It should remain documentation-only until the shell boundaries, client-safe configuration model, and LIMA Office/LIMA AI OS integration contracts are approved.

## Current Foundation Docs

- [Arc Bot Operator Console Foundation](docs/OPERATOR_CONSOLE_FOUNDATION.md)
- [Arc Bot Completion Audit And Phase Plan](docs/audits/ARC_BOT_COMPLETION_AUDIT_AND_PHASE_PLAN.md)
- [Arc Bot Operator Console State Contract](docs/contracts/ARC_BOT_OPERATOR_CONSOLE_STATE.md)
- [Arc Guardian/Spine Base](docs/ARC_GUARDIAN_SPINE_BASE.md)
- [Arc Intent Envelope Contract](docs/contracts/ARC_INTENT_ENVELOPE.md)
- [Arc LIMA Office Read Adapter Contract](docs/contracts/ARC_LIMA_OFFICE_READ_ADAPTER.md)
- [Arc Approval And Evidence Dependency Contract](docs/contracts/ARC_APPROVAL_EVIDENCE_DEPENDENCY.md)
- [Arc Bot Lima Office External Answers](docs/interop/ARC_BOT_LIMA_OFFICE_EXTERNAL_ANSWERS.md)
- [Arc Bot Remaining Implementation Gate Request](docs/requests/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_REQUEST.md)
- [Arc Worker Local PC Setup Guide](docs/deployment/ARC_WORKER_LOCAL_PC_SETUP.md)
- [Arc Field Deployment Package](docs/deployment/ARC_FIELD_DEPLOYMENT_PACKAGE.md)
- [Insurance Intake Narrow Pilot](docs/pilots/INSURANCE_INTAKE_NARROW_PILOT.md)
- [Insurance Intake Sample Data Policy](docs/pilots/INSURANCE_INTAKE_SAMPLE_DATA_POLICY.md)
- [Arc Bot MVP Completion Gate](docs/readiness/ARC_BOT_MVP_COMPLETION_GATE.md)
- [Arc Bot Basic Guardian Console](ui/arc_bot_basic_console.html)
- Arc Bot Phase-4 document extraction preview:
  `python -m phase4_document_extraction.extraction`
- Arc Bot Phase-5 office workflow templates:
  `python -m phase5_office_workflows.workflows`
- [Arc Bot Phase-2 Ollama/Qwen Readiness Request For LIMA Office](docs/LIMA_OFFICE_TEAM_PHASE2_REQUEST.md)
- [Arc Bot Client Configuration Schema](docs/contracts/schemas/arc_bot_client_configuration.schema.json)
- [Arc Bot No-Execution Skeleton Plan](docs/NO_EXECUTION_SKELETON_PLAN.md)
- [Arc Bot Client Configuration Fixture](tests/fixtures/arc_bot_phase1_client_configuration.json)
- [Arc Bot Client Configuration No-Execution Packet Fixture](tests/fixtures/arc_bot_phase1_client_configuration_no_execution_packet.json)
- [Arc Bot Phase-1 Business Inventory Contract](tests/fixtures/arc_bot_phase1_business_inventory.json)
- [Arc Bot Phase-1 Business Inventory Schema](docs/contracts/schemas/arc_bot_phase1_business_inventory.schema.json)
- [Arc Bot Phase-1 Business Inventory Wireframes](docs/wireframes/ARC_BOT_PHASE1_BUSINESS_INVENTORY_WIREFRAMES.md)
- [Arc Bot Runtime UI Schemas](docs/contracts/schemas/arc_bot_console_state_envelope.schema.json)
  - [work queue snapshot schema](docs/contracts/schemas/arc_bot_work_queue_state.schema.json)
  - [runtime settings snapshot schema](docs/contracts/schemas/arc_bot_runtime_settings_state.schema.json)
  - [overview snapshot schema](docs/contracts/schemas/arc_bot_overview_state.schema.json)
- [Arc Bot Runtime UI Scaffold Contract Pack](tests/fixtures/arc_bot_runtime_ui_scaffold_contract_pack.json)
- [Arc Bot Runtime UI Scaffold Adapter Proof Packet](docs/proof_packets/ARC_BOT_RUNTIME_UI_SCAFFOLD_PHASE0_ADAPTER_PROOF_PACKET.md)
- [Arc Bot Runtime UI Scaffold Guardian Suite Seam Proof Packet](docs/proof_packets/ARC_BOT_RUNTIME_UI_SCAFFOLD_PHASE0_GUARDIAN_SUITE_SEAM_PROOF_PACKET.md)
- [Arc Bot Runtime UI Scaffold Scope-Lock Status Snapshot Proof Packet](docs/proof_packets/ARC_BOT_RUNTIME_UI_SCAFFOLD_PHASE0_SCOPE_LOCK_STATUS_SNAPSHOT_PROOF_PACKET.md)
- [Arc Bot Runtime UI Scaffold Runtime-Control Renderer Proof Packet](docs/proof_packets/ARC_BOT_RUNTIME_UI_SCAFFOLD_PHASE2_RUNTIME_CONTROL_RENDERER_HANDOFF_PROOF_PACKET.md)
- [Arc Bot Runtime UI Scaffold Runtime-Control Execution Planning Proof Packet](docs/proof_packets/ARC_BOT_RUNTIME_UI_SCAFFOLD_PHASE3_RUNTIME_CONTROL_EXECUTION_HANDOFF_PROOF_PACKET.md)
- [Arc Bot Phase-1 Client Configuration No-Execution Packet](docs/proof_packets/ARC_BOT_PHASE1_CLIENT_CONFIGURATION_NO_EXECUTION_PACKET.md)
- [Arc Bot Phase-1 Client Configuration Migration Gate Packet](docs/proof_packets/ARC_BOT_PHASE1_CLIENT_CONFIGURATION_MIGRATION_GATE_PACKET.md)
- [Arc Bot Phase-1 Business MVP Roadmap Packet](docs/proof_packets/ARC_BOT_PHASE1_MVP_ROADMAP_PACKET.md)
- [Arc Bot Phase-1 Readiness Bundle Packet](docs/proof_packets/ARC_BOT_PHASE1_READINESS_BUNDLE_PACKET.md)
- [Arc Bot Phase-1 Runtime Authority Gating Packet](docs/proof_packets/ARC_BOT_PHASE1_RUNTIME_AUTHORITY_GATING_PACKET.md)
- [Arc Bot Phase-B Intent Envelope Packet](docs/proof_packets/ARC_BOT_PHASE_B_INTENT_ENVELOPE_PACKET.md)
- [Arc Bot Phase-C LIMA Office Read Adapter Packet](docs/proof_packets/ARC_BOT_PHASE_C_LIMA_OFFICE_READ_ADAPTER_PACKET.md)
- [Arc Bot Phase-D Approval Evidence Dependency Packet](docs/proof_packets/ARC_BOT_PHASE_D_APPROVAL_EVIDENCE_DEPENDENCY_PACKET.md)
- [Arc Bot Phase-G Field Deployment Package Packet](docs/proof_packets/ARC_BOT_PHASE_G_FIELD_DEPLOYMENT_PACKAGE_PACKET.md)
- [Arc Bot Phase-H Narrow Pilot Readiness Packet](docs/proof_packets/ARC_BOT_PHASE_H_NARROW_PILOT_READINESS_PACKET.md)
- [Arc Bot Phase-I MVP Completion Gate Packet](docs/proof_packets/ARC_BOT_PHASE_I_MVP_COMPLETION_GATE_PACKET.md)
- [Phase-0 Scope-Lock Contract Change Handoff Runbook](docs/runbooks/phase0_scope_lock_contract_change_handoff.md)
- Field support runbooks:
  - [Worker Offline](docs/runbooks/worker_offline.md)
  - [Model Not Reachable](docs/runbooks/model_not_reachable.md)
  - [Approval Queue Stuck](docs/runbooks/approval_queue_stuck.md)
  - [Evidence Packet Missing](docs/runbooks/evidence_packet_missing.md)
  - [Document Preview Failed](docs/runbooks/document_preview_failed.md)
- [Arc Bot Phase-1 Business Inventory Proof Packet](docs/proof_packets/ARC_BOT_PHASE1_BUSINESS_INVENTORY_PROOF_PACKET.md)
- [Arc Bot Phase-1 Business Inventory Migration Gate Packet](docs/proof_packets/ARC_BOT_PHASE1_BUSINESS_INVENTORY_MIGRATION_GATE_PACKET.md)
- [Arc Bot Phase-1 Business MVP Roadmap](docs/ROADMAP_PHASE1_BUSINESS_MVP.md)
- [Arc Bot Completion Roadmap](docs/ROADMAP_ARC_BOT_COMPLETION.md)
- [Arc Bot Runtime UI Scope Lock Punch List](docs/ROADMAP_SCOPE_LOCK_PUNCH_LIST.md)
- [Arc Bot Phase-0 Scope Lock Punch List](docs/ROADMAP_SCOPE_LOCK_PHASE0_PUNCH_LIST.md)
- [Arc Bot Phase-1 Readiness Handoff Punch List](docs/ROADMAP_PHASE1_HANDOFF_PUNCH_LIST.md)
- [Arc Bot Reconstruction Docs And Source Map](docs/audits/ARC_BOT_RECONSTRUCTION_DOCS_AND_SOURCE_MAP.md)
- [Arc Bot Phase-0 Roadmap](docs/ROADMAP.md)
- [LIMA Office / LIMA AI OS Contract Assumptions (Reviewed)](docs/LIMA_OFFICE_LIMA_AI_OS_CONTRACT_ASSUMPTIONS.md)
- Core architecture planning:
  - [ARCHITECTURE.md](ARCHITECTURE.md)
  - [MVP_SCOPE.md](MVP_SCOPE.md)
  - [CONTRACTS.md](CONTRACTS.md)
  - [SECURITY_MODEL.md](SECURITY_MODEL.md)
  - [THREAT_MODEL.md](THREAT_MODEL.md)
  - [WORKER_NODE_SPEC.md](WORKER_NODE_SPEC.md)
  - [SUPERVISOR_SPEC.md](SUPERVISOR_SPEC.md)
  - [AUTONOMY_BOUNDARIES.md](AUTONOMY_BOUNDARIES.md)
  - [DECISIONS.md](DECISIONS.md)
  - [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)

The operator-console foundation defines the first office-worker control-room surfaces and server-side state boundary. It is not a frontend, backend, persistence layer, worker runtime, connector, model router, scheduler, Guardian implementation, or LIMA runtime integration.

## Scope Lock Notes (Current)

- Phase-0 runtime UI scaffold is locked: preview/render-only pages, no live execution.
- Runtime authority is deferred to approved LIMA-Guardian-Suite / LIMA-Guardian Spine integration phases.
- The current shell scope remains documentation-first and fail-closed.
- Preview entrypoint (no execution): `python -m phase0_runtime_ui_scaffold.preview`.
- Phase-1 read-feed seam preview: `python -m phase0_runtime_ui_scaffold.read_feed`.
- Guardian Suite spine seam dry-run (fixture-backed): `python -m phase0_runtime_ui_scaffold.guardian_suite_seam`.
- Phase-1 runtime consumer preview (for downstream UI/runtime handoff): `python -m phase0_runtime_ui_scaffold.runtime_consumer`.
- Phase-2 runtime-control seam preview (downstream UI state handoff): `python -m phase0_runtime_ui_scaffold.phase2_runtime_control`.
- Phase-2 runtime-control consumer handoff preview (for downstream bounded UI control consumer): `python -m phase0_runtime_ui_scaffold.runtime_control_consumer`.
- Phase-2 runtime-control renderer preview (bounded UI controls, execution-disabled): `python -m phase0_runtime_ui_scaffold.runtime_control_renderer`.
- Phase-3 runtime-control execution planning preview (execution still blocked by default): `python -m phase0_runtime_ui_scaffold.runtime_control_execution`.
- Arc Guardian/Spine base preview (local-model PC shell, execution blocked): `python -m arc_guardian_spine.preview`.
- Arc intent envelope preview (future signed-request boundary, execution blocked): `python -m arc_guardian_spine.intent_envelope_preview`.
- Arc LIMA Office read adapter preview (RuntimeStateSnapshot-style metadata, execution blocked): `python -m phase6_lima_office_integration.read_adapter`.
- Arc Phase-D approval/evidence dependency preview (Lima Office answers recorded, runtime still blocked): `python -m phase7_approval_evidence.readiness`.
- Arc Phase-G field deployment package preview (read-only setup/runbook/smoke posture): `python -m phase10_field_deployment.package`.
- Arc Phase-H narrow pilot readiness preview (sanitized insurance-intake pilot planning): `python -m phase11_pilot_readiness.pilot`.
- Arc Phase-I MVP completion gate preview (completion-readiness, not MVP-complete): `python -m phase12_mvp_completion.completion`.
- Arc Guardian/Spine Phase-1 contract shape includes non-reusable approval requests, redacted evidence refs, and a projection-only local Spine ledger.
- Basic Guardian console preview projection: `python -m phase0_runtime_ui_scaffold.basic_console`.
- Phase-2 Ollama/Qwen local model readiness projection:
  `python -m phase2_local_model_readiness.readiness`.
  - Runtime target: Ollama.
  - Model family target: Qwen.
  - Default planning model tag: `qwen2.5:7b`.
  - Endpoint label: `http://127.0.0.1:11434`.
  - No Ollama API call, model invocation, socket probe, provider SDK, provider
    credential, or cloud fallback is used by the projection.
  - LIMA Office handoff packets can be consumed in-memory as read-only metadata
    through `build_ollama_qwen_readiness_from_lima_packet`; `degraded` remains
    setup-required, and blocked statuses remain blocked.
- Phase-3 document intake metadata preview:
  `python -m phase3_document_intake.intake`.
  - Supports PDF, text, image scan, and Word document metadata.
  - Validates document ID, source/upload ref, tenant, sensitivity, intake
    operator, and processing mode.
  - Does not read files, persist raw content, run OCR/parsers, call models, or
    mutate customer systems.
- Phase-4 document extraction preview:
  `python -m phase4_document_extraction.extraction`.
  - Returns deterministic filename metadata, classified file type, page-count
    placeholder, checksum placeholder, and operator-supplied document category.
  - Emits Guardian decision metadata, evidence refs, and a projection-only Spine
    event.
  - Provides an injectable local model preview provider interface, but the
    default provider is blocked and does not invoke any model.
  - Missing local model seat health, approval token, redaction policy, or output
    policy keeps model-assisted preview approval-required; even complete gate
    data does not grant runtime execution in Phase 4.
  - Does not read files, persist raw content, run OCR/parsers, use provider SDKs,
    call models, open network paths, call connectors, or mutate customer
    systems.
- Phase-5 office workflow templates:
  `python -m phase5_office_workflows.workflows`.
  - Defines intake note summary, insurance claim packet triage, policy document
    summary, missing information checklist, customer-service draft reply, and
    internal follow-up task draft workflows.
  - Defines Document Processing Bot, Customer Support Draft Bot, Billing Intake
    Assistant, and Compliance Review Assistant role profiles.
  - Each workflow has schema coverage, fixture coverage, proof tests, and a
    blocked-action matrix.
  - Outputs are draft previews only and remain pending operator review.
  - Saving final output, external sends, customer-record updates, form
    submissions, and connector writes require approval and remain blocked.
  - Does not read files, persist raw content, invoke models, use provider SDKs,
    call connectors, send messages, submit forms, or mutate customer systems.
- Phase-G field deployment package:
  `python -m phase10_field_deployment.package`.
  - Defines local worker PC setup docs, support runbooks, and read-only smoke
    commands for one Supervisor Server, 1-8 Arc workers, and a single tenant.
  - Production deployment remains disallowed.
  - Does not install/update software, start services, register workers, probe
    sockets, invoke models, call connectors, write durable evidence, or mutate
    customer systems.
- Phase-H narrow pilot readiness:
  `python -m phase11_pilot_readiness.pilot`.
  - Defines the first sanitized insurance-intake pilot package for insurance
    claim packet triage and missing-information checklist drafts.
  - Uses Phase-5 draft-preview workflow templates only.
  - Live pilot execution remains disallowed.
  - Does not process raw customer documents, invoke models, call connectors,
    send external messages, write durable evidence, or mutate customer systems.
- Phase-I MVP completion gate:
  `python -m phase12_mvp_completion.completion`.
  - Evaluates documented MVP completion criteria against current repo evidence.
  - Records five Lima Office external answers from
    `docs/interop/ARC_BOT_LIMA_OFFICE_EXTERNAL_ANSWERS.md`.
  - Reports the repo as not MVP-complete while remaining owner questions and
    runtime dependencies remain unresolved.
  - Does not grant runtime authority, invoke models, call connectors, write
    evidence, mutate customer systems, or claim production readiness.
- Basic Guardian console static UI: `ui/arc_bot_basic_console.html`.
  - Shows Local Model and LIMA Office connection indicators with connect buttons.
  - Includes file upload, office workflow templates, training notes,
    self-learning review mode, and chat panels.
  - Buttons and inputs create local preview/pending states only; no model call,
    LIMA Office connector action, file processing, training write, or memory write
    occurs from the static page.
- End-to-end phase-chain seam preview (preview -> runtime consumer -> control handoff -> control consumer): `python -m phase0_runtime_ui_scaffold.phase_chain`.
- Include guardian-suite seam summary in phase-chain preview: `python -m phase0_runtime_ui_scaffold.phase_chain --with-guardian-suite-seam`.
- Include phase-3 execution planning in phase-chain/status-snapshot preview:
  `python -m phase0_runtime_ui_scaffold.phase_chain --with-phase3-execution-projection`.
- Scope-lock automation check command: `./scripts/scope_lock_guardrails.ps1`.
- Scope-lock artifact refresh command (canonical fixture regeneration): `./scripts/refresh_scope_lock_artifacts.ps1`.
- Combined phase-0 + phase-1 guardrail command: `./scripts/phase0_phase1_handoff_guardrails.ps1`.
- Phase-1 readiness handoff check command: `./scripts/phase1_handoff_guardrails.ps1`.
- Phase-2/3 runtime-control handoff guardrail command: `./scripts/phase2_handoff_guardrails.ps1`.
- Arc worker read-only smoke command: `./scripts/arc_worker_smoke.ps1`.
- Emit read-only Phase-1 business inventory preview: `python -m phase1_business_shell_inventory.inventory`.
- Emit read-only Phase-1 client configuration preview: `python -m phase1_client_configuration.configuration`.
- Emit Phase-1 runtime authority gating projection: `python -m phase1_runtime_authority_gating.gating`.
- Emit read-only Phase-1 business/runtime alignment projection: `python -m phase1_business_shell_inventory.runtime_alignment`.
- Emit read-only Phase-1 readiness bundle: `python -m phase1_readiness.bundle`.
- Emit deterministic phase-lock projection pack (chain/status snapshot + phase-2/3 control projections + readiness handoff artifacts): `python scripts/emit_arc_bot_artifacts.py --fixtures-dir tests/fixtures --compact`.
- Emit projection pack via PowerShell helper (same as above): `./scripts/emit_arc_bot_artifacts.ps1`.
- Emit canonical scope-lock status snapshot artifact: `python -m phase0_runtime_ui_scaffold.phase_chain --emit-status-snapshot --with-guardian-suite-seam`.
- Emit and write canonical snapshot artifact: `python -m phase0_runtime_ui_scaffold.phase_chain --emit-status-snapshot --with-guardian-suite-seam --status-snapshot-path tests/fixtures/arc_bot_runtime_ui_scaffold_phase0_scope_lock_status_snapshot.json --compact`.
- Scope-lock status snapshot fixture assertion: `python -m pytest -q tests/test_arc_bot_runtime_ui_scaffold_phase_chain.py::test_phase_chain_scope_lock_status_snapshot_matches_fixture`.
- Reproducible local check: `python -m pytest -p no:cacheprovider --basetemp tmp_pytest -q tests/test_arc_bot_runtime_ui_scaffold_phase_chain.py tests/test_arc_bot_runtime_ui_scaffold_guardian_suite_seam.py tests/test_arc_bot_phase0_scope_lock_runtime_ui.py tests/test_arc_bot_runtime_ui_scaffold_contracts.py`.
- CI guardrail workflow: `.github/workflows/guardrails.yml` (runs scope-lock, phase-1, and phase-2/3 handoff suites on push/PR).

## Reference Context (For Next Phase)

- Sparkbot: `https://github.com/armpit-symphony/Sparkbot`
- Sparkbot_shell: `https://github.com/armpit-symphony/Sparkbot_shell`
- LIMA-Guardian-Suite: `https://github.com/armpit-symphony/LIMA-Guardian-Suite`
- LIMA AI Office operator/docs and contracts remain the source for downstream state schemas.

## Development Principles

- Strict by default
- Task-oriented by default
- Approval/audit/evidence first
- Business workflow focused
- Client-customizable without exposing internals
- Local-first or local-node friendly
- No broad Sparkbot-style workstation behavior by default
- No unrestricted shell/browser/file/network control by default
- No robotics/IoT hardware control by default
- No surprise cloud dependency
- No hidden autonomy
- No execution, dispatch, persistence, or mutation without explicit approved wiring

## Suggested Tagline Options

- "Guarded worker bots for real business tasks."
- "Preview the work. Approve the action. Keep the evidence."
- "Role-specific AI workers for LIMA Office."
- "Strict business automation shells for local-first deployments."

## Next Steps Checklist

- [x] Confirm Arc Bot product boundary
- [x] Decide repo visibility and license/distribution model
- [x] Define first target business role
- [x] Define task status and risk labels
- [x] Define approval posture labels
- [x] Define evidence panel requirements
- [x] Define connector readiness states
- [x] Define client configuration schema
- [x] Define bot role/persona template schema
- [x] Create shell wireframes
- [x] Create no-execution skeleton plan
- [x] Prepare first business MVP roadmap
- [x] Review LIMA Office/LIMA AI OS contract assumptions
