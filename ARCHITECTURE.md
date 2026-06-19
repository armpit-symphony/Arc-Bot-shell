# Arc Bot Shell Architecture (Phase-0)

Date: 2026-06-18
Status: Foundation architecture only

## 1) Purpose

Arc Bot Shell is the operator-facing surface for small-business deployment around LIMA Office.
In Phase-0, it is a **read-only governance UI scaffold** and must not execute work.

## 2) Core Layers

- **State Sources (read-only in this phase)**
  - Adapter payload snapshots (`tests/fixtures/*_snapshot.json`).
  - Preview contracts (`tests/fixtures/arc_bot_runtime_ui_scaffold_*_contract.json`).
  - Spine source metadata in fixtures (read-only references).

- **Projection Layers (implemented as pure functions)**
  - `phase0_runtime_ui_scaffold.adapter`
  - `phase0_runtime_ui_scaffold.read_feed`
  - `phase0_runtime_ui_scaffold.runtime_consumer`
  - `phase0_runtime_ui_scaffold.phase2_runtime_control`
  - `phase0_runtime_ui_scaffold.runtime_control_consumer`
  - `phase0_runtime_ui_scaffold.phase_chain`

- **Surface Rendering Targets**
  - `work_queue`
  - `runtime_settings`
  - `overview`

## 3) Trust Boundaries

- Runtime authority may not be inferred from preview payloads.
- No direct model/tool/connector/file/network execution paths are implemented.
- Future execution paths must route through:
  - Guardian decision/approval systems,
  - LIMA-Guardian-Suite (`app.services.guardian.suite`),
  - explicit runtime authorities and evidence lineage gates.

## 4) Data Flow (Phase-0)

```text
fixture contract -> fixture payload -> phase-1 read-feed projection
                -> phase-1 runtime consumer projection
                -> phase-2 control handoff
                -> phase-2 control consumer seam
```

All steps are deterministic and fail-closed when required metadata, policy references, or evidence refs are missing.

## 5) Non-Goals (Phase-0)

- No live model/provider calls.
- No connector mutation.
- No worker dispatch.
- No filesystem/network side effects from shell runtime modules.

## 6) Next architecture direction (post Phase-0)

- Add remaining operator surfaces in a phased read-only expansion.
- Introduce validated adapter-to-runtime handoff only after contract and threat-model gates.
- Keep output contracts stable and versioned through proof packets.
