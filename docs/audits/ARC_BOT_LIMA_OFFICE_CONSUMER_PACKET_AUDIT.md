# Arc Bot / LIMA Office Consumer Packet Audit

Date: 2026-06-12

Branch: `proof-arc-bot-shell-lima-office-consumer-packet`

## Executive summary

Arc-Bot-shell is currently **not ready for live LIMA Runtime consumption**. It is a proof-oriented, documentation-first shell that defines interfaces, postures, and blocked action boundaries. The repo provides enough design evidence for LIMA API freeze context, but does not provide production-ready runtime adapters or execution authority yet.

Current status from evidence artifacts:
- `docs`-centric and non-runnable shell design posture.
- No runtime routes, no worker dispatch, no persistence, no connector bridge, no model calls, no file/network/browser/device side effects.
- Existing artifacts strongly indicate Arc-owned approval and governance posture with LIMA seams marked future-only.

## Question 1: Is Arc-Bot-shell ready to consume LIMA Runtime today?

Short answer: **No** for live consumption.

- Static readiness proof exists.
- Runtime-safe behavior is **not implemented**.
- LIMA import/wiring in product code is explicitly absent.
- No proven ingestion to `HumanInput`/`IntentEnvelope`/`CandidatePreview`/`RuntimeStateSnapshot` runtime path.

Therefore:
- **Static readyness for API framing:** Yes
- **Live runtime consumption:** No

## Question 2: If not, what exactly is missing?

### Critical missing readiness for integration
1. `ConsumerRequest` intake implementation with tenant/session validation.
2. `HumanInput` adapter and normalization step.
3. Typed intent compilation (`TypedIntentEnvelope`/`TaskIntent`) with constrained action set.
4. `CandidatePreview` runtime producer with deterministic status model constrained to:
   - `preview_only`, `explain_plan`, `blocked`, `deferred`
5. `RuntimeStateSnapshot` ingestion from Supervisor / control-plane source.
6. `GuardianDecision` enforcement point for consequential requests.
7. `ApprovalMetadata` and replay/token binding for operator-confirmed high-risk tasks.
8. `SpineEvent`/audit emission with evidence lineage.
9. Persistent server-side state boundary (no frontend source of truth).
10. Trust model validation for role, session, device identity.

### Missing operational capabilities
- No queueing, scheduling, or worker dispatch.
- No connector operations (no read/write).
- No model/provider routing.
- No evidence persistence and no audit ledger writes.
- No diagnostics execution path.
- No run-time health collector or probe actor.

## Question 3: What product-shell requirements should influence LIMA API freeze?

LIMA API freeze should preserve these mandatory Arc-shell boundaries:

1. **No implicit authority in previews**
   - preview outputs cannot become execution artifacts by default.
2. **Strictly typed intent and tool-pack posture**
   - allowed action set must be explicit and tenant-scoped.
3. **Guardian-first execution**
   - every consequential action requires `GuardianDecision` + operator proof artifacts.
4. **Evidence-first observability**
   - all decision and preview paths must carry evidence + audit references.
5. **Blocked/fail-closed defaults**
   - if required contract fields are missing, LIMA-facing actions must fail blocked.
6. **Small-business single tenant/session assumptions**
   - one customer context at a time, and explicit role-based isolation.
7. **Source-of-truth clarity**
   - server-side state only; no frontend local source of truth.
8. **Runtime action whitelist**
   - connector actions, sends, writes, commands, tool invocations must be denied unless the LIMA boundary contract explicitly enables.

## Question 4: What must be proven by Sparkbot before Arc Bot should integrate?

Sparkbot should prove:

- `readiness` posture:
  - `HumanInput`/intent compiler behavior is testable and safe.
  - no side-effect leaks in preview paths.
- `operations` posture:
- no hidden autonomy, explicit action surfaces, and consistent blocked reasons.
- `evidence` posture:
  - stable evidence and audit IDs are emitted end-to-end.
  - redaction and tenant scoping are enforced.
- `governance` posture:
- approval token/expiry/replay and separation-of-duty are enforceable without shell overrides.
- `integration` posture:
  - candidate preview and snapshot read contracts can be used in bounded office workflows.
- `security` posture:
  - no provider secrets or secrets-of-file-system actions in shell layer.
  - no terminal/automation/browser/device side-effect paths in shell product layer.

These proofs should be independently repeatable and version-anchored before Arc integration milestones.

## Question 5: What should remain Arc-shell-owned vs LIMA-owned?

### Arc-shell-owned (phase-appropriate)
- Shell role definitions and small-business task surface naming.
- Operator approval UX behavior and operator-runbook guidance.
- Office context framing, worker persona intent, and intake taxonomy.
- Local blocked/blocked guidance language for unsupported surfaces.
- Product-safe default posture and user-facing decision workflow.

### LIMA-owned (future shared seam)
- Typed runtime contracts (`HumanInput`, intent, candidate preview envelopes).
- Guardian runtime decision protocol and enforcement semantics.
- Runtime event and evidence spine contracts.
- Runtime snapshot contract shape and freshness rules.
- Tool-pack capability registry and policy mapping at kernel/seam level.
- Runtime audit export and evidence durability semantics.

## Question 6: What are the top blockers before LIMA Office / Arc Bot integration?

1. Missing runtime ingestion/adapters for `ConsumerRequest -> HumanInput -> Intent`.
2. Missing implementation for constrained `CandidatePreview` producer (currently static).
3. No durable server-side state and no audit/evidence persistence.
4. No proven non-execution health + diagnostics read loop.
5. No hardened connector model and no safe connector token policy bridge.
6. Missing explicit operator confirmation + Guardian enforcement chain for consequential actions.
7. No tested role/session/device trust assertions in shell path.
8. No validated status whitelist enforcement in live pipeline.

## Question 7: What are the minimum future acceptance tests for office-worker flows?

### Minimum acceptance criteria
1. **Static proof continuity**
   - proof packet and audit artifacts remain passively present and consistent.
2. **Intake test**
   - one office request yields normalized `ConsumerRequest` with tenant/operator/session fields.
3. **Intent test**
   - request maps to typed intent with strict action whitelist.
4. **Preview test**
   - every preview response status is one of:
   - `preview_only`, `explain_plan`, `blocked`, `deferred`.
5. **Candidate test**
   - every `CandidatePreview` includes `embodiment_profile`.
6. **Guardrail test**
   - blocked execution channel must never generate `execution_authority=true`.
7. **Evidence test**
   - each blocked/explain path contains `evidence_ref`, `audit_ref`, and `guardian_ref` when applicable.
8. **Snapshot test**
   - health and workflow snapshots are read-only and do not mutate external state.
9. **Operator approval test**
   - no action can move from preview/explain to execution without explicit approval binding and Guardian decision.
10. **State trust test**
   - cross-tenant state access is rejected and test failures produce blocked paths.

## Final readiness verdict

- **Arc-Bot-shell can inform LIMA API freeze with evidence-oriented requirements and safe boundary assumptions.**
- **Arc-Bot-shell cannot yet consume LIMA Runtime for live office-worker automation.**
- Next safe step: implement a static-to-runtime adapter shim contract test bench (read-only) that proves the four-stage boundary flow above, without adding any execution path.