# Arc Bot Reconstruction Docs And Source Map

Date: 2026-06-07

Branch: `audit-arc-bot-reconstruction-docs-source-map`

Scope: documentation/source-first reconstruction audit only. No product code, UI implementation, execution path, runtime action, persistence adapter, connector, scheduler, model call, terminal/process path, browser automation path, or secrets path was added.

## 1. Repo Status

### Arc-Bot-shell

- Repo: `armpit-symphony/Arc-Bot-shell`
- Local path: `C:\Users\limap\Arc-Bot-shell`
- Starting branch and commit inspected: `roadmap-arc-bot-shell-business-worker` at `bc6ce59`
- Audit branch created: `audit-arc-bot-reconstruction-docs-source-map`
- Pre-audit working tree: clean
- Current repo content before this audit: `README.md` only
- Remote: `https://github.com/armpit-symphony/Arc-Bot-shell.git`

### LIMA-AI-OS

- Repo: local `C:\Users\limap\LIMA-AI-OS`
- Branch: `design-lima-discovery-adapter-interface`
- Commit: `3a6b8a3`
- Working tree: clean
- Role in this audit: LIMA Runtime / kernel contract source and Arc Bot consumer-boundary reference.

### LIMA Office

- Repo: local `C:\Users\limap\Lima-Office`
- Branch: `phase-1c-closeout-status-archive`
- Commit: `d84a682`
- Working tree: clean
- Remote: `https://github.com/armpit-symphony/Lima-Office.git`
- Role in this audit: closest office-worker control-plane source for Supervisor Server, Arc worker, task, approval, evidence, console, connector-readiness, and model-routing contracts.

### LIMA IT

- Repo: local `C:\Users\limap\LIMA--IT`
- Branch: `audit-phase-7-3-mock-simulator-validation-matrix-hardening`
- Commit: `f38f5a3`
- Working tree: clean
- Role in this audit: related IT/remediation posture reference only. No LIMA IT source was selected for Arc Bot porting.

### Sparkbot

- Repo: local `C:\Users\limap\Sparkbot`
- Branch: `public-release-final-cleanup-assessment`
- Commit: `0f8d059`
- Working tree: dirty due to unrelated untracked files:
  - `scripts/file_v1_6_72_proposals.py`
  - `scripts/file_v1_6_75_proposals.py`
- Remote: `git@github-armpit:armpit-symphony/Sparkbot.git`
- Role in this audit: public/self-hosted workstation reference and lessons learned only. It is not Arc Bot source of truth.

### Sparkbot_shell

- Repo: local `C:\Users\limap\Sparkbot_shell`
- Branch: `mock-lima-contract-vocabulary-alignment`
- Commit: `9c26c6d`
- Working tree: clean
- Remote: `https://github.com/armpit-symphony/Sparkbot_shell.git`
- Role in this audit: static public shell rebuild reference and UX vocabulary only. It is not Arc Bot source of truth.

### Missing Or Inaccessible References

- No separate local Arc Bot R&D repo was found beyond `Arc-Bot-shell`.
- The available LIMA Office repo is `Lima-Office`; no separate local checkout named exactly `LIMA-OFFICE` was found.
- `rg` encountered access-denied cache/runtime folders under unrelated local paths, but the required repos above were readable.
- GitHub network discovery was not used for additional repo hunting in this docs-only branch.

## 2. Source-Of-Truth Map

### Current Working Arc Bot Behavior

There is no implemented Arc Bot product behavior in `Arc-Bot-shell` today. The repo is a roadmap/staging repo with one `README.md`. That README defines the desired product boundary:

- guarded business worker-bot shell
- task inbox
- task runner panel
- approval queue
- connector status
- evidence panel
- client config
- bot role/persona template
- no execution, dispatch, persistence, approval enforcement, or mutation without future approved contracts

The current Arc-Bot-shell source of truth is therefore product doctrine and scope, not code.

### Behavior Defined In Related Sources

