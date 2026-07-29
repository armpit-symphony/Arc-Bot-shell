# Arc Harness Shell Release Candidate

Arc Harness Shell is a minimal, local, Guardian-gated worker shell for the
Arc/LIMA stack. Its current control-plane path supports guarded task intake,
non-executing preflight, evidence capture, and local operator visibility.

## LIMA v0.1 governed preflight consumer

Arc includes a non-executing governed preflight path:

`ArcActionRequest -> normalize_for_lima -> lima.runtime.run_governed_request -> GovernedDecision`

The dependency is `lima-runtime==0.1.0rc1`, pinned to LIMA commit
`4e7c648349f0a5a19694ac5f0c57b5cb14dc2b17`. This path is preview/preflight
only. It grants no execution authority and performs no provider, model, tool,
connector, external-send, credential, network, background, robotics, IoT, or
physical-world action.

## LIMA Office worker control plane

Arc also provides an explicit foreground endpoint for authenticated worker
registration, heartbeat, and non-executing assignment acknowledgement. The
boundary starts no hidden service, is loopback-only in the first lab slice,
and never restores the retired `lima.harness` execution API.

The separate-process launcher is `arc-worker-preview`. It accepts its
ephemeral lab channel key only on stdin and never persists or prints the key.

The Arc-centered operator path is `arc-preflight`. It submits one authenticated
request to the foreground LIMA Office Supervisor, displays Guardian, LIMA,
assignment, and evidence metadata, and always stops before execution. The
ephemeral operator key is accepted only on stdin. The first lab Supervisor
transport remains loopback-only.

See [the Arc operator preflight boundary](docs/arc-operator-preflight.md).

See [the authenticated worker control-plane boundary](docs/arc-worker-control-plane.md).

## Retired v0.10 Ollama experiment

The former Guardian -> `lima.harness` -> loopback Ollama experiment is
historical and permanently quarantined. Its retained entry points fail closed
before provider, model, network, credential, tool, connector, or side-effect
activity. The supported path is `lima.runtime.run_governed_request` and stops
at a non-executing governed decision.

See [docs/ARC_V0_10_GUARDIAN_LIMA_OLLAMA.md](docs/ARC_V0_10_GUARDIAN_LIMA_OLLAMA.md).

## What Works Now

- Guardian-gated task packet evaluation through `ArcActionRequest -> GuardianDecision -> harness result`
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

The legacy `lima.harness`, direct Ollama executor, model probe, and completion
smoke are permanently quarantined. They fail closed before model, provider,
tool, connector, credential, filesystem, or network activity. Use the
non-executing Arc governed-preflight path instead.

## Local Integration Doctor

Set ARC_GUARDIAN_PATH, ARC_LIMA_PATH, ARC_OLLAMA_URL, and ARC_OLLAMA_MODEL,
then run:

    python -m arc_bot_shell.integrations doctor

The JSON report verifies the supported Guardian and `lima.runtime` imports and
reports the retired Ollama surface as unavailable. It does not probe a model,
generate output, use network, or grant runtime authority.

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
- Retained direct Ollama adapters, executor helpers, probes, installer flags,
  and smokes fail closed without calling a model process or network.
- `LocalLimaImportRuntimePort` only resolves from `ARC_LIMA_PATH`, `workspace.lock.json`, or an installed `lima` package.
- Missing Guardian or missing LIMA import support fails closed; CI does not require sibling checkouts, Ollama, or network access.

## Safety Boundary

Arc Harness Shell is a preview-safe worker shell. Every consequential path
passes through a Guardian decision and stops before runtime, model, tool, or
side-effect execution. Every run writes evidence plus state. There are no
hidden background actions.

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

## Windows operator installation (v0.11)

Prerequisites: Windows PowerShell 5.1+, Python 3.11+, and Git. Ollama and a
local model are not required for the non-executing control plane. Arc installs
per-user under `%LOCALAPPDATA%\SparkPitLabs\ArcBot` and does not add a firewall
rule or external listener.

```powershell
.\scripts\windows\install-arc.ps1
.\scripts\windows\arc.ps1 start
.\scripts\windows\arc.ps1 status
.\scripts\windows\arc.ps1 submit .\samples\tasks\local_model_preview.json
.\scripts\windows\arc.ps1 history
.\scripts\windows\arc.ps1 startup-enable
.\scripts\windows\arc.ps1 startup-disable
.\scripts\windows\upgrade-arc.ps1 -Tag <approved-tag>
.\scripts\windows\rollback-arc.ps1 -Tag arc-harness-shell-v0.10
.\scripts\windows\uninstall-arc.ps1
```

The installer never invokes or installs Ollama; `-InstallModel` fails closed.
Default uninstall preserves data, evidence, approvals, and logs. Use
`arc.ps1 doctor`, `arc.ps1 health`, `arc.ps1 logs`, or `arc.ps1 diagnostics`
for troubleshooting. See
[docs/ARC_V0_11_WINDOWS_OPERATOR.md](docs/ARC_V0_11_WINDOWS_OPERATOR.md) for
layout, lifecycle, rollback, and security details.
