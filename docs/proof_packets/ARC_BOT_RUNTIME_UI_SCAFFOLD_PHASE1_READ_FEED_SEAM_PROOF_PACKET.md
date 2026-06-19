# Arc Bot Runtime UI Scaffold Phase-1 Read-Feed Seam Proof Packet

Date: 2026-06-19
Repository: `armpit-symphony/Arc-Bot-shell`
Branch: `arc-bot-runtime-ui-scaffold-phase1-read-feed-seam`
Source commit before branch: `37af88ce94ade29cb2d3f97489e62ee423788d4d`

This packet records the Phase-1 read-feed seam contract scaffold for
`app.services.guardian.suite` + read-only Guardian Spine feeds.

It is a static proof packet only. It does **not** add runtime wiring,
live model routing, provider calls, connector I/O, worker dispatch, or any live
tool/automation actions.

## Files Reviewed

Arc-Bot-shell evidence reviewed:

- `README.md`
- `docs/ROADMAP.md`
- `docs/OPERATOR_CONSOLE_FOUNDATION.md`
- `docs/contracts/ARC_BOT_OPERATOR_CONSOLE_STATE.md`
- `docs/contracts/schemas/arc_bot_console_state_envelope.schema.json`
- `docs/contracts/schemas/arc_bot_work_queue_state.schema.json`
- `docs/contracts/schemas/arc_bot_runtime_settings_state.schema.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_contract_pack.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_preview_contract.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json`
- `tests/fixtures/arc_bot_phase0_work_queue_state_snapshot.json`
- `tests/fixtures/arc_bot_phase0_runtime_settings_state_snapshot.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_adapter_payload.json`
- `tests/test_arc_bot_runtime_ui_scaffold_read_feed.py`
- `tests/test_arc_bot_runtime_ui_scaffold_phase1_read_feed_packet.py`
- `tests/test_arc_bot_runtime_ui_scaffold_phase1_read_feed_preview.py`
- `tests/test_arc_bot_runtime_ui_scaffold_phase1_read_feed_ingest.py`
- `phase0_runtime_ui_scaffold/read_feed.py`

New files in this packet:

- `docs/proof_packets/ARC_BOT_RUNTIME_UI_SCAFFOLD_PHASE1_READ_FEED_SEAM_PROOF_PACKET.md`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_packet.json`
- `tests/test_arc_bot_runtime_ui_scaffold_phase1_read_feed_packet.py`
- `tests/test_arc_bot_runtime_ui_scaffold_phase1_read_feed_preview.py`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json`
- `tests/test_arc_bot_runtime_ui_scaffold_phase1_read_feed_ingest.py`
- `phase0_runtime_ui_scaffold/read_feed.py`

## Packet Intent

Arc-Bot-shell defines a Phase-1 read-feed seam scaffold that is explicitly
read-only and preview-oriented for:

- `Work Queue`
- `Runtime Settings`

The feed contract is intended to be consumed by later UI/runtime integration only
after a new phase gate is satisfied.

## What This Packet Proves

- The read-feed contract for Phase-1 is bounded to:
  - `source_reference`: `app.services.guardian.suite`
  - `source_access_mode`: `read_only`
  - read-only spine sources:
    `guardian_spine_tasks`, `guardian_spine_events`, `guardian_spine_approvals`,
    `guardian_spine_projects`
- `work_queue` and `runtime_settings` surface projections are declared and
  normalized by `build_phase1_read_feed_projection`.
- `build_phase1_read_feed_runtime_projection` materializes those surfaces from a
  read-feed payload.
- Projection ingest validates runtime-authority blocks and expected spine sources.
- Projection metadata requires hard policy/evidence/runbook refs.
- Runtime authority actions remain blocked and out-of-scope for this phase:
  `provider_model_calls`, `connector_reads`, `connector_writes`,
  `tool_execution`, `runtime_route_mutation`, `credential_storage`.
- The read-feed seam is constrained to static/read-only state projection evidence
  and references current preview contract anchor artifacts for downstream traceability.

## What This Packet Does Not Prove

- Live guardian-spine execution or writeback.
- Live model/tool/connector/runtime authority.
- LIMA runtime ownership, worker dispatch, or production mutation.
- Live approval enforcement.
- Evidence persistence or raw runtime event durability inside Arc-Bot-shell.

## Recommended Next Step

Phase-1 projection ingestion is now implemented behind `RUNTIME_UI_SCAFFOLD_PHASE1_FEED`
using `app.services.guardian.suite` read-only fixture payloads.
The next move is a separate runtime-consuming seam for phase-2 work with preserved gates.

- Work Queue (`task.execution`, `guardian.decision`, `approval.*`, `token.*` family)
- Runtime Settings (`model.route`, `supervisor.health`, `worker.lifecycle`)

Any future Phase-2 movement must preserve the read-only metadata discipline and
only add execution authority through additional approved gates and contracts.
