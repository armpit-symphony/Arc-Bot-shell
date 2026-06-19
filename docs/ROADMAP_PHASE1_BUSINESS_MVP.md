# Arc Bot Business MVP Roadmap (Phase-1 Candidate)

Date: 2026-06-19
Status: planning and implementation-boundary lock

## Objective

Define the first business-grounded MVP execution sequence from the current
Phase-0 scaffolding and approved planning artifacts, while preserving the
no-execution guardrail posture.

This roadmap keeps behavior in documents/contracts/tests only until a future
implementation branch explicitly unlocks runtime authority through approved
Guardian and LIMA Office gate packets.

## Starting Position

- Scope lock and phase-chain read-only scaffold are complete.
- Phase-1 business inventory is defined and contract-validated.
- Phase-1 client configuration is documented as docs-only with no-execution skeleton constraints.
- Reference contracts and seams are documented for:
  - Operator console surfaces (`work_queue`, `runtime_settings`, `overview`).
  - Phase-1 read-feed -> consumer -> runtime-control seam projection.
  - `app.services.guardian.suite` read-path attachment planning.

## Delivery Targets

### Milestone 1: Contracted MVP Definition

- Freeze the final surface set for initial business MVP:
  - Task Inbox
  - Task Runner Panel
  - Approval Queue
  - Connector Status
  - Evidence Panel
  - Client Config
  - Bot Role / Persona Template
- Lock all phase-0 to phase-1 behavior as preview/render only and blocked for:
  - connector live I/O
  - model/provider calls
  - worker dispatch
  - customer-system mutation
  - persistence writes
  - production-readiness claims
- Produce a migration-gate packet for any future activation path.

### Milestone 2: Runtime Authority Gating Pack

- [x] Define one-to-one mapping from each planned user intent to required future gates:
  - `guardian_runtime_authority_approval`
  - `connector_authority_approval`
  - `approval_token_lineage`
  - `evidence_and_rollback_gate`
  - `production_readiness_approval`
- Keep all future gates unresolved in Phase-1 candidate state.
- Keep all surface outputs fail-closed when gate data is absent or stale.

### Milestone 3: LIMA Office/Shell Runtime Handoff Readiness

- Validate proof packet set for:
  - phase-0 scope lock
  - phase-1 business inventory
  - phase-1 client configuration
  - `ARC_BOT_PHASE1_READINESS_BUNDLE_PACKET`
  - read-feed seam projection
- Freeze source-of-truth assumption: server-side, authoritative state in future
  LIMA Office / LIMA AI Office.
- Keep local UI/storage as presentation state only.
- Require explicit operator approval workflow for any downstream state mutation.

Topology boundary: this roadmap assumes one supervisor and **1-8 workers**.

## Non-goals for this roadmap (this phase)

- No execution implementation.
- No live connectors or network mutation.
- No model/provider/local inference routing.
- No worker dispatch, service control, or remediation actions.
- No customer data writes or tenant switching.

## Exit Criteria for the Candidate

- New MVP artifact references are complete and test-addressed.
- Foundation docs/test suite references the roadmap.
- Any deviation from preview-only behavior requires a new approved proof packet
  and explicit gate migration in a later phase.

## Required References

- [README current foundation docs list](../README.md)
- [Phase-0 roadmap](../docs/ROADMAP.md)
- [Phase-0 scope-lock punch list](ROADMAP_SCOPE_LOCK_PUNCH_LIST.md)
- [Phase-1 business inventory proof packet](proof_packets/ARC_BOT_PHASE1_BUSINESS_INVENTORY_PROOF_PACKET.md)
- [Phase-1 client configuration no-execution packet](proof_packets/ARC_BOT_PHASE1_CLIENT_CONFIGURATION_NO_EXECUTION_PACKET.md)
- [Phase-1 client configuration migration gate packet](proof_packets/ARC_BOT_PHASE1_CLIENT_CONFIGURATION_MIGRATION_GATE_PACKET.md)
- [Phase-1 readiness bundle packet](proof_packets/ARC_BOT_PHASE1_READINESS_BUNDLE_PACKET.md)
- [Phase-1 runtime authority gating packet](proof_packets/ARC_BOT_PHASE1_RUNTIME_AUTHORITY_GATING_PACKET.md)