| Source | Files inspected | What it defines | Audit finding |
| --- | --- | --- | --- |
| Arc-Bot-shell | `README.md` | Arc Bot product boundary and planned shell surfaces | Keep as product doctrine. No code exists to port. |
| LIMA Office | `docs/MVP_SCOPE.md`, `docs/ux/OPERATOR_CONSOLE_SPEC.md`, `docs/ux/OPERATOR_WORKFLOWS.md`, `contracts/v1/*.schema.json`, `lima_office/supervisor/*`, `lima_office/guardian/*`, `lima_office/evidence/*`, `lima_office/runtime/model_routing.py` | Small-business Supervisor/Arc worker control plane, console views, tasks, approvals, evidence, worker state, connector readiness, model routing posture | Strongest office-worker source. It is still mock/in-memory and contract-first. |
| LIMA-AI-OS | `lima/contracts/*`, `lima/kernel/candidate_preview.py`, `lima/kernel/runtime_state.py`, `lima/adapters/sparkbot_humaninput.py`, `lima/guardian/*_fakes.py`, Phase 40-48 docs | LIMA Runtime contracts, non-authoritative preview, non-production adapter/fake pipeline, Arc Bot planning vocabulary | Use only as contract vocabulary and future seam. Do not assume runtime services. |
| Sparkbot | `backend/app/api/routes/chat/*`, `backend/app/services/guardian/*`, `frontend/src/pages/WorkstationPage.tsx`, `frontend/src/components/CommandCenter/*`, `frontend/src/lib/workstationMeeting.ts` | Mature public workstation behavior: chat, Workstation, Command Center, terminal, model setup, memory, approvals, Task Guardian, connectors | Reference only. Do not clone Arc Bot from Sparkbot. High-risk localStorage/sessionStorage and broad workstation behavior must not become Arc defaults. |
| Sparkbot_shell | `src/components/*`, `src/data/demo*.ts`, `docs/*` | Static public shell demo: Workstation, Command Center, Task Guardian, model seats, memory/context preview, connectors | Lessons and vocabulary only. It is demo React state, not server truth. |

### Real Operator Workflow Versus Placeholder Shell UI

Real operator workflow is best represented by LIMA Office docs/contracts:

- `docs/ux/OPERATOR_CONSOLE_SPEC.md`
- `docs/ux/OPERATOR_WORKFLOWS.md`
- `contracts/v1/console.view.schema.json`
- `contracts/v1/console.action.schema.json`
- `contracts/v1/console.alert.schema.json`
- `contracts/v1/task.execution.schema.json`
- `contracts/v1/worker.lifecycle.schema.json`
- `contracts/v1/worker.heartbeat.schema.json`
- `contracts/v1/guardian.decision.schema.json`
- approval, evidence, connector, model-route, LIMA IT, and attestation schemas

Placeholder or static shell UI is represented by Sparkbot_shell:

- `src/App.tsx`
- `src/components/WorkstationShell.tsx`
- `src/components/TaskGuardianPreview.tsx`
- `src/components/ModelConfigShell.tsx`
- `src/data/demoShellState.ts`
- `src/data/demoTaskGuardianState.ts`
- docs repeatedly stating no backend, no persistence, no provider calls, no LIMA wiring, and no execution

Sparkbot proper contains real R&D workstation behavior, but it is a personal/workstation product surface. For Arc Bot, it should inform risk lessons and vocabulary only.

### What Should Be Ported Directly

- Arc-Bot-shell README product boundaries and no-execution posture.
- LIMA Office operator-console information architecture, workflow list, and contract names as requirements.
- LIMA Office task/worker/evidence/Guardian/model-route schema fields as source requirements, not necessarily the exact implementation.
- LIMA AI OS `ShellManifest`, `HumanInput`, `IntentEnvelope`, `GuardianDecision`, `ApprovalMetadata`, `SpineEvent`, `StorageProtocol`, and tool-pack vocabulary as future integration contract shapes.
- LIMA AI OS `candidate_preview` invariants as acceptance language for preview-only Arc Bot behavior.

### What Should Be Rebuilt From Behavior

- Arc Bot operator console UI should be rebuilt for the Arc office-worker mental model, using LIMA Office contracts as server truth.
- Chat/workflow state should be rebuilt as a task-oriented office-worker flow, not as a Sparkbot personal Workstation clone.
- Model/provider setup should be rebuilt as provider/model routing posture and local model readiness, not as client-side seat cards only.
- Memory/context should be rebuilt behind tenant, worker, redaction, evidence, and Guardian boundaries.
- Task Guardian-style health checks should be rebuilt as LIMA Office health/task/evidence workflows, not copied as public demo panels.
- Sparkbot Workstation and Command Center concepts can inspire operator ergonomics, but the implementation must be Arc-specific and fail closed.

