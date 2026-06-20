# Arc Bot Shell Security Model

Date: 2026-06-18
Status: Phase-0 draft

## Core Security Principle

All high-risk actions are blocked by design in this branch. Preview UI artifacts are governance surfaces only.

## Controls (Phase-0)

- **No execution authority**
  - No tool execution.
  - No connector writes.
  - No provider/model routing.
  - No local model invocation.
  - No file mutation.

- **Evidence and policy requirements**
  - `policy_refs` and `evidence_refs` are required in guarded outputs.
  - Missing references result in blocked/review posture.

- **Read-only seams**
  - Projection inputs and outputs are immutable data transforms.
  - `runtime_authority_blocked: true` and `runtime_execution_blocked: true` enforced across seams.

- **Failure posture**
  - Validation failures are explicit, non-silenced, and return fail-closed shapes.

## Attack Surface Reduction

- No credentials are stored in repo/project state.
- Client configuration fixtures may contain only placeholder metadata and must not contain provider tokens, API keys, OAuth client secrets, refresh tokens, or credential values.
- No hidden background actions.
- No external I/O in phase-0 scaffold modules.
- Arc Guardian/Spine base is projection-only and does not import Sparkbot or LIMA-Guardian-Suite runtime modules.
- Strict gate checks on all projection transitions.

## Future Security Additions (not active now)

- Token-bound approval lane (`approval.token` and Guardian binding).
- Signed envelope handoff and audit chain.
- Local model seat health proof and raw document redaction policy.
- Runtime route mutation requiring explicit policy/risk adjudication.
