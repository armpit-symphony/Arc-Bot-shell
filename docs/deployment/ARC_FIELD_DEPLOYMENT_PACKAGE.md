# Arc Field Deployment Package

Date: 2026-06-21
Status: Phase-G package, planning ready and runtime blocked

## Objective

Make a one-supervisor, one-to-eight-worker Arc Bot deployment repeatable enough
for internal field-prep review without claiming production readiness.

## Package Contents

- Worker local PC setup guide:
  `docs/deployment/ARC_WORKER_LOCAL_PC_SETUP.md`
- Field deployment readiness projection:
  `phase10_field_deployment/package.py`
- Read-only smoke wrapper:
  `scripts/arc_worker_smoke.ps1`
- Support runbooks:
  - `docs/runbooks/worker_offline.md`
  - `docs/runbooks/model_not_reachable.md`
  - `docs/runbooks/approval_queue_stuck.md`
  - `docs/runbooks/evidence_packet_missing.md`
  - `docs/runbooks/document_preview_failed.md`
- Proof packet:
  `docs/proof_packets/ARC_BOT_PHASE_G_FIELD_DEPLOYMENT_PACKAGE_PACKET.md`

## Readiness Gates

- Topology remains one Supervisor Server and one to eight Arc workers.
- Tenant mode remains single-tenant.
- Runtime authority remains blocked.
- Runtime execution remains blocked.
- Production deployment remains disallowed.
- Phase-D approval/evidence answers are recorded, but remaining owner questions
  and runtime implementation gates stay blocked.
- Smoke checks are local, deterministic, and read-only.

## Blocked Until Later Approval

- Installing or updating software.
- Starting worker services.
- Registering workers with a live Supervisor Server.
- Invoking local or cloud models.
- Reading or writing connectors.
- Mutating customer records.
- Sending external messages.
- Writing durable evidence/audit records.
- Issuing or verifying approval tokens.

## Exit Criteria For This Phase

- All package docs and runbooks exist.
- `python -m phase10_field_deployment.package --compact` emits a safe
  read-only projection.
- `./scripts/arc_worker_smoke.ps1` passes locally.
- `python -m pytest -q` passes.
- `git diff --check` reports no whitespace errors.