### What Should Remain Private/Internal Only

- Sparkbot Guardian/Vault internals.
- Private token, PIN, CLI session, local auth, or subscription bridges.
- Browser automation, terminal, shell command, subprocess, MCP execution, and robotics paths.
- Connector token handling, webhook secrets, external send paths, OAuth/provider setup internals.
- Sparkbot public rebuild release/readiness docs except as lessons learned.
- Any proprietary LIMA Office, Guardian, Vault, or LIMA IT internals not exposed through contracts.

## 3. LIMA AI OS Reality Check

### Callable Or Importable Today

LIMA AI OS currently provides importable Python contract and helper surfaces:

- `lima.contracts.intent`: `HumanInput`, `IntentEnvelope`, `IntentCompilerProtocol`, risk/status/source enums.
- `lima.contracts.guardian`: `ConsequentialActionRequest`, `GuardianDecision`, `GuardianProtocol`, action/risk/status enums.
- `lima.contracts.approval`: `ApprovalMetadata`, `ApprovalScope`, `ApprovalProtocol`.
- `lima.contracts.harness`: `ModelRequest`, `ModelResponse`, `HarnessProtocol`.
- `lima.contracts.shell`: `ShellManifest`, `ShellProtocol`.
- `lima.contracts.storage`: `StorageProtocol`.
- `lima.contracts.spine`: `SpineEvent`, `TaskRecord`, `SpineProtocol`.
- Additional contracts for policy, tool packs, privacy/redaction, events, driver, auth, readiness, vault, adapters, boundary, and drift.
- `lima.kernel.candidate_preview.preview_candidate`: deterministic, read-only, local-only, non-authoritative candidate preview.
- `lima.kernel.runtime_state.inspect_runtime_state`: read-only advisory snapshot for caller-provided candidate state.
- `lima.adapters.sparkbot_humaninput.SparkbotHumanInputAdapter`: non-production neutral payload conversion to `HumanInput`.
- `lima.guardian.*_fakes`: fake in-memory policy, Guardian decision, approval, Spine, and fake pipeline classes for tests.

### Docs, Contracts, Fixtures, Or Tests Only

- Arc Bot / LIMA Office consumer vocabulary in Phase 40-41 docs and fixtures.
- Universal consumer and embodiment taxonomy in Phase 42 docs.
- Typed bridge and future implementation-gate docs in Phase 44-48.
- Sparkbot-shaped payload fixtures and regression harnesses.
- `tests/fixtures/*` payloads, product-family data, kernel-pipeline fixtures, and static test plans.
- Tool-pack scoping/risk policy docs and Sparkbot inventory docs.

### Not Implemented Yet

Do not assume LIMA AI OS currently provides:

- live chat
- durable memory
- task routing
- worker execution
- Guardian policy enforcement for production actions
- provider/model calls
- tool execution
- persistence/storage implementation
- approval runtime
- connector access
- file/network/browser mutation
- terminal/process execution
- robotics/device execution
- live shell adapter wiring
- audit storage
- background workers, queues, schedulers, or daemons

The only implemented runtime-like LIMA helper found is non-authoritative preview/state inspection that explicitly keeps execution, side effects, approval, dispatch, persistence, adapters, external calls, robotics, and physical-world behavior disabled.

### Clean Future Integration Seams

Arc-Bot-shell should eventually integrate into LIMA AI OS through these seams:

1. Shell identity: Arc Bot declares a `ShellManifest` with allowed and denied tool packs.
2. Intake: operator/task input becomes `HumanInput` and then `IntentEnvelope` through an approved adapter/compiler.
3. Candidate preview: Arc Bot can render LIMA `candidate_preview`-shaped metadata while staying non-authoritative.
4. Guardian gate: every consequential request must become `ConsequentialActionRequest` and require `GuardianDecision`.
5. Approvals: approval inbox state maps to `ApprovalMetadata` and LIMA Office approval-token contracts.
6. Spine/evidence: every task, decision, approval, and result must carry lineage refs and sanitized evidence refs.
7. Storage: Arc Bot server persists state through a future `StorageProtocol` implementation, never frontend storage as truth.
8. LIMA Office supervisor: Arc worker registration, heartbeat, task assignment, and status should align with LIMA Office contracts.

