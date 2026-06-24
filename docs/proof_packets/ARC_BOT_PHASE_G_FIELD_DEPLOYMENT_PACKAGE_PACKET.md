# Arc Bot Phase-G Field Deployment Package Packet

Date: 2026-06-21
Status: read-only field-prep evidence

## Objective

Record the Phase-G package that makes Arc worker mini-PC field preparation
repeatable without granting runtime, deployment, connector, model, approval, or
customer-system authority.

## Evidence

- Projection module: `phase10_field_deployment/package.py`
- Preview command: `python -m phase10_field_deployment.package`
- Setup guide: `docs/deployment/ARC_WORKER_LOCAL_PC_SETUP.md`
- Package guide: `docs/deployment/ARC_FIELD_DEPLOYMENT_PACKAGE.md`
- Smoke wrapper: `scripts/arc_worker_smoke.ps1`
- Tests: `tests/test_arc_field_deployment_package.py`

## Support Runbooks

- `docs/runbooks/worker_offline.md`
- `docs/runbooks/model_not_reachable.md`
- `docs/runbooks/approval_queue_stuck.md`
- `docs/runbooks/evidence_packet_missing.md`
- `docs/runbooks/document_preview_failed.md`

## Required Posture

- `runtime_authority_blocked = true`
- `runtime_execution_blocked = true`
- `production_ready = false`
- `production_deployment_allowed = false`
- Single tenant.
- One Supervisor Server.
- One to eight Arc workers.
- No software install/update.
- No model invocation.
- No connector action.
- No durable evidence writer.

## Blocker Reference

Phase-D Guardian/LIMA Office approval/evidence questions remain blocking for
any execution-adjacent field pilot behavior:

`docs/requests/GUARDIAN_LIMA_OFFICE_PHASE_D_APPROVAL_EVIDENCE_REQUEST.md`
