# Arc Bot Lima Office External Answers

Date: 2026-06-21
Status: external handoff recorded, runtime still blocked

## Source

- Source repo: `Lima-Office`
- Source branch: `arc-bot-ollama-qwen-readiness-handoff`
- Source commit: `4e1ed0e54515d41933b8d7132d091b2915d9dff7`
- Source packet:
  `Lima-Office/docs/interop/ARC_BOT_GUARDIAN_LIMA_EXTERNAL_ANSWERS.md`

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

## Remaining Blockers

- Operator-console server-state owner.
- Guardian-owned local-model executor boundary.
- Runtime implementation contracts for approval issuance/verification,
  verifier-result ingestion, supervisor projection ingestion, and durable
  evidence writes.

## Arc Bot Rule

These answers are contract metadata only. They do not grant runtime authority,
local model execution, approval issuance, approval verification, durable
evidence writing, connector I/O, customer mutation, or production deployment.
