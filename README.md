# Arc Harness Shell v0.4

Arc Harness Shell v0.4 is a minimal, local, Guardian-gated harness path for the Arc/LIMA stack.

It supports three preview-safe paths from a clean clone:

- `ArcActionRequest -> GuardianFacade -> GuardianDecision -> LimaRuntimePort -> EvidenceBundle -> CLI result`
- `ArcActionRequest -> GuardianFacade -> GuardianDecision -> LocalModelPreviewAdapter -> EvidenceBundle -> CLI result`
- `Task intake -> local task queue -> Guardian-gated harness run -> EvidenceBundle -> state/history`

It is a harness shell, not a full office bot.

## What It Is

- A narrow Arc request runner with explicit contracts.
- A Guardian-first decision path for every consequential request.
- A deterministic fake LIMA runtime for tests and smoke runs.
- A deterministic local model preview adapter for clean-clone drafting.
- A local evidence bundle writer, JSONL state record, and JSONL task queue for every CLI run.
- A config-driven path for future LIMA imports through `ARC_LIMA_PATH`, `workspace.lock.json`, or an installed `lima` package.

## What It Is Not

- Not a live office automation worker.
- Not a browser, email, calendar, network, device, robotics, or file-mutation executor.
- Not a credential handler.
- Not a hidden background service.
- Not a sibling-folder auto-import hack.

## Smoke Commands

```bash
python -m arc_bot_shell.harness run samples/tasks/preview_summary.json --runtime fake
python -m arc_bot_shell.harness run samples/tasks/external_email_send.json --runtime fake
python -m arc_bot_shell.harness run samples/tasks/local_model_preview.json --runtime fake --model-adapter deterministic
python -m arc_bot_shell.console intake samples/tasks/local_model_preview.json
python -m arc_bot_shell.console tasks
python -m arc_bot_shell.health
```

Expected behavior:

- `preview_summary.json`: Guardian returns `allowed_preview_only`, fake runtime runs, evidence bundle is written, exit code `0`.
- `external_email_send.json`: Guardian returns `blocked`, runtime is not called, evidence bundle is written, exit code `2`.
- `local_model_preview.json`: Guardian returns `allowed_preview_only`, deterministic preview runs, evidence and state are written, exit code `0`.
- `console intake`: queues a task record without executing it.

## Guardian And LIMA Behavior

- `GuardianFacade.evaluate(request)` always returns a `GuardianDecision`.
- `GuardianSuiteAdapter` only attempts `LIMA-Guardian-Suite` through the public `app.services.guardian` entrypoint.
- If Guardian Suite is missing or unusable, the facade falls back to `FailClosedGuardian`.
- `FakeLimaRuntimePort` is deterministic and side-effect free.
- `DeterministicPreviewAdapter` is deterministic and side-effect free.
- `LocalLimaImportRuntimePort` only loads `lima.adapters` from:
  1. `ARC_LIMA_PATH`
  2. `workspace.lock.json`
  3. an installed `lima` package
- Missing or unusable LIMA fails closed through `DisabledLimaRuntimePort` or a controlled runtime-unavailable result.
- Optional Ollama preview use remains explicit and controlled through `--model-adapter ollama` or `ARC_MODEL_ADAPTER=ollama`.

## Blocked Categories

- `external_send`
- `file_write`
- `network_action`
- `device_action`
- `robotics_action`
- `credential_access`
- `office_system_mutation`

## Reproducibility

- Lock file: `workspace.lock.json`
- Bootstrap script: `python scripts/bootstrap_workspace.py`
- CI workflow: `.github/workflows/guardrails.yml`
- Legacy scope-lock context remains in `docs/ROADMAP.md`.
- Phase-0 runtime UI scaffold is locked in the legacy scaffold docs; this branch adds the runnable harness path beside that older material.
- Legacy preview command reference: `python -m phase0_runtime_ui_scaffold.preview`.
- Legacy Guardian reference: `LIMA-Guardian-Suite`.

## Console/State Commands

```bash
python -m arc_bot_shell.console history
python -m arc_bot_shell.console show-run <run_id>
python -m arc_bot_shell.console evidence
python -m arc_bot_shell.console inbox
```

## Task Queue Commands

```bash
python -m arc_bot_shell.console intake samples/tasks/local_model_preview.json
python -m arc_bot_shell.console tasks
python -m arc_bot_shell.console task <task_id>
python -m arc_bot_shell.console run-task <task_id> --runtime fake --model-adapter deterministic
```
