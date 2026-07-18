# Arc v0.9 Real LIMA Runtime Adapter

Arc v0.9 proves the bounded runtime chain:

`ArcActionRequest -> real Guardian allow -> installed LIMA harness -> in-process fake executor -> Arc result/evidence/state`

The milestone stops before Ollama and every external provider or network call.

## Pinned contracts

- Guardian: `guardian-core-v1.1-local-model-preview-policy` at
  `69e843218c521b913edcec404dea6b7be8c64f06`.
- LIMA Runtime: `lima-runtime-v1-arc-consumer-baseline` at
  `cd40f486be19e01026d293b374b99d213ca275d9`.
- Public LIMA import:
  `from lima.harness import execute_v1_live_provider_model_call`.

The package dependency uses the tagged Git reference. The workspace lock does
not require a sibling LIMA checkout path.

## Execution boundary

`LimaRuntimeAdapter` accepts only `arc.local_model_preview` requests that are
preview-only and carry a Guardian decision with:

- a non-empty Guardian-generated `decision_id`;
- Arc status `allowed_preview_only` and Guardian status `allow`;
- `allowed=true`;
- `requires_approval=false`.

Every other condition fails before LIMA or the executor is called. LIMA then
validates the same decision and calls only `in_process_fake_executor`.

The result, evidence bundle, and state record preserve the exact Guardian
decision ID and record the LIMA adapter, public entrypoint, pinned reference,
executor call, result status, network use, credential use, and
`ollama_called=false`.

## CLI proof

```powershell
python -m arc_bot_shell.harness run `
  samples/tasks/local_model_preview.json `
  --guardian guardian_core `
  --guardian-path ..\LIMA-Guardian-Suite `
  --runtime lima `
  --executor fake
```

The external-email sample remains denied and records `lima_called=false`,
`executor_called=false`, `network_called=false`, and `ollama_called=false`.

## Boundaries

Arc v0.9 does not add Ollama, cloud providers, credentials, external
connectors, browser/file/device/robotics actions, production execution, or
hidden background work. Explicit LIMA mode fails closed if the installed public
import is unavailable or incompatible.
