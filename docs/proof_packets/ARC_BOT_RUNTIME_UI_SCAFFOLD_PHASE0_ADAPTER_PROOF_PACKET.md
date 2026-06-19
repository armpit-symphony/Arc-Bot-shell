# Arc Bot Runtime UI Scaffold Phase-0 Adapter Proof Packet

Date: 2026-06-19
Repository: `armpit-symphony/Arc-Bot-shell`
Branch: `arc-bot-runtime-ui-scaffold-readonly-adapter`
Source commit before branch: `f11f726eebcae07f056421bd3ff46ee337c9f708`

This packet records the Phase-0 read-only runtime UI scaffold adapter contract shape for
`Work Queue`, `Runtime Settings`, and `Overview`.

It is a static proof packet only. It does **not** add runtime behavior, LIMA runtime imports,
provider/model routing, live guardian enforcement, connector I/O, file mutation, browser/network
automation, scheduler execution, worker dispatch, or physical-world control.

## Files Reviewed

Arc-Bot-shell evidence reviewed:

- `README.md`
- `docs/ROADMAP.md`
- `docs/OPERATOR_CONSOLE_FOUNDATION.md`
- `docs/contracts/ARC_BOT_OPERATOR_CONSOLE_STATE.md`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_contract_pack.json`
- `tests/fixtures/arc_bot_phase0_work_queue_state_snapshot.json`
- `tests/fixtures/arc_bot_phase0_runtime_settings_state_snapshot.json`
- `docs/contracts/schemas/arc_bot_console_state_envelope.schema.json`
- `docs/contracts/schemas/arc_bot_work_queue_state.schema.json`
- `docs/contracts/schemas/arc_bot_runtime_settings_state.schema.json`
- `docs/contracts/schemas/arc_bot_overview_state.schema.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_preview_contract.json`
- `tests/fixtures/arc_bot_phase0_overview_state_snapshot.json`

New files in this packet:

- `docs/proof_packets/ARC_BOT_RUNTIME_UI_SCAFFOLD_PHASE0_ADAPTER_PROOF_PACKET.md`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_adapter_payload.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_phase0_adapter_packet.json`
- `tests/test_arc_bot_runtime_ui_scaffold_adapter.py`
- `phase0_runtime_ui_scaffold/adapter.py`
- `tests/test_arc_bot_runtime_ui_scaffold_render_harness.py`
- `phase0_runtime_ui_scaffold/preview.py`
- `tests/test_arc_bot_runtime_ui_scaffold_preview.py`

## Packet Intent

Arc-Bot-shell defines a fixture-backed, read-only projection adapter shape for the
scaffold surfaces:

- `work_queue`
- `runtime_settings`
- `overview`

The adapter payload is intentionally non-authoritative and must remain phase-gated.
This packet proves only contract shape, scoped surface binding, and explicit runtime
authority blocking.

## What This Packet Proves

- `Work Queue`, `Runtime Settings`, and `Overview` are rendered through a projection adapter contract.
- Surface bindings match the existing Phase-0 contract pack entries.
- Envelopes, schemas, and snapshot references are present for all surfaces.
- Runtime authority actions are blocked by default (`provider_model_calls`, `connector_*`,
  `tool_execution`, `runtime_route_mutation`, `credential_storage`, `customer_system_mutation`).
- Read-only metadata actions are allowed only as notes/readiness scaffolding.
- Guardian spine/read-read sources are documented as future read-only seams:
  `app.services.guardian.suite`, `guardian_spine_tasks`, `guardian_spine_events`,
  `guardian_spine_approvals`, `guardian_spine_projects`.

## What This Packet Does Not Prove

- Live read/write to LIMA Office or LIMA AI OS.
- Live provider/model calls.
- Approval enforcement, live Guardian decisions, evidence persistence, or token routing.
- Connector writes or external sends.
- Worker dispatch, task execution, device/robotic control, or production touch.

## Read-only Boundaries

This phase allows:

- metadata display,
- readiness notes and queue/runtime setup annotations,
- blocked-path visibility with runbook references.

This phase denies:

- connector writes,
- model calls,
- provider token storage,
- runtime-route mutation,
- any execution path without a future phase gate and explicit authority contract.

## Recommended Next Step

Phase-0 render harness is implemented behind an explicit `RUNTIME_UI_Scaffold` phase gate in
`phase0_runtime_ui_scaffold.preview`. It loads
`tests/fixtures/arc_bot_runtime_ui_scaffold_adapter_payload.json` and renders only the approved
surfaces in read-only mode.
