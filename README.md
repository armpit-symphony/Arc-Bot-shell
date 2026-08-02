# Arc Harness Shell Release Candidate

Arc Harness Shell is a minimal, local, Guardian-gated worker shell for the
Arc/LIMA stack. Its current control-plane path supports guarded task intake,
non-executing preflight, evidence capture, and local operator visibility.

## Start here

Arc is one of four repositories. It is the **worker shell and operator
client** — the only component in the stack that can perform a side effect, and
only when handed a grant it has been independently opted in to honour.

- The stack, the request flow, and which LIMA commit each consumer pins:
  [LIMA-AI-OS `docs/GOVERNED_STACK_MAP.md`](https://github.com/armpit-symphony/LIMA-AI-OS/blob/main/docs/GOVERNED_STACK_MAP.md)
- Running Arc against a real Supervisor: [docs/RUNNING_THE_LAB.md](docs/RUNNING_THE_LAB.md)
- Moving a dependency pin: [docs/DEPENDENCY_PIN_LOCK.md](docs/DEPENDENCY_PIN_LOCK.md)

The model is **LIMA decides, shells execute.** A governed decision can never
authorize execution. Permission arrives separately, as a short-lived
single-use grant, and even a valid grant does nothing unless Arc was started
with its own execution opt-in. Arc cannot enable itself from the Supervisor
side, and the Supervisor cannot enable Arc.

Arc's LIMA pin is deliberately **frozen** at the v0.1 RC1 public API freeze
and is intentionally older than the commit Lima-Office tracks. That is not
drift. Arc consumes grants as JSON off the wire and imports nothing from
`lima`, so it does not need a newer kernel.

## LIMA v0.1 governed preflight consumer

Arc includes a non-executing governed preflight path:

`ArcActionRequest -> normalize_for_lima -> lima.runtime.run_governed_request -> GovernedDecision`

The dependency is `lima-runtime==0.1.0rc1`, pinned to LIMA commit
`40d6f1379284931ee46f05650e9201d6f98975d6`. This path is preview/preflight
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
- Authenticated worker control plane and operator preflight against a LIMA Office Supervisor
- Honouring a Supervisor execution grant for one read-only capability, behind Arc's own opt-in

## Granted Execution

`document_read` is the only capability Arc will act on, and it needs all of:

1. A valid, unexpired, single-use grant issued by the Supervisor.
2. `--execute-granted-capability` passed to `arc-preflight`. Off by default.
3. `--document-root` pointing at the directory a read may come from. There is
   no default, so without it nothing can be read.

Arc derives the expected capability from the action it submitted and compares
that against the grant, rather than reading the capability back off the grant.
A grant naming something Arc did not ask for is refused with
`execution_grant_binding_mismatch`. Path containment is resolved before the
check, reads are capped at 1 MB, and Arc returns byte counts and identifiers —
never document content.

Every refusal is reported with a reason code rather than raised, so the
preflight result still prints.

## Intentionally Blocked

Outside a valid grant for the capability above, Arc Harness Shell does not
execute live email, calendar, browser, network, device, robotics, credential,
or office-system mutation actions. The blocked categories are:

- `external_send`
- `file_write`
- `network_action`
- `device_action`
- `robotics_action`
- `credential_access`
- `office_system_mutation`

## Quickstart

This repository needs its own virtual environment. It pins `lima-runtime` to a
commit Lima-Office does not, so a shared interpreter silently gives one of the
two repositories the wrong runtime — see [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md).

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e . pytest    # .venv/bin/python elsewhere
.venv/Scripts/python scripts/check-stack-pins.py --check-installed
.venv/Scripts/python -m compileall arc_bot_shell
.venv/Scripts/python -m arc_bot_shell.health
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
