# Arc Bot Lima Office External Answers

Date: 2026-06-21
Status: external handoff recorded, runtime still blocked

## Source

- Source repo: `Lima-Office`
- Source branch: `arc-bot-ollama-qwen-readiness-handoff`
- Source commit: `4e1ed0e54515d41933b8d7132d091b2915d9dff7`
- Source packet:
  `Lima-Office/docs/interop/ARC_BOT_GUARDIAN_LIMA_EXTERNAL_ANSWERS.md`
- Recorded remaining-gate response:
  `docs/interop/ARC_BOT_REMAINING_IMPLEMENTATION_GATE_RESPONSE.json`

## Answers Recorded

1. Approval token reference:
   - Canonical field: `approval_token_id`
   - Generic typed ref form: `approval.token:<approval_token_id>`
2. Approval binding:
   - Canonical contract family: `approval.binding`
   - Binding covers tenant/customer refs, chain IDs, Guardian decision refs,
     task/worker/tool refs, scope hashes, nonce/expiry, status, verification,
     mismatch reasons, and evidence refs.
3. Signature and replay verification owner:
   - Owner: LIMA Office Guardian/Supervisor verifier plane.
   - Arc Bot boundary: consume verifier result refs only.
4. Runtime state:
   - No standalone `RuntimeStateSnapshot` schema is available yet.
   - Arc Bot should use a read-only projection over `supervisor.health`,
     `worker.heartbeat`, `worker.lifecycle`, `model.route`, Guardian,
     evidence, and console refs.
5. Durable evidence writer:
   - Owner: LIMA Office Supervisor evidence plane.
   - Durable implementation remains blocked.
6. Operator-console server state:
   - Owner: LIMA Office Supervisor and operator-console plane.
   - Arc Bot may consume read-only console/supervisor/evidence refs.
   - Arc Bot must not become source of truth, mutate console server state, or
     use local display state as authorization.
7. Guardian-owned local-model executor boundary:
   - Owner: LIMA Office Guardian plane plus Supervisor model-route policy.
   - Current contract family: `model.route` metadata only.
   - `local_model_bundle_ref.execution_enabled` remains `false`.
   - Arc Bot must not execute local inference, call Ollama/Qwen, probe
     endpoints, or treat route metadata as execution authority.

## Remaining Runtime Blockers

- Approval token issuance and verification contracts.
- Verifier result-ref ingest contract.
- Supervisor projection ingest implementation.
- Durable evidence writer and audit/Spine implementation.
- Operator-console server-state runtime implementation.
- Guardian-owned local-model executor contract and implementation.
- Live supervisor attachment and worker registration lifecycle.

## Arc Bot Rule

These answers are contract metadata only. They do not grant runtime authority,
local model execution, approval issuance, approval verification, durable
evidence writing, connector I/O, customer mutation, or production deployment.
