# Arc Bot Phase-D Approval Evidence Dependency Packet

Date: 2026-06-21
Status: external answers recorded, runtime still blocked

## Objective

Record the Guardian/LIMA Office decisions received for Arc Bot approval and
evidence dependencies while preserving the runtime block for enforceable
approval token lineage, replay protection, durable evidence writing, and
execution-adjacent approval flows.

## Evidence

- Projection module: `phase7_approval_evidence/readiness.py`
- Preview command: `python -m phase7_approval_evidence.readiness`
- Contract doc: `docs/contracts/ARC_APPROVAL_EVIDENCE_DEPENDENCY.md`
- External request packet:
  `docs/requests/GUARDIAN_LIMA_OFFICE_PHASE_D_APPROVAL_EVIDENCE_REQUEST.md`
- Recorded Lima Office answers:
  `docs/interop/ARC_BOT_LIMA_OFFICE_EXTERNAL_ANSWERS.md`
- Recorded remaining-gate response:
  `docs/interop/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_RESPONSE.json`
- Remaining implementation gate request:
  `docs/requests/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_REQUEST.md`
- Tests: `tests/test_arc_approval_evidence_dependency.py`

## Required Posture

- `runtime_authority_blocked = true`
- `runtime_execution_blocked = true`
- `status = external_answers_recorded_runtime_still_blocked`
- `requires_external_owner_input = false`
- `requires_runtime_implementation_gate_approval = true`
- No approval token issuance.
- No signature verification.
- No durable evidence writer.
- No runtime execution.

## Answers Recorded

- Approval token canonical field: `approval_token_id`.
- Approval token typed ref: `approval.token:<approval_token_id>`.
- Approval binding contract family: `approval.binding`.
- Signature/replay verification owner: LIMA Office Guardian/Supervisor
  verifier plane; Arc Bot consumes result refs only.
- Runtime state uses read-only projections; no standalone
  `RuntimeStateSnapshot` schema exists yet.
- Durable evidence writer owner: LIMA Office Supervisor evidence plane;
  durable implementation remains blocked.
- Operator-console server-state owner: LIMA Office Supervisor and
  operator-console plane; Arc Bot consumes read-only refs only.
- Guardian-owned local-model executor boundary: LIMA Office Guardian plane plus
  Supervisor model-route policy; no executor is approved and local execution
  remains disabled.

## Remaining Blockers

No immediate owner-answer dependency remains open in Arc Bot Shell.

Runtime contracts and implementation remain blocked for approval
issuance/verification, verifier-result ingestion, supervisor projection
ingestion, durable evidence writes, operator-console server-state runtime, and
Guardian-owned local-model execution.