## 4. Arc Bot Operator Surface Search

Search terms used included: Command Center, Workstation, Control Center, Shell, Arc Bot shell, Agent console, Worker console, Spine, Dashboard, Task Guardian, HumanInput, LIMA, memory/context, approvals, routing, provider/model setup, job/worker state.

Findings:

- Arc-Bot-shell has only README-level shell surface names: Task Inbox, Task Runner Panel, Approval Queue, Connector Status, Evidence Panel, Client Config, Bot Role / Persona Template.
- LIMA Office has the strongest real operator-console definition: Overview, Workers, Tasks, Approvals, Guardian, Evidence, Incidents, LIMA IT, Deployment, Governance, Connectors, Audit / Exit, Runbooks.
- LIMA Office operator workflows define concrete screens, roles, required contracts, allowed metadata actions, blocked runtime actions, Guardian/policy/evidence requirements, and runbook links.
- Sparkbot has a mature Workstation and Command Center with chat, model stack, Task Guardian, memory, approvals, terminals, connectors, and dashboard routes. It is too broad and too personal-workstation-shaped to port directly into Arc Bot.
- Sparkbot_shell has static Workstation/Command Center/Task Guardian/connector/model-seat UI and docs, but it is explicitly static, demo-state only, and not wired to backend/runtime/LIMA.
- LIMA AI OS docs mention Arc Bot as a guarded office-task consumer, but they do not implement Arc Bot.

Source-of-truth conclusion: Arc Bot product-readiness should start from Arc-Bot-shell doctrine plus LIMA Office operator-console/task/worker/evidence/approval contracts. Sparkbot and Sparkbot_shell can only provide lessons and UX vocabulary.

## 5. Shared State Requirements

The following must persist server-side for Arc Bot product readiness:

- chat/workflow state
- task intake, classification, status, blocked reasons, draft outputs, and result summaries
- agent/worker configuration, role, tool-pack scope, allowed model routes, kill switch, expiration, and review status
- Arc worker registration, heartbeat, lifecycle, deployment, quarantine, revoke, and handoff state
- task/job assignment, approval need, evidence refs, retry/timeout posture, and worker status
- memory/context facts, notes, summaries, retrieval metadata, source confidence, redaction class, retention class, and tenant boundary
- notes/history, meeting/workflow notes, customer-service drafts, and operator annotations
- provider/model routing posture, local model availability, fallback posture, route denial/degradation reason codes
- Guardian decisions, approval requests/results/tokens, replay/expiry/binding metadata, and breakglass posture
- events/logs, audit/evidence lineage, evidence artifacts/failures, and redacted summaries
- dashboard/status views, alerts, incident state, connector readiness, health status, and governance posture
- shell/worker handoff records between operator console, Supervisor Server, and Arc workers

### LocalStorage Or SessionStorage Findings

- Arc-Bot-shell has no UI code and no browser storage.
- Sparkbot_shell `src` did not show `localStorage`, `sessionStorage`, `IndexedDB`, or `document.cookie`; it uses React state and fixture data only.
- Sparkbot proper does use browser storage in several places:
  - terminal session IDs in `frontend/src/hooks/useTerminalSession.ts`
  - Workstation specialty assignments in `frontend/src/pages/WorkstationPage.tsx`
  - auth/session tokens in `frontend/src/hooks/useAuth.ts`, `frontend/src/main.tsx`, and related route/layout files
  - room selection, voice mode, meeting drafts, and task-meeting links in chat/workstation files

Arc Bot must not treat those Sparkbot browser-storage patterns as product source of truth. At most, frontend storage can hold transient UI preferences. Product state belongs server-side behind Guardian, evidence, tenant, worker, and approval contracts.

## 6. Safety And Private Exclusions

Fail closed by default for:

- file mutation
- terminal/process execution
- browser automation
- device/robotics control
- connector writes
- external sends
- scheduler/background execution
- local CLI auth/session bridges
- token bridges
- private Guardian/Vault internals

