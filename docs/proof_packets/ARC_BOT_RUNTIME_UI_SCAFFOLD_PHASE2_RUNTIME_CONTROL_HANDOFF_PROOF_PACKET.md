# Arc Bot Runtime UI Scaffold Phase-2 Runtime Control Handoff Proof Packet

Date: 2026-06-19
Repository: `armpit-symphony/Arc-Bot-shell`
Branch: `arc-bot-runtime-ui-scaffold-phase2-runtime-control-handoff`
Source commit before branch: `58023ff15448ce6ecdcdf2e9bf1c64d720173b6c`

This packet records the Phase-2 runtime-control handoff seam for
`arc_bot_runtime_ui_scaffold` output to a downstream UI-only control surface.

It is a static proof packet only. It does **not** add runtime authority,
execution dispatch, provider/model calls, connector I/O, worker dispatch,
file mutation, scheduler loops, or any physical-world driver integration.

## Files Reviewed

Arc-Bot-shell evidence reviewed:

- `README.md`
- `docs/ROADMAP.md`
- `docs/OPERATOR_CONSOLE_FOUNDATION.md`
- `docs/contracts/ARC_BOT_OPERATOR_CONSOLE_STATE.md`
- `docs/contracts/schemas/arc_bot_console_state_envelope.schema.json`
- `docs/contracts/schemas/arc_bot_work_queue_state.schema.json`
- `docs/contracts/schemas/arc_bot_runtime_settings_state.schema.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_phase2_runtime_consumer_packet.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_phase2_runtime_control_packet.json`
- `phase0_runtime_ui_scaffold/runtime_consumer.py`
- `phase0_runtime_ui_scaffold/phase2_runtime_control.py`
- `tests/test_arc_bot_runtime_ui_scaffold_runtime_consumer.py`
- `tests/test_arc_bot_runtime_ui_scaffold_phase2_runtime_control.py`
- `tests/test_arc_bot_runtime_ui_scaffold_phase2_runtime_control_packet.py`

## New Files in This Packet

- `tests/fixtures/arc_bot_runtime_ui_scaffold_phase2_runtime_control_packet.json`
- `tests/test_arc_bot_runtime_ui_scaffold_phase2_runtime_control_packet.py`
- `docs/proof_packets/ARC_BOT_RUNTIME_UI_SCAFFOLD_PHASE2_RUNTIME_CONTROL_HANDOFF_PROOF_PACKET.md`

## Packet Intent

Arc-Bot-shell defines a phase-2 runtime-control projection handoff that:

- consumes `build_phase1_runtime_ui_consumer_projection`,
- outputs a read-only UI state handoff envelope in
  `build_phase2_runtime_control_projection`,
- preserves the phase-1 source contract and spine boundaries,
- keeps runtime authority explicitly blocked in all output shapes.

## What This Packet Proves

- The phase-2 control projection remains read-only and cannot be used for execution.
- `source_reference` stays `app.services.guardian.suite`.
- `source_access_mode` remains `read_only`.
- Surface bindings remain exactly `work_queue`, `runtime_settings`, and
  `overview`.
- `spine_sources` and per-surface `spine_sources` remain constrained to
  `guardian_spine_tasks`, `guardian_spine_events`, `guardian_spine_approvals`,
  `guardian_spine_projects`.
- Control payload marks UI handoff posture as read-only and runtime authority as blocked.
- `build_phase2_runtime_control_projection` validates the phase gate and surface projection shape.
- A preview CLI is available:
  `python -m phase0_runtime_ui_scaffold.phase2_runtime_control`.
- No runtime side-effect surface is added in this phase.

## What This Packet Does Not Prove

- No real runtime or control-plane integration.
- No worker dispatch, model execution, or connector writes.
- No production persistence.
- No physical-device or robotics control.

## Recommended Next Step

- Add a bounded downstream UI control consumer that uses
  `phase2_runtime_control_handoff_projection` as an input for gated
  rendering only, with an additional phase authorization before any non-preview
  action path can be introduced.
