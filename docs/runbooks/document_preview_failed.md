# Runbook: Document Preview Failed

Status: Phase-G support runbook, manual review only

## Trigger

A document intake or extraction preview is blocked, incomplete, or fails schema
checks.

## Operator Response

1. Record the document metadata ID and source/upload ref label.
2. Confirm raw document content is not copied into logs, fixtures, or proof
   packets.
3. Check Phase-3 intake and Phase-4 extraction metadata requirements.
4. Capture the missing metadata fields as a support note.
5. Escalate before any OCR, parser, file read, model call, or connector action.

## Blocked Actions

- No raw file read.
- No OCR/parser invocation.
- No local or cloud model call.
- No connector action.
- No customer-system mutation.
