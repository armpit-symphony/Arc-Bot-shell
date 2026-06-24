# Arc Worker Local PC Setup

Date: 2026-06-21
Status: Phase-G planning guide, runtime blocked

## Purpose

This guide defines the operator checklist for preparing a local mini PC as an
Arc worker node for a future LIMA Office field pilot.

It is not an installer and does not grant deployment authority. Any future
software install, service start, supervisor registration, local model call,
connector setup, remediation, or customer data access requires Guardian/LIMA
Office approval and evidence.

## Target Topology

- One Supervisor Server.
- One to eight Arc worker mini PCs.
- One tenant/customer workspace at a time.
- Local-first worker posture.
- No cloud model fallback by default.
- No live customer connectors in this phase.

## Operator Checklist

1. Confirm the worker PC has an assigned local asset label.
2. Confirm the target tenant/workspace label is single-tenant.
3. Confirm the operator role and approval owner are known.
4. Confirm the repo checkout is internal/private for this phase.
5. Run only read-only projection smoke commands.
6. Record any readiness gaps as notes; do not remediate automatically.
7. Keep connector credentials, provider tokens, and customer data out of the
   repo, logs, screenshots, proof packets, and fixtures.

## Explicit Non-Actions

- Do not install or update software from this guide.
- Do not start services.
- Do not register with LIMA Office.
- Do not call Ollama or any provider API.
- Do not open network probes.
- Do not connect Gmail, Slack, calendars, CRMs, file stores, or helpdesk tools.
- Do not process customer documents.
- Do not send external messages.
- Do not write durable evidence packets.

## Smoke Command

Use the read-only smoke wrapper:

```powershell
./scripts/arc_worker_smoke.ps1
```

The wrapper runs local projection/test checks only.
