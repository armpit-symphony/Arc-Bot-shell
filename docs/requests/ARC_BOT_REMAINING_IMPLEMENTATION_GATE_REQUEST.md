# Arc Bot Remaining Implementation Gate Request

Date: 2026-06-22
Status: ready to send to LIMA Office / Guardian owners

## Send To

- LIMA Office Guardian/Supervisor owners.
- LIMA Runtime / Guardian Model Harness owners.

## Subject

Arc Bot remaining implementation-gate answers needed: operator console state
and Guardian-owned local-model executor boundary

## Message

Arc Bot has recorded the Lima Office handoff answers from commit
`4e1ed0e54515d41933b8d7132d091b2915d9dff7`.

Five Phase-D dependency answers are now recorded:

- Approval token canonical field: `approval_token_id`.
- Approval token typed ref: `approval.token:<approval_token_id>`.
- Approval binding contract family: `approval.binding`.
- Signature/replay verification owner: LIMA Office Guardian/Supervisor
  verifier plane; Arc Bot consumes result refs only.
- Durable evidence writer owner: LIMA Office Supervisor evidence plane;
  durable implementation remains blocked.

Arc Bot still needs two owner decisions before any implementation-gate lane can
start:

1. Which component owns authoritative operator-console server state for
   approval queue, deny/block state, operator decisions, mismatch reasons,
   and verifier result refs?
2. Which Guardian-owned contract gates local-model executor authority for
   approved preview work on an Arc worker PC?

Please answer using this shape:

```text
operator_console_server_state_owner:
  owner:
  canonical contract family:
  authoritative fields:
  Arc Bot may consume:
  Arc Bot must not do:

guardian_owned_local_model_executor_boundary:
  owner:
  canonical contract family:
  required Guardian inputs:
  required verifier/evidence outputs:
  Arc Bot may consume:
  Arc Bot must not do:
```

## Arc Bot Assumptions Until Answered

- `mvp_complete = false`.
- Runtime authority remains blocked.
- Runtime execution remains blocked.
- Arc Bot will not issue or verify approval tokens.
- Arc Bot will not own authoritative operator-console server state.
- Arc Bot will not invoke Ollama/Qwen or any local/cloud model.
- Arc Bot will not write durable evidence, call connectors, mutate customer
  systems, send external messages, register workers, or attach to a live
  Supervisor Server.

## Arc Bot Reference Artifacts

- `docs/interop/ARC_BOT_LIMA_OFFICE_EXTERNAL_ANSWERS.md`
- `docs/contracts/ARC_APPROVAL_EVIDENCE_DEPENDENCY.md`
- `docs/readiness/ARC_BOT_MVP_COMPLETION_GATE.md`
- `phase7_approval_evidence/readiness.py`
- `phase7_approval_evidence/remaining_gate_response.py`
- `phase12_mvp_completion/completion.py`

## Arc Bot Response Intake

After the owner response arrives, Arc Bot can inspect the local JSON packet without granting runtime authority:

```powershell
python -m phase7_approval_evidence.remaining_gate_response --response-path path\to\owner_response.json --compact
```

A complete response shape still reports runtime authority and runtime execution as blocked. Implementation work must remain separate from response-shape inspection.
