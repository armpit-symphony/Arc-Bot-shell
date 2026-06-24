# Runbook: Evidence Packet Missing

Status: Phase-G support runbook, manual review only

## Trigger

A preview, blocked action, approval decision, or operator correction lacks an
expected evidence reference.

## Operator Response

1. Record the task/action ID and expected evidence ref.
2. Confirm whether the evidence ref is projection-only.
3. Check whether the Phase-D durable evidence writer implementation is still
   blocked.
4. Capture a support note and stop before any replay or synthetic evidence
   creation.

## Blocked Actions

- No durable evidence write.
- No audit/Spine publication.
- No synthetic backfill.
- No customer data retention change.
- No execution based on missing evidence.
