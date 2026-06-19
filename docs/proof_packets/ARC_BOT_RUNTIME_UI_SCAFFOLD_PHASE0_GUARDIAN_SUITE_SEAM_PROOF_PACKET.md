# Arc Bot Runtime UI Scaffold Phase-0 Guardian Suite Seam Proof Packet

Date: 2026-06-19
Repository: `armpit-symphony/Arc-Bot-shell`
Branch: `arc-bot-runtime-ui-scaffold-foundation-phase-chain`

This packet records the Phase-0 Guardian Suite seam scaffold for
fixture-backed `app.services.guardian.suite` read-only spine input.

It is a static proof packet only. It does **not** add live model calls,
connector reads/writes, worker dispatch, or runtime execution.

## Files Reviewed

Arc-Bot-shell evidence reviewed:

- `README.md`
- `docs/ROADMAP.md`
- `docs/OPERATOR_CONSOLE_FOUNDATION.md`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_contract_pack.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json`
- `tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json`
- `tests/fixtures/arc_bot_guardian_suite_spine_payload.json`
- `tests/test_arc_bot_runtime_ui_scaffold_phase_chain.py`
- `tests/test_arc_bot_runtime_ui_scaffold_guardian_suite_seam.py`
- `phase0_runtime_ui_scaffold/guardian_suite_seam.py`
- `phase0_runtime_ui_scaffold/phase_chain.py`
- `phase0_runtime_ui_scaffold/__init__.py`

New files in this packet:

- `tests/fixtures/arc_bot_guardian_suite_spine_payload.json`
- `tests/test_arc_bot_runtime_ui_scaffold_guardian_suite_seam.py`
- `phase0_runtime_ui_scaffold/guardian_suite_seam.py`
- `docs/proof_packets/ARC_BOT_RUNTIME_UI_SCAFFOLD_PHASE0_GUARDIAN_SUITE_SEAM_PROOF_PACKET.md`

## Packet Intent

Arc-Bot-shell defines a Phase-0 read-only guardian-suite seam projection to keep the
runtime UI scaffold bounded to preview-only behavior.

The seam consumes a fixture payload from
`app.services.guardian.suite` and validates:

- phase gate enforcement,
- read-only source mode,
- exact spine source list,
- record shape and required identifier fields,
- missing runtime authority,
- source alignment with existing read-feed contract surfaces.

## What This Packet Proves

- New fixture-backed seam module exists and exports fail-closed validation APIs:
  - `build_guardian_suite_seam_projection`
  - `run_guardian_suite_seam_preview`
  - dedicated errors:
    - `GuardianSuitePayloadError`
    - `GuardianSuiteGateError`
- The seam enforces `phase = "phase-1"` and requires:
  - `source_reference = "app.services.guardian.suite"`
  - `source_access_mode = "read_only"`
  - `projection_scope = "read_only"`
  - `runtime_authority_enabled = false`
  - enabled and matching phase gate (`RUNTIME_UI_SCAFFOLD_PHASE1_FEED`)
- Required spine sources are validated to exactly:
  - `guardian_spine_tasks`
  - `guardian_spine_events`
  - `guardian_spine_approvals`
  - `guardian_spine_projects`
- Required per-record fields are validated for spine source records (`surface` + ID + `updated_at`).
- The phase-chain preview path can include the guardian-suite seam as an explicit opt-in stage
  via `--with-guardian-suite-seam`.

## What This Packet Does Not Prove

- No live Guardian-spine execution or writeback.
- No live model/model-provider calls.
- No connector/OAuth/file/tool execution in Phase-0.
- No runtime authority handoff implementation beyond static read-only projection checks.

## Recommended Next Step

Run `python -m phase0_runtime_ui_scaffold.phase_chain --with-guardian-suite-seam --compact`
to produce an end-to-end projection artifact including the guardian-suite seam summary and
continue downstream planning toward runtime-control handoff tests.
