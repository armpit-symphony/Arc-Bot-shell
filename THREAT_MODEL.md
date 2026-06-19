# Arc Bot Shell Threat Model

Date: 2026-06-18
Status: Foundation draft

## Threat Classes

1. **False authority projection**
   Surface incorrectly presents actions as executable.
   - Mitigation: `runtime_authority_blocked`, `runtime_execution_blocked`, read-only projection modes in all seams.

2. **Missing evidence/policy**
   Missing refs leading to softened states.
   - Mitigation: required metadata fields and fail-closed validation.

3. **Connector/tool side-effect leakage**
   Preview path enables real side effects.
   - Mitigation: explicit contract fields set false and gate checks on snapshots.

4. **Cross-surface drift**
   Inconsistent spine bindings and contract references.
   - Mitigation: shared surface contracts and continuity tests.

5. **Evidence tamper/misuse risk**
   Untrusted runtime metadata used as authority.
   - Mitigation: no runtime path in Phase-0; preview-only posture and contract checks.

## Residual Risk

- Fixtures are manually maintained and can drift if contract owners do not update seam tests.
- Cross-repo integration assumptions (`app.services.guardian.suite`) are forward references only.

## Planned Controls for Later Phases

- Signed provenance and immutable event lineage.
- Explicit human approval and bound execution tokens.
- Runtime policy evaluation prior to any dispatch.
