# Arc Bot Supervisor Specification

Date: 2026-06-18
Status: Phase-0 planning

## Supervisor Server Scope

Target deployment initially assumes 1 Supervisor Server for one tenant at a time.

## Supervisor Responsibilities (Foundational)

- Aggregate readiness and state summaries.
- Maintain display-only operator surfaces.
- Prepare evidence and policy refs for blocked or pending states.
- Remain read/write separated from worker execution in this phase.

## Data and Contracts

- Sources: read-only fixture projections.
- Future sources: `app.services.guardian.suite`, `guardian_spine_*` read tables.

## Control Model

- No dispatch in shell runtime.
- No live mutation from Arc Bot Shell projection modules.
- Future dispatch requires explicit approval + Guardian enforcement + validated control seams.

## Availability Requirements (Future)

- Deterministic projection availability.
- Retry-safe projection refresh path.
- Traceable blocked-state transitions.
