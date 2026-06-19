# Arc Bot Shell MVP Scope (Phase-0)

Date: 2026-06-18
Status: Foundation + contracts

## In Scope

- Operator console planning and documentation for priority surfaces.
- Work Queue, Runtime Settings, and Overview preview surfaces.
- Read-only projection pipeline:
  - adapter payloads -> phase-1 read-feed -> consumer -> control seams.
- Immutable proof packet chain for auditability.
- Deterministic fail-closed behavior for missing policy/evidence/runtime metadata.

## Out of Scope (Phase-0)

- Runtime execution and worker dispatch.
- Live provider/model inference.
- Connector writes and live connector read side effects.
- Storage mutations and hidden background actions.
- Secret capture or secret-backed runtime behavior.

## Exit Criteria for MVP phase

- Surface-level state remains display-only and explicitly bounded by contracts.
- All preview and handoff payloads include blocked runtime actions and required references.
- Guardian/approval systems are present as display inputs only.
- A documented migration plan exists for future execution activation.

## Minimal Product Definition

Arc Bot Shell in MVP foundation is a **governed evidence and readiness interface**, not an execution engine.
