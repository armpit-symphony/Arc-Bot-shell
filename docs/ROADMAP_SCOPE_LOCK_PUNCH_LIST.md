# Arc Bot Runtime UI Scope Lock - Punch List

Date: 2026-06-19
Status: active

## Phase 0 Objective

Keep the runtime UI as preview-only and prove where future authority may attach
without wiring it in this phase.

## Scope Lock Checklist

### 1) Runtime UI lock posture

- [x] Declare scope in docs as read-only/operator-display only.
  - Evidence: `docs/ROADMAP.md`, `docs/OPERATOR_CONSOLE_FOUNDATION.md`,
    `README.md`.
- [x] Explicitly deny live model calls, connector writes, worker dispatch,
  and task/customer-system mutation in phase-0 behavior and contracts.
  - Evidence: `docs/contracts/schemas/*.json`, `tests/test_arc_bot_runtime_ui_scaffold_contracts.py`,
    `docs/ROADMAP.md`.
- [x] Keep no frontend or local storage source-of-truth claims.
  - Evidence: `docs/OPERATOR_CONSOLE_FOUNDATION.md`.

### 2) Seams and read path

- [x] Keep `app.services.guardian.suite` as the read reference point for future seam.
  - Evidence: `tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_contract.json`,
    `tests/fixtures/arc_bot_runtime_ui_scaffold_phase1_read_feed_payload.json`.
- [x] Restrict seam tables to read-only guardian spine sources:
  `guardian_spine_tasks`, `guardian_spine_events`,
  `guardian_spine_approvals`, `guardian_spine_projects`.
  - Evidence: fixture payload + validators in
    `phase0_runtime_ui_scaffold/guardian_suite_seam.py` and
    `tests/test_arc_bot_runtime_ui_scaffold_guardian_suite_seam.py`.
- [x] Add phase-gate enforcement (`RUNTIME_UI_SCAFFOLD_PHASE1_FEED`)
  on guardian-suite seam and read-feed inputs.
  - Evidence: seam parser + tests + CLI tests.

### 3) Tooling and visibility

- [x] Add seam fixture + seam projection helper + CLI preview.
  - Evidence: `tests/fixtures/arc_bot_guardian_suite_spine_payload.json`,
    `phase0_runtime_ui_scaffold/guardian_suite_seam.py`,
    `tests/test_arc_bot_runtime_ui_scaffold_guardian_suite_seam.py`.
- [x] Add optional phase-chain opt-in for seam summary.
  - Evidence: `phase0_runtime_ui_scaffold/phase_chain.py`,
    `tests/test_arc_bot_runtime_ui_scaffold_phase_chain.py`.
- [x] Document the new seam in proof artifacts.
  - Evidence: `docs/proof_packets/ARC_BOT_RUNTIME_UI_SCAFFOLD_PHASE0_GUARDIAN_SUITE_SEAM_PROOF_PACKET.md`,
    `README.md`.

## Open/Next Items (this phase)

- [x] Add a one-shot artifact fixture for the full phase-chain + seam output
  to make handoff to downstream seams deterministic.
- [x] Add a phase-0 scope-lock status snapshot test that compares
  `phase_chain`/`phase1`/`phase2` outputs in a single assertion file.
- [x] Add a small execution checklist in project docs for the next operator who
  inherits this phase boundary.
- [x] Add deterministic status snapshot export path support for fixture refresh.

## Phase-0 Operator Checklist

- [x] Confirm the phase-chain plus phase-1/phase-2 status snapshot fixture passes
  (`arc_bot_runtime_ui_scaffold_phase0_scope_lock_status_snapshot.json`).
- [x] Before starting any runtime-control integration work, re-run:
  - `python -m pytest -q tests/test_arc_bot_runtime_ui_scaffold_phase_chain.py`
  - `python -m pytest -q tests/test_arc_bot_runtime_ui_scaffold_guardian_suite_seam.py`
  - `python -m pytest -q tests/test_arc_bot_phase0_scope_lock_runtime_ui.py`
- [x] Keep `source_reference` fixed to `app.services.guardian.suite`
  and all `runtime_*_blocked` flags true in all preview/control outputs
  (`tests/test_arc_bot_runtime_ui_scaffold_phase_chain.py`).
- [ ] If a phase contract changes, update both:
  - `tests/fixtures/arc_bot_runtime_ui_scaffold_phase0_scope_lock_chain_packet.json`
  - `tests/fixtures/arc_bot_runtime_ui_scaffold_phase0_scope_lock_status_snapshot.json`
  before downstream handoff.

## Phase-0 Scope Lock (This Turn)

- [x] Confirm all source references resolve to `app.services.guardian.suite` with
  `read_only` access mode.
- [x] Confirm all runtime/action surfaces are preview-only (`overview`,
  `work_queue`, `runtime_settings`).
- [x] Confirm no connector writes, model calls, worker dispatch, or persistence
  behavior exists in this phase.
- [x] Confirm deterministic proof artifacts and one-shot tests are present.

## Exit Criteria for Scope Lock

- [x] Scope lock language and gates exist in docs, contracts, and projections.
- [x] No runtime authority is enabled in projection outputs.
- [x] Seams are present only as read-only, fail-closed fixtures with explicit
  off-by-default stage-inclusion behavior in phase-chain.
- [x] Deterministic full-chain handoff artifact exists.
