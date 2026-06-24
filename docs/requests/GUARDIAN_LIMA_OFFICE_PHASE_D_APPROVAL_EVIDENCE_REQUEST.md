# Guardian / LIMA Office Phase-D Approval Evidence Request

Date: 2026-06-21
Status: answered by Lima Office handoff, runtime still blocked

## Request

Arc Bot Shell requested Guardian/LIMA Office decisions before implementing the
next approval and evidence phase. Lima Office answered the Phase-D dependency
questions in commit `4e1ed0e54515d41933b8d7132d091b2915d9dff7`.

Recorded Arc-side handoff:
`docs/interop/ARC_BOT_LIMA_OFFICE_EXTERNAL_ANSWERS.md`.

## Questions

1. What is the canonical approval-token reference format?
2. Which fields must bind an approval to an action?
   Required candidates include action ID, operator ID, tenant ID, policy refs,
   evidence refs, expiry, nonce, device ID, and session ID.
3. Who owns signature verification and replay protection?
   Candidate owners are LIMA Office supervisor, Guardian Suite, or LIMA Runtime
   kernel.
4. What canonical `RuntimeStateSnapshot` field names should Arc match before
   freezing the read adapter shape?
5. Which component owns immutable evidence packet persistence and audit/Spine
   event durability?

## Why This Blocks Phase D

The answers allow Arc Bot to reference canonical metadata fields, but they do
not implement approval token lineage, replay prevention, durable evidence
packets, or execution-adjacent approval paths. The current repo remains
metadata-only and fail-closed.

Remaining owner questions:

- Operator-console server-state owner.
- Guardian-owned local-model executor boundary.

## Current Safe Artifacts

- `arc_guardian_spine/intent_envelope.py`
- `phase6_lima_office_integration/read_adapter.py`
- `phase7_approval_evidence/readiness.py`
- `docs/contracts/ARC_APPROVAL_EVIDENCE_DEPENDENCY.md`
