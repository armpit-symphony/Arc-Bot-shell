# Runbook: Worker Offline

Status: Phase-G support runbook, manual review only

## Trigger

An Arc worker is missing from a future Supervisor Server view or has stale
heartbeat metadata in a read-only projection.

## Operator Response

1. Record the worker ID label and tenant/workspace label.
2. Confirm whether the worker is expected to be online.
3. Check local power, display, keyboard, network cable, and Wi-Fi status
   manually.
4. Capture a support note with observed status and timestamp.
5. Escalate to the field IT owner before any restart, service action, or
   remediation.

## Blocked Actions

- No remote restart.
- No service start/stop.
- No software install or update.
- No supervisor re-registration.
- No customer-system mutation.
