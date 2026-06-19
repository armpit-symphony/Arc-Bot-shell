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

## Repo Status

This repo is currently a roadmap/staging repo for the Arc Bot business worker-bot shell. It should remain documentation-only until the shell boundaries, client-safe configuration model, and LIMA Office/LIMA AI OS integration contracts are approved.

## Current Foundation Docs

- [Arc Bot Operator Console Foundation](docs/OPERATOR_CONSOLE_FOUNDATION.md)
- [Arc Bot Operator Console State Contract](docs/contracts/ARC_BOT_OPERATOR_CONSOLE_STATE.md)
- [Arc Bot Runtime UI Schemas](docs/contracts/schemas/arc_bot_console_state_envelope.schema.json)
  - [work queue snapshot schema](docs/contracts/schemas/arc_bot_work_queue_state.schema.json)
  - [runtime settings snapshot schema](docs/contracts/schemas/arc_bot_runtime_settings_state.schema.json)
  - [overview snapshot schema](docs/contracts/schemas/arc_bot_overview_state.schema.json)
- [Arc Bot Runtime UI Scaffold Contract Pack](tests/fixtures/arc_bot_runtime_ui_scaffold_contract_pack.json)
- [Arc Bot Runtime UI Scaffold Adapter Proof Packet](docs/proof_packets/ARC_BOT_RUNTIME_UI_SCAFFOLD_PHASE0_ADAPTER_PROOF_PACKET.md)
- [Arc Bot Runtime UI Scaffold Guardian Suite Seam Proof Packet](docs/proof_packets/ARC_BOT_RUNTIME_UI_SCAFFOLD_PHASE0_GUARDIAN_SUITE_SEAM_PROOF_PACKET.md)
- [Arc Bot Runtime UI Scope Lock Punch List](docs/ROADMAP_SCOPE_LOCK_PUNCH_LIST.md)
- [Arc Bot Reconstruction Docs And Source Map](docs/audits/ARC_BOT_RECONSTRUCTION_DOCS_AND_SOURCE_MAP.md)
- [Arc Bot Phase-0 Roadmap](docs/ROADMAP.md)
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
- End-to-end phase-chain seam preview (preview -> runtime consumer -> control handoff -> control consumer): `python -m phase0_runtime_ui_scaffold.phase_chain`.
- Include guardian-suite seam summary in phase-chain preview: `python -m phase0_runtime_ui_scaffold.phase_chain --with-guardian-suite-seam`.

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

- [ ] Confirm Arc Bot product boundary
- [ ] Decide repo visibility and license/distribution model
- [ ] Define first target business role
- [ ] Define task status and risk labels
- [ ] Define approval posture labels
- [ ] Define evidence panel requirements
- [ ] Define connector readiness states
- [ ] Define client configuration schema
- [ ] Define bot role/persona template schema
- [ ] Create shell wireframes
- [ ] Create no-execution skeleton plan
- [ ] Review LIMA Office/LIMA AI OS contract assumptions
- [ ] Prepare first business MVP roadmap
