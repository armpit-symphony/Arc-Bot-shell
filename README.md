# Arc Harness Shell Release Candidate

Arc Harness Shell is a minimal, local, Guardian-gated worker shell for the Arc/LIMA stack. It is the first credible public baseline for guarded task intake, preview-safe execution, evidence capture, and local operator visibility.

## Arc v0.10 local Ollama milestone

The current integration milestone connects real Guardian-approved local model
preview requests to the installed public LIMA v1.1 harness and its explicit
`loopback_ollama` executor contract. Arc supplies a bounded executor callable;
LIMA validates the Guardian decision and loopback scope before the callable
may issue one non-streaming request to local Ollama. Guardian `decision_id`
lineage is preserved across LIMA input, executor input, result, evidence, and
state. Credentials, cloud fallback, remote endpoints, and external actions
remain disabled.

See [docs/ARC_V0_10_GUARDIAN_LIMA_OLLAMA.md](docs/ARC_V0_10_GUARDIAN_LIMA_OLLAMA.md).

## What Works Now

- Guardian-gated task packet execution through `ArcActionRequest -> GuardianDecision -> harness result`
- Fake runtime preview path for deterministic harness runs
- Deterministic local model preview path for operator-safe draft generation
- Local JSONL task queue with `intake`, `tasks`, `task`, and `run-task`
- Local JSONL run history plus evidence bundle listing
- Health output for Guardian, LIMA import readiness, queue/state presence, and sample availability
- Release smoke path that proves intake -> guarded run -> evidence/state -> blocked external send

## Intentionally Blocked

Arc Harness Shell does not execute live email, calendar, browser, network, device, robotics, credential, or office-system mutation actions. The blocked categories are:

- `external_send`
- `file_write`
- `network_action`
- `device_action`
- `robotics_action`
- `credential_access`
- `office_system_mutation`

## Quickstart

```bash
python -m pip install -e .
python -m compileall arc_bot_shell
python -m arc_bot_shell.health
```

## Task Queue Commands

```bash
python -m arc_bot_shell.console intake samples/tasks/local_model_preview.json
python -m arc_bot_shell.console tasks
python -m arc_bot_shell.console task <task_id>
python -m arc_bot_shell.console run-task <task_id> --runtime fake --model-adapter deterministic
```

## Local Model Preview

```bash
python -m arc_bot_shell.harness run samples/tasks/local_model_preview.json --runtime fake --model-adapter deterministic
```

Explicit local Ollama preview is available only through Guardian and LIMA:

```powershell
$env:ARC_OLLAMA_URL = "http://127.0.0.1:11434"
$env:ARC_OLLAMA_MODEL = "qwen2.5:7b"
python -m arc_bot_shell.harness run `
  samples/tasks/local_model_preview.json `
  --guardian guardian_core `
  --runtime lima `
  --executor ollama
```

The harness and console reject the legacy direct Ollama model-adapter route.

## Local Integration Doctor

Set ARC_GUARDIAN_PATH, ARC_LIMA_PATH, ARC_OLLAMA_URL, and ARC_OLLAMA_MODEL,
then run:

    python -m arc_bot_shell.integrations doctor

The JSON report verifies imports, the LIMA `loopback_ollama` contract, and
loopback Ollama/model reachability. It does not generate model output or grant
runtime authority.

Guardian-only v0.8 proof, stopped before LIMA and Ollama:

```powershell
$env:ARC_GUARDIAN_MODE = "guardian_core"
$env:ARC_GUARDIAN_PATH = "C:\path\to\LIMA-Guardian-Suite"
python -m arc_bot_shell.harness guardian-check samples/tasks/local_model_preview.json
```

The durable Guardian baseline is
`guardian-core-v1.1-local-model-preview-policy`.

## Release Smoke

```bash
python scripts/smoke_arc_harness_release.py
./scripts/smoke_arc_harness_release.sh
./scripts/smoke_arc_harness_release.ps1
```

## Console And Evidence

```bash
python -m arc_bot_shell.console history
python -m arc_bot_shell.console show-run <run_id>
python -m arc_bot_shell.console evidence
python -m arc_bot_shell.console inbox
python -m arc_bot_shell.health
```

## Operator Approval Queue

```bash
python -m arc_bot_shell.console approvals
python -m arc_bot_shell.console approval <approval_id>
python -m arc_bot_shell.console approve <approval_id> --reason "reviewed locally"
python -m arc_bot_shell.console deny <approval_id> --reason "not approved"
```

Approvals and denials are durable local records only. In v0.6, approving a blocked task does not enable external execution.

## Guardian And LIMA Dependency Behavior

- `GuardianFacade.evaluate(request)` always returns a `GuardianDecision`.
- `GuardianCoreAdapter` imports only the public `guardian_core` request, decision, and evaluator contract.
- Explicit `guardian_core` mode fails closed without falling back to a fake allow decision.
- Guardian allow in v0.8 only records eligibility for later LIMA routing; no LIMA or Ollama call occurs.
- `FakeLimaRuntimePort` and `DeterministicPreviewAdapter` require no network or credentials.
- The Ollama HTTP request exists only in the callable injected into
  `execute_v1_live_provider_model_call`; Arc console/queue/harness services do
  not call Ollama directly.
- Ollama endpoints are restricted to HTTP `127.0.0.1` or `localhost` with an
  explicit port. No redirects, credentials, retry endpoint, or cloud fallback
  are allowed.
- `LocalLimaImportRuntimePort` only resolves from `ARC_LIMA_PATH`, `workspace.lock.json`, or an installed `lima` package.
- Missing Guardian or missing LIMA import support fails closed; CI does not require sibling checkouts, Ollama, or network access.

## Safety Boundary

Arc Harness Shell is a preview-safe worker shell. Every consequential path passes through a Guardian decision object before runtime or model execution, and every run writes evidence plus state. There are no hidden background actions.

## Release Guardrails

- Release smoke script: [scripts/smoke_arc_harness_release.py](scripts/smoke_arc_harness_release.py)
- CI workflow: [.github/workflows/guardrails.yml](.github/workflows/guardrails.yml)
- Lock file: [workspace.lock.json](workspace.lock.json)
- Bootstrap script: [scripts/bootstrap_workspace.py](scripts/bootstrap_workspace.py)

## Legacy Context

- Legacy scope-lock context remains in `docs/ROADMAP.md`.
- Phase-0 runtime UI scaffold is locked in the legacy scaffold docs; this branch adds the runnable harness path beside that older material.
- Legacy preview command reference: `python -m phase0_runtime_ui_scaffold.preview`.
- Legacy Guardian reference: `LIMA-Guardian-Suite`.