This branch added no execution paths. Future branches must not add these paths until Guardian/action boundaries, approval flow, evidence, and threat model are approved.

## 7. Secrets Policy

Arc-Bot-shell should not store runtime secrets inside the repo tree by default.

Recommended future default:

- Use `$XDG_DATA_HOME/arc-bot-shell/...` when `XDG_DATA_HOME` is set.
- Otherwise use `~/.local/share/arc-bot-shell/...`.

Recommended override:

- `ARC_BOT_SECRETS_DIR`

Additional rules:

- Store raw secrets only through a future approved Vault/secrets provider.
- Repo files should contain docs, schemas, fixtures, and non-secret config only.
- Do not log prompts, outputs, headers, request bodies, response bodies, tokens, cookies, provider keys, connector secrets, or Vault material.

## 8. Recommended Next Implementation Branch

Recommended next branch:

`port-arc-bot-operator-console-foundation`

Reason: the source map supports an operator-console foundation branch only if it is built from LIMA Office operator-console/task/worker/approval/evidence contracts and Arc-Bot-shell product boundaries. It must not copy Sparkbot Workstation as product code and must not add runtime execution.

Allowed first scope for that branch should be:

- document exact operator-console information architecture for Arc Bot Shell
- define server-side state contracts or adapters against LIMA Office schemas
- create static or contract-bound UI only if explicitly approved
- keep all actions display-only or metadata-only
- prove no localStorage source-of-truth, no secrets, no runtime actions

## 9. Do-Not-Do List

- Do not create a clean shell and call it a product.
- Do not strip working R&D behavior without mapping it first.
- Do not replace existing command/console flows with generic setup screens.
- Do not keep important product state only in frontend localStorage.
- Do not log prompts, outputs, headers, request bodies, response bodies, or secrets.
- Do not store secrets inside the repo tree.
- Do not add subprocess/CLI/session auth casually.
- Do not build automation before Guardian/action boundaries are ready.
- Do not use "runtime" as the product identity where the operator mental model is Workstation, Shell, Console, or Office Worker.
- Do not copy Sparkbot terminal/browser/file/network behavior into Arc Bot.
- Do not import private Guardian/Vault internals into Arc Bot Shell.
- Do not wire providers, local models, connectors, schedulers, or workers without contract and threat-model approval.

## Validation Evidence

Commands and inspections performed:

- `git status --short --branch` for Arc-Bot-shell, LIMA-AI-OS, Lima-Office, LIMA--IT, Sparkbot, and Sparkbot_shell.
- `git rev-parse --short HEAD` for the same inspected repos.
- `rg --files` across Arc-Bot-shell, LIMA-AI-OS, Lima-Office, Sparkbot_shell, and targeted Sparkbot paths.
- Operator-surface `rg -n` searches for Command Center, Workstation, Control Center, Shell, Agent console, Worker console, Spine, Dashboard, Task Guardian, HumanInput, LIMA, memory/context, approvals, routing, provider/model setup, and job/worker state.
- Targeted browser-storage scan for `localStorage`, `sessionStorage`, `IndexedDB`, and `document.cookie`.
- Source reads for:
  - Arc-Bot-shell `README.md`
  - LIMA-AI-OS `README.md`, contracts, `candidate_preview.py`, `runtime_state.py`, `sparkbot_humaninput.py`, Guardian fakes, and Phase 40-48 docs
  - Lima-Office `README.md`, `STATUS.md`, `docs/MVP_SCOPE.md`, `docs/ux/OPERATOR_CONSOLE_SPEC.md`, `docs/ux/OPERATOR_WORKFLOWS.md`, task/console contracts, task queue, worker registry, Guardian decision helper, evidence writer, and model-routing posture classifier
  - Sparkbot_shell static UI/data/docs
  - Sparkbot targeted route/component/service paths and local browser-storage matches

Changed files in this branch:

- `docs/audits/ARC_BOT_RECONSTRUCTION_DOCS_AND_SOURCE_MAP.md`

Validation expectations before commit:

- `git status --short --branch`
- `git diff --check`

Safety confirmation:

- No product code implementation.
- No secrets added.
- No runtime/action execution added.
- No connector, scheduler, browser, terminal, process, model provider, worker daemon, or persistence adapter added.
