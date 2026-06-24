# Insurance Intake Narrow Pilot

Date: 2026-06-21
Status: Phase-H/Phase-11 planning package, runtime blocked

## Objective

Define the first narrow Arc Bot pilot: insurance intake summary and
missing-information checklist for operator review.

This pilot package is not a live pilot authorization. It uses sanitized local
sample metadata only and remains blocked until Guardian/LIMA Office approves
approval/evidence lineage, local model preview execution, operator-console
state, field deployment boundaries, and pilot evidence handling.

## Pilot Workflow

1. Use sanitized sample document metadata.
2. Render Phase-4 extraction preview refs only.
3. Render Phase-5 workflow previews for:
   - `insurance_claim_packet_triage`
   - `missing_information_checklist`
4. Require operator review for every draft section.
5. Record gaps as notes only.

## Allowed In This Phase

- Read-only projection rendering.
- Sanitized sample metadata.
- Draft-preview workflow output.
- Blocked-action review.
- Evidence-gap notes.
- Operator correction notes.

## Blocked In This Phase

- Raw customer document processing.
- Local model invocation.
- Cloud model fallback.
- Connector reads/writes.
- Customer-record updates.
- External sends.
- Form submissions.
- Durable evidence writes.
- Approval-token issuance or verification.
- Production or live-pilot claims.

## Exit Criteria

- `python -m phase11_pilot_readiness.pilot --compact` renders.
- `tests/test_arc_pilot_readiness.py` passes.
- Every workflow output remains `draft_preview_only`.
- Every consequential action remains blocked or approval-required.
- Phase-D Guardian/LIMA Office dependencies are still listed as blockers for
  live pilot work.
