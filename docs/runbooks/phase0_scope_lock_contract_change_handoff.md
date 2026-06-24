# Phase-0 Scope-Lock Contract Change Handoff

Date: 2026-06-21
Status: active runbook

## Purpose

Use this runbook when a Phase-0 runtime UI scaffold contract, fixture, proof
packet, or projection shape changes.

## Steps

1. Confirm the change is still preview-only.
2. Confirm `runtime_authority_blocked` remains `true`.
3. Confirm `runtime_execution_blocked` remains `true`.
4. Update affected fixtures and proof packets together.
5. Run:
   - `./scripts/scope_lock_guardrails.ps1`
   - `./scripts/phase0_phase1_handoff_guardrails.ps1`
   - `python -m pytest -q`
   - `git diff --check`

## Stop Conditions

Stop and request LIMA Office / Guardian owner input if the change needs:

- signed runtime envelopes,
- approval token issuance,
- connector access,
- local model execution,
- external send authority,
- customer-system mutation,
- worker dispatch.
