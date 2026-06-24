# Runbook: Model Not Reachable

Status: Phase-G support runbook, manual review only

## Trigger

Local model readiness is `setup_required`, `blocked`, stale, or missing in an
Arc projection.

## Operator Response

1. Record the worker ID and model readiness label.
2. Confirm no cloud fallback is enabled.
3. Confirm no provider credentials are present in the repo or logs.
4. Capture the readiness gap as a support note.
5. Escalate to Guardian/LIMA Office owners before any model probe, install,
   update, or invocation.

## Blocked Actions

- No Ollama API call.
- No socket probe.
- No provider SDK call.
- No model download.
- No model invocation.
- No cloud fallback.
