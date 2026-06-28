# Arc Bot MVP Completion Gate

Date: 2026-06-21
Status: Phase-12 completion-readiness gate, not complete

## Purpose

This gate turns the roadmap's MVP completion criteria into an explicit
evidence matrix. It prevents Arc Bot Shell from being treated as a runnable MVP
until each runtime, Guardian, approval, evidence, operator-console, and field
deployment criterion has direct evidence.

## Current Result

Arc Bot Shell is not complete as an MVP.

Current repo artifacts prove strong Phase-0/contract readiness, but they do
not prove live runtime completion. Lima Office has answered the Phase-D owner
and boundary questions now recorded in Arc Bot Shell, but the gate must remain
blocked until runtime implementation work is approved, added, and verified.

## Preview Command

```powershell
python -m phase12_mvp_completion.completion --compact
```

## External Answers Recorded

- Approval-token reference format: `approval_token_id` and
  `approval.token:<approval_token_id>`.
- Approval binding fields: `approval.binding`.
- Signature/replay verification owner: LIMA Office Guardian/Supervisor
  verifier plane.
- Runtime state: read-only projection over supervisor, worker, model route,
  Guardian, evidence, and console refs.
- Durable evidence writer owner: LIMA Office Supervisor evidence plane.
- Operator-console server-state owner: LIMA Office Supervisor and
  operator-console plane.
- Guardian-owned local-model executor boundary: LIMA Office Guardian plane
  plus Supervisor model-route policy; no executor is approved and execution
  remains disabled.

Recorded handoffs:

- `docs/interop/ARC_BOT_LIMA_OFFICE_EXTERNAL_ANSWERS.md`
- `docs/interop/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_RESPONSE.json`

## Blocking External Dependencies

No immediate owner-answer dependency remains open in Arc Bot Shell.

The original request packet remains as history:
`docs/requests/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_REQUEST.md`.

Runtime implementation approval is tracked by:

- `docs/requests/ARC_BOT_RUNTIME_IMPLEMENTATION_GATE_REQUEST.md`
- `docs/proof_packets/ARC_BOT_RUNTIME_IMPLEMENTATION_GATE_REQUEST_PACKET.md`
- `docs/contracts/schemas/arc_runtime_implementation_gate_response.schema.json`
- `docs/examples/arc_lima/runtime_implementation_gate_response.template.json`

Response-intake preview command:

```powershell
python -m phase12_mvp_completion.runtime_implementation_gate --response-path path\to\response.json --compact
```

A shape-complete response still cannot grant runtime authority by itself;
implementation remains blocked until separate approved implementation work is
added and verified.

## Blocking Runtime Dependencies

- Live supervisor attachment.
- Worker registration lifecycle.
- Approval token issuance or verification.
- Verifier result-ref ingest.
- Durable evidence writer implementation.
- Operator-console server-state implementation.
- Local-model executor runtime contract.

## Must Remain Blocked

- Live supervisor attachment.
- Local model invocation.
- Approval token issuance or verification.
- Durable evidence write.
- Connector read/write.
- Customer-system mutation.
- External message send.
- Production deployment.

## Completion Rule

MVP completion may be claimed only when
`phase12_mvp_completion.completion` can truthfully set `mvp_complete = true`
with direct evidence for every criterion and no remaining runtime blockers.
