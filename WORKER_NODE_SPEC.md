# Arc Bot Worker Node Specification

Date: 2026-06-18
Status: Phase-0 draft

## Role

Worker nodes are bounded execution workers in future phases; in Phase-0 they are **informational entities only** in shell state.

## Node Responsibilities (post-Phase-0)

- Receive reviewed work assignments.
- Report heartbeat/health metadata.
- Execute work under approval and Guardian guardrails.
- Emit lineage evidence and outcome summaries.

## Worker Node Data Surfaces (Foundation)

- `worker.lifecycle` references.
- `worker.heartbeat` metadata.
- `worker.deployment` and `worker.attestation` readiness markers (display-only references in this phase).

## Safety Constraints

- No task dispatch or execution initiated from shell in Phase-0.
- No direct worker control channels in scaffold modules.
