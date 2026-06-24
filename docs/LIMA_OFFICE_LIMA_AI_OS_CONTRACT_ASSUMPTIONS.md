# LIMA Office / LIMA AI OS Contract Assumptions

Date: 2026-06-21
Status: reviewed planning assumptions

## Deployment Assumptions

- One Supervisor Server.
- One tenant at a time for MVP.
- 1-8 Arc worker mini PCs.
- Arc Bot Shell runs as a bounded worker shell under LIMA Office.
- LIMA Runtime / LIMA AI OS remains the future kernel/runtime substrate.

## Authority Assumptions

- Guardian is the syscall gate for model calls, tool calls, connector access,
  file/network/browser actions, privileged operations, and outbound messages.
- Arc Bot Shell does not grant runtime authority from UI state.
- LIMA Office owns future authoritative supervisor state.
- Worker-local state is presentation/readiness metadata until signed runtime
  envelopes are approved.

## Data Assumptions

- Single-tenant state only for MVP.
- Cross-tenant memory is disabled.
- Fixtures, proof packets, and logs must not contain raw customer content,
  provider tokens, OAuth secrets, API keys, refresh tokens, or credential
  material.
- Evidence refs are redacted metadata until an approved evidence store exists.

## Integration Assumptions

- `app.services.guardian.suite` is a future read reference, not an imported
  runtime dependency in this repo.
- Guardian Spine sources are read-only handoff sources in this repo:
  - `guardian_spine_tasks`
  - `guardian_spine_events`
  - `guardian_spine_approvals`
  - `guardian_spine_projects`
- Future live execution requires signed intent envelopes, approval token
  lineage, evidence/rollback refs, and LIMA Office control-plane acceptance.

## Blocked Until Later Approval

- Local model execution.
- Cloud model fallback.
- Provider SDK use.
- Connector reads or writes.
- External sends.
- Customer-record mutation.
- Worker dispatch.
- Production deployment claims.
