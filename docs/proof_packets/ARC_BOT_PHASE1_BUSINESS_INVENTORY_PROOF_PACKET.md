# Arc Bot Phase-1 Business Inventory Proof Packet

Date: 2026-06-19
Status: Phase-1 planning artifact

## Objective

Establish a read-only, contract-driven Phase-1 business shell inventory before
runtime control is introduced.

- Bot role/persona templates are defined.
- Task model, execution modes, and risk tiers are defined.
- Surface-level runtime constraints and blocked runtime actions are defined.
- Inventory projection is fixture-backed and emits deterministic output.

## Evidence

- Contract fixture:
  - `tests/fixtures/arc_bot_phase1_business_inventory.json`
- Projection tests:
  - `tests/test_arc_bot_phase1_business_shell_inventory.py`
- Runtime status:
  - `python -m pytest -q tests/test_arc_bot_phase1_business_shell_inventory.py`
- CLI preview command:
  - `python -m phase1_business_shell_inventory.inventory --compact`

## Validation Checks

- Inventory contract is validated with:
  - `artifact_type == phase1_business_shell_inventory_contract`
  - exact surface set of planning surfaces
  - all role templates include required fields
  - all surface definitions block runtime authority/execution
  - required phase gate is enforced
- Projection is fail-closed for malformed fixtures through `InventorySchemaError` / `InventoryPhaseGateError`.

## Status

- Phase-1 inventory projection now exists in read-only form and is deterministic.
- This is still planning documentation and does not add runtime execution paths.
