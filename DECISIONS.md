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
