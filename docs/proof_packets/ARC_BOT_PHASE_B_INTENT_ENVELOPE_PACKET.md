# Arc Bot Phase-B Intent Envelope Proof Packet

Date: 2026-06-21
Status: contract scaffold evidence

## Objective

Create a non-executing Arc intent envelope contract for future LIMA Office /
Guardian signed-request handoff.

## Evidence

- Contract module: `arc_guardian_spine/intent_envelope.py`
- Preview CLI: `python -m arc_guardian_spine.intent_envelope_preview`
- Contract doc: `docs/contracts/ARC_INTENT_ENVELOPE.md`
- Tests: `tests/test_arc_intent_envelope.py`

## Required Posture

- `runtime_authority_blocked = true`
- `runtime_execution_blocked = true`
- Arc Shell signature verification is false.
- Guardian verification is required.
- Approval token lineage is metadata only.

## Non-Goals

- No signing implementation.
- No signature verification.
- No approval token issuance.
- No execution, dispatch, model call, connector action, or customer mutation.
