# Arc Bot Phase-0 Scope Lock Punch List

Date: 2026-06-21
Status: compatibility handoff

This file preserves the README-advertised Phase-0 punch-list path. The canonical
runtime UI scope-lock punch list remains:

- `docs/ROADMAP_SCOPE_LOCK_PUNCH_LIST.md`

## Phase-0 Lock Summary

- Arc Bot Shell remains preview-only.
- Runtime authority remains blocked.
- Runtime execution remains blocked.
- `app.services.guardian.suite` is a future read reference only.
- No model calls, connector actions, worker dispatch, file mutation, or customer
  system mutation are authorized from this repo.

## Required Checks

- `python -m pytest -q tests/test_arc_bot_runtime_ui_scaffold_phase_chain.py`
- `python -m pytest -q tests/test_arc_bot_runtime_ui_scaffold_guardian_suite_seam.py`
- `python -m pytest -q tests/test_arc_bot_phase0_scope_lock_runtime_ui.py`
- `./scripts/scope_lock_guardrails.ps1`

## Handoff Rule

Any change to Phase-0 scope-lock fixtures must update both the canonical
scope-lock punch list and the fixture parity tests before downstream handoff.
