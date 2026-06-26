# Arc Bot Runtime Implementation Gate Request

Date: 2026-06-25
Status: ready to send to LIMA Office / Guardian runtime owners

## Send To

- LIMA Office Supervisor owners.
- LIMA Office Guardian/Supervisor verifier owners.
- LIMA Office Supervisor evidence-plane owners.
- LIMA Office operator-console plane owners.
- LIMA Office Guardian plane plus Supervisor model-route policy owners.

## Subject

Arc Bot runtime implementation gate approval request for guarded MVP path

## Context

Arc Bot Shell has recorded the Phase-D owner and boundary answers from LIMA
Office. No immediate owner-answer dependency remains open in Arc Bot Shell.
The repo remains metadata-only and fail-closed.

Recorded handoffs:

- `docs/interop/ARC_BOT_LIMA_OFFICE_EXTERNAL_ANSWERS.md`
- `docs/interop/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_RESPONSE.json`

Current MVP completion projection:

```powershell
python -m phase12_mvp_completion.completion --compact
```

The projection still reports:

- `mvp_complete = false`
- `production_ready = false`
- `runtime_authority_blocked = true`
- `runtime_execution_blocked = true`
- `requires_runtime_implementation_gate_approval = true`

## Approval Requested

Please approve, reject, or amend the runtime implementation gate for the seven
remaining runtime-dependent dependencies. Arc Bot will not begin runtime work
until this approval exists as a recorded contract/handoff.

1. `live_supervisor_attachment`
   - Owner: LIMA Office Supervisor plane.
   - Needed: live supervisor attachment contract and allowed transport.
   - Required evidence: supervisor identity/trust contract, worker attach
     lifecycle, read-only projection ingest acceptance, disconnect/fail-closed
     behavior.
2. `worker_registration_lifecycle`
   - Owner: LIMA Office Supervisor and worker lifecycle owners.
   - Needed: bounded Arc worker registration lifecycle.
   - Required evidence: worker identity fields, tenant binding, heartbeat
     cadence, revocation/offline states.
3. `approval_token_issuance_or_verification`
   - Owner: LIMA Office Guardian/Supervisor verifier plane.
   - Needed: durable approval token issuance and verification contract.
   - Required evidence: `approval_token_id` issuance semantics,
     `approval.binding` verification semantics, expiry/nonce/replay rejection,
     mismatch reason refs.
4. `verifier_result_ref_ingest`
   - Owner: LIMA Office Guardian/Supervisor verifier plane.
   - Needed: verifier result-ref ingest contract.
   - Required evidence: allowed verifier result states, freshness rules,
     binding to action/task/worker refs, fail-closed missing-result behavior.
5. `durable_evidence_writer_implementation`
   - Owner: LIMA Office Supervisor evidence plane.
   - Needed: durable evidence writer and audit/Spine publication contract.
   - Required evidence: immutable evidence packet schema, writer ownership and
     retention policy, audit/Spine publication semantics, failure and rollback
     handling.
6. `operator_console_server_state_implementation`
   - Owner: LIMA Office Supervisor and operator-console plane.
   - Needed: operator-console server-state runtime implementation contract.
   - Required evidence: canonical server-state fields, approval queue mutation
     rules, operator decision lifecycle, UI read-only/local display boundary.
7. `local_model_executor_runtime_contract`
   - Owner: LIMA Office Guardian plane plus Supervisor model-route policy.
   - Needed: Guardian-owned local-model executor contract.
   - Required evidence: executor syscall boundary, `model.route`
     execution-enabled semantics, redacted prompt/input/output refs, network
     egress denial proof, Ollama/Qwen failure and timeout policy.

## Arc Bot Must Not Start Until Approved

- Live Supervisor Server attachment.
- Worker registration lifecycle.
- Approval token issuance or verification.
- Verifier result-ref ingest.
- Durable evidence write.
- Operator-console state authority.
- Local model invocation.
- Connector read/write.
- Customer-system mutation.
- External message send.
- Production deployment.

## Requested Response Shape

Arc Bot can inspect a response using the schema/template below without granting runtime authority:

- Schema: `docs/contracts/schemas/arc_runtime_implementation_gate_response.schema.json`
- Template: `docs/examples/arc_lima/runtime_implementation_gate_response.template.json`
- Preview command: `python -m phase12_mvp_completion.runtime_implementation_gate --response-path path\to\response.json --compact`

```text
runtime_implementation_gate_decision:
  decision: approved | rejected | amend_requested
  approving_owner:
  approved_dependencies:
  rejected_or_deferred_dependencies:
  required_contract_refs:
  required_schema_refs:
  required_test_gates:
  explicit_runtime_limits:
  evidence_writer_authority:
  local_model_executor_authority:
  operator_console_state_authority:
  effective_after_commit_or_packet_ref:
```

## Arc Bot Rule

This request is not a runtime implementation. It is the next approval gate.
Arc Bot remains docs/contracts/projections-only until the owners approve a
specific runtime implementation lane and the repo adds tests before any
execution-adjacent behavior.
