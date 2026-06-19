# Arc Bot No-Execution Skeleton Plan

Date: 2026-06-19
Status: read-only planning artifact

This plan defines the skeleton that may be reviewed before any Arc Bot implementation surface exists. It is not a frontend, backend, persistence layer, connector adapter, worker runtime, model router, scheduler, Guardian implementation, or LIMA runtime integration.

## Skeleton Layers

| Layer | Allowed now | Blocked now |
| --- | --- | --- |
| Client configuration | Static schema, static fixture, policy/evidence refs | persistence, customer record mutation, tenant switching |
| Surface inventory | Static role and surface metadata | executable buttons, dispatch controls, approval token issue |
| Connector posture | readiness labels and blocker notes | OAuth, token entry, live reads, live writes, webhooks |
| Runtime posture | blocked action display and model/local readiness notes | provider calls, local model calls, route mutation |
| Worker posture | enrollment and evidence metadata | service start/stop, quarantine release, tool-pack broadening |
| Evidence posture | evidence ref requirements | raw evidence access, secret reveal, evidence deletion |

## Required Static Artifacts

- `tests/fixtures/arc_bot_phase1_client_configuration.json`
- `docs/contracts/schemas/arc_bot_client_configuration.schema.json`
- `tests/fixtures/arc_bot_phase1_client_configuration_no_execution_packet.json`
- `docs/proof_packets/ARC_BOT_PHASE1_CLIENT_CONFIGURATION_NO_EXECUTION_PACKET.md`

## Allowed Review Actions

- Review configuration labels.
- Compare fixture fields to schema constants.
- Review policy and evidence references.
- Record blocker notes as metadata in future planning artifacts.
- Link future approval gates by reference.

## Blocked Actions

- No frontend route activation.
- No interactive action controls.
- No persistence or customer data writes.
- No connector live I/O, OAuth, webhooks, token entry, or credential value access.
- No provider/model/local inference call.
- No worker dispatch or service control.
- No file, browser, network, device, robotics, or physical-world behavior.
- No production deployment or product-readiness claim.

## Future Gate Requirements

Any move beyond this skeleton requires:

- a Guardian authority packet,
- explicit operator approval,
- policy and evidence references,
- rollback metadata,
- tenant-boundary checks,
- secret/credential handling plan,
- connector consent/scope plan when connectors are involved,
- LIMA runtime and consumer integration audit.
