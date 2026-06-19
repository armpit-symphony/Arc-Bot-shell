# Arc Bot Shell Phase-0 Roadmap

Date: 2026-06-18
Status: foundation lock

Current branch goal:

- Lock runtime UI scope to Phase-0 preview surfaces only.
- Keep all behavior doc-only and fail-closed.
- Explicitly define where Guardian Spine / LIMA-Guardian-Suite integration will attach in later phases.

## 1) Scope Lock (Runtime UI Scaffold)

Purpose:
Lock down runtime scope for the shell user surface so no action path can infer runtime authority.

### 1.1 Punch list

1. Confirm runtime scope lock
   - [x] The shell is preview/display first in this branch.
   - [x] No live model calls, connector reads/writes, worker dispatch, or file mutations.
   - [x] No provider keys, tokens, or secrets are stored in shell product state.
   - [x] Frontend state is not a source of truth.
2. Lock the two runtime UI targets
   - [x] `Work Queue` listed and defined as preview/state-only.
   - [x] `Runtime Settings` listed and defined as preview/state-only.
   - [x] Surface actions that are blocked by default with explicit reasons.
3. Harden guardrails in docs/contracts
   - [x] Missing metadata forces blocked/review rendering (`fail-closed`).
   - [x] Missing policy refs are a hard block.
   - [x] Missing evidence refs are a hard block.
   - [x] Cross-surface consistency enforced by shared envelope (`tenant_id`, `environment`, `operator_role`, etc.).
4. Align non-authoritative authority references
   - [x] `guardian.decision`, `approval.request`, `approval.token`, and `token.verification` are display-only inputs.
   - [x] `model.route` and `supervisor.health` appear as readiness metadata only.
   - [x] No runtime authority is derived directly in this repo.
5. Add proof scaffolding
   - [x] Fixture packet records scope constraints for both surfaces.
   - [x] Preview contract scaffold is pinned in a stable artifact fixture for downstream consumers.
   - [x] Tests assert scope-lock text, boundary flags, and docs-first posture.
   - [x] `README` includes active phase lock and deferred runtime authority note.

### 1.2 Guardian spine/suite seam plan for Phase-1+

- In Phase 0, Arc-Bot-shell only defines read-only display contracts.
- Future adapter reads are expected from a read-optimized runtime telemetry source:
  - LIMA-Guardian-Suite entrypoint: `app.services.guardian.suite`
  - Guardian Spine sources (read-only): `guardian_spine_tasks`, `guardian_spine_events`, `guardian_spine_approvals`, `guardian_spine_projects`
  - Canonical read event path should map to shell surfaces as metadata only (no execution permission).
- Runtime authority for consequential actions remains out of scope until approved by later phase gates.

### 1.3 Immediate completion criteria

- [x] No runtime behavior has been added.
- [x] Foundation docs and tests explicitly deny provider/model calls and connector actions.
- [x] Work Queue and Runtime Settings are listed as preview-only with no dispatch authority.
- [x] Dependency boundaries are explicit:
  - LIMA-Guardian-Suite: future decision/evidence source
  - LIMA-Guardian-Spine: future read-only state feed
  - LIMA AI OS: future authoritative runtime control plane

### 1.4 Contract-shape scaffolding

- [x] Add initial Phase-0 schema documents for shared console envelope and surface-specific payloads.
- [x] Add preview contract artifact pinning required shared envelope fields and blocked runtime actions.
- [x] Add snapshot fixtures for Work Queue and Runtime Settings.
- [x] Add contract checks that assert no runtime authority in the snapshots.
- [x] Add a single proof-pack fixture that bundles scope lock, schemas, and snapshot references for read-only scaffold handoff.
  - [x] Add a proof-only adapter payload contract for surface read-only projection (`work_queue`, `runtime_settings`).
  - [x] Add a no-execution preview interface for phase-gated projection rendering.
  - [x] Add a phase-1 read-feed runtime-seam projection wrapper for downstream runtime UI consumers.

## 2) Next Milestones (post-scope lock)

- [x] Add mock/read-only contract fixtures for full shell-state envelope.
- [x] Add adapter contract package and proof packet for surface snapshots.
  - [x] Implement a phase-gated read-only render harness from adapter payload (mock-safe).
  - [x] Add read-feed runtime-seam projection helper behind phase gate for preview-only UI handoff.
  - [x] Add runtime-consumer handoff proof and validation for phase-2 transfer continuity.
  - [x] Add migration gate tests so runtime authority cannot appear without guardrail updates.
  - [x] Add a preview interface/entrypoint to render the read-only projection for downstream consumers.

## External Reference Alignment

- Sparkbot reference: `https://github.com/armpit-symphony/Sparkbot`
- Sparkbot shell reference: `https://github.com/armpit-symphony/Sparkbot_shell`
- LIMA-Guardian-Suite reference: `https://github.com/armpit-symphony/LIMA-Guardian-Suite`
- LIMA Office references and contracts remain the operator source of truth for state shaping.
