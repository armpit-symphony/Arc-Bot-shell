# Arc LIMA Office Read Adapter Contract

Date: 2026-06-21
Status: Phase-C read-only adapter scaffold

## Purpose

`arc_lima_office_read_adapter_projection` exports Arc worker shell metadata in
a LIMA Office-readable `RuntimeStateSnapshot` style shape.

## Current Authority

- Export worker posture metadata.
- Export local model readiness metadata.
- Export preview, blocked, and approval-required queues.
- Export evidence and policy refs.
- Export preview artifact refs.

## Blocked In This Phase

- No live LIMA imports.
- No supervisor pull service.
- No worker dispatch.
- No approval issuance.
- No local model execution.
- No connector action.
- No customer-system mutation.
- No external send.
- No persistence writes.

## Required Snapshot Posture

- `projection_scope = read_only`
- `source_access_mode = read_only`
- `runtime_authority_blocked = true`
- `runtime_execution_blocked = true`
- `connector_actions_allowed = false`
- `customer_system_mutation_allowed = false`
- `external_send_allowed = false`
- `local_model_execution_allowed = false`

## Topology

- One Supervisor Server.
- One tenant at a time for MVP.
- 1-8 Arc worker PCs.
- Supervisor owns future authoritative state.
- Arc worker shell exports read-only state until a later approved runtime phase.
