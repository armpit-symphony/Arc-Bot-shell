# Arc Bot Shell ADR Log

Date: 2026-06-18
Status: Phase-0 decision log

## ADR-01: Scope to Preview-Only Runtime UI in Phase-0

- **Decision:** Keep Arc Bot Shell runtime UI scaffold read-only and contract-gated.
- **Rationale:** Prevents unchecked action and aligns with LIMA Office control-plane expectations.
- **Implication:** No execution paths in core modules.

## ADR-02: Use Guardian-leaning seam vocabulary

- **Decision:** Reference Guardian/Spine names (`app.services.guardian.suite`, `guardian_spine_*`) as future read seams.
- **Rationale:** Preserve architectural continuity with Sparkbot/LIMA ecosystems.
- **Implication:** No direct runtime implementation now; seam mapping is for future phases.

## ADR-03: Build through fixtures and proof packets

- **Decision:** Use fixture-backed projections with proof packets for every seam milestone.
- **Rationale:** Deterministic verification and regression-safe contracts.
- **Implication:** Every new seam has tests and packet artifacts.

## ADR-04: Fail-closed defaults

- **Decision:** Missing policy/evidence/authority fields default to blocked or rejected seam projection.
- **Rationale:** Prevent silent privilege escalation through malformed input.
- **Implication:** Strict validation in all seam builders.

## ADR-05: Ollama executes only through Guardian and LIMA

- **Decision:** Permit one local-model preview path through a real Guardian
  allow decision, the installed LIMA v1.1 `loopback_ollama` contract, and an
  Arc-supplied HTTP-loopback executor callable.
- **Rationale:** Preserves Guardian syscall-gate authority and LIMA runtime
  validation while completing the local-PC model milestone without creating a
  generic network/provider framework.
- **Implication:** Direct Arc console/queue/harness Ollama adapters are blocked;
  only HTTP `127.0.0.1` or `localhost` endpoints with no credentials, side
  effects, redirects, or fallback are permitted. Exact Guardian `decision_id`
  lineage and sanitized evidence/state are mandatory.

## Decision: stable manager plus selected runtime release

Arc v0.11 uses a stable non-listening manager and an atomic `current/release.json` pointer instead of making the operator depend on a terminal or an elevated Windows service. This keeps per-user startup and lifecycle management available while allowing the runtime to roll back to the exact `arc-harness-shell-v0.10` trust baseline. No execution authority moves into the manager.