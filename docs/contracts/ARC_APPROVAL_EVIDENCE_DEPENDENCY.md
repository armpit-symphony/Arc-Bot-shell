# Arc Approval And Evidence Dependency Contract

Date: 2026-06-21
Status: Phase-D external answers recorded, runtime still blocked

## Purpose

This contract records the Guardian/LIMA Office answers received for approval
and evidence dependencies. Arc Bot Shell may use these answers as metadata
refs only. It still cannot move into enforceable approval token lineage, replay
protection, durable evidence writing, or execution-adjacent approval paths
without later implementation gates.

## Current Authority

Arc Bot Shell may emit:

- metadata-only approval request refs,
- redacted evidence refs,
- blocked queue projections,
- approval-required queue projections,
- read-only LIMA Office adapter projections,
- recorded owner-answer refs.

## External Answers Recorded

- Approval token canonical field: `approval_token_id`.
- Approval token typed ref: `approval.token:<approval_token_id>`.
- Approval binding contract family: `approval.binding`.
- Signature/replay verification owner: LIMA Office Guardian/Supervisor
  verifier plane.
- Arc Bot signature/replay boundary: consume verifier result refs only.
- Runtime state boundary: read-only projection over `supervisor.health`,
  `worker.heartbeat`, `worker.lifecycle`, `model.route`, Guardian, evidence,
  and console refs; no standalone `RuntimeStateSnapshot` schema exists yet.
- Durable evidence writer owner: LIMA Office Supervisor evidence plane.
- Durable evidence implementation: blocked.
- Operator-console server-state owner: LIMA Office Supervisor and
  operator-console plane; Arc Bot consumes read-only refs only.
- Guardian-owned local-model executor boundary: LIMA Office Guardian plane plus
  Supervisor model-route policy; no executor is approved and local execution
  remains disabled.

Sources:

- `docs/interop/ARC_BOT_LIMA_OFFICE_EXTERNAL_ANSWERS.md`
- `docs/interop/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_RESPONSE.json`

Historical request packet:
`docs/requests/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_REQUEST.md`.

## Still Blocked

- Approval token issuance.
- Approval token verification.
- Approval replay protection.
- Signature verification.
- Runtime authority acceptance.
- Durable evidence writer.
- Audit/Spine publication.
- Operator-console state authority.
- Local model execution approval.
- Connector action approval.
- External send approval.

## Remaining External Questions

No immediate owner-answer dependency remains open in Arc Bot Shell.

## Current Safety Posture

- Runtime authority remains blocked.
- Runtime execution remains blocked.
- No approval token values are generated.
- No cryptographic signing or verification is implemented.
- No durable evidence writer is implemented.
- No local-model executor is approved or invoked.
