# Runbook: Approval Queue Stuck

Status: Phase-G support runbook, manual review only

## Trigger

An approval-required item remains pending, expired, mismatched, or blocked in
projection metadata.

## Operator Response

1. Record the action ID, operator ID label, tenant label, and policy refs.
2. Confirm whether the item is only a metadata projection.
3. Check the Phase-D dependency request for unresolved approval-token and
   evidence-owner questions.
4. Escalate to Guardian/LIMA Office owners if approval behavior is needed.

## Blocked Actions

- No approval token issuance.
- No approval token verification.
- No signature verification.
- No replay override.
- No local model or connector execution.
