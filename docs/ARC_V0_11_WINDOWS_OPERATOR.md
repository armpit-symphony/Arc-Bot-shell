# Arc v0.11 Windows operator layer

Arc v0.11 is an operator-experience layer over the tagged v0.10 runtime. It
does not change Guardian policy, LIMA executor authority, connector access, or
the loopback-only Ollama boundary.

## Architecture

The installation separates a stable per-user manager from the selected Arc
runtime release:

```text
PowerShell launcher
  -> stable Arc manager process (no network listener)
  -> selected release public CLI
  -> task queue
  -> real Guardian
  -> published LIMA Runtime
  -> loopback_ollama executor
  -> localhost Ollama
  -> evidence/state/history under the install data directory
```

The manager opens no HTTP port. It maintains a token-bound PID file, writes a
periodic health snapshot, and responds to an authenticated local stop-request
file. It never terminates arbitrary Python or Ollama processes.

The active release is selected by `current/release.json`. The manager remains
available when the selected runtime is rolled back to
`arc-harness-shell-v0.10`.

## Per-user layout

The default root is `%LOCALAPPDATA%\SparkPitLabs\ArcBot`.

```text
app/       initial installed release
venv/      stable manager environment
data/      task queue, approvals, evidence, state, diagnostics, PID state
logs/      install, service, operator, upgrade, rollback, uninstall logs
config/    sanitized configuration and installation manifest
releases/  isolated upgrade and rollback targets
current/   atomic active-release pointer
backups/   failed or superseded staging material
manager/   installed PowerShell launcher scripts
```

Generated operator data is outside the Git checkout and is preserved across
upgrade, rollback, and default uninstall.

## Security invariants

- Guardian remains mandatory for every model call.
- Ollama is invoked only by the LIMA `loopback_ollama` executor.
- Only `http://127.0.0.1:<port>` or `http://localhost:<port>` is accepted.
- The Arc manager has no listener and creates no firewall exception.
- Startup is a current-user Task Scheduler entry without highest privileges.
- No credentials or private environment dumps are stored.
- Diagnostics exclude task payloads, evidence bodies, raw prompts, and model
  output.
- Model installation requires the explicit `-InstallModel` flag.
- Uninstall preserves data unless `-RemoveData` is explicitly requested.
- Upgrade failure restores the previous release pointer before restarting.

## Operator commands

```powershell
.\scripts\windows\install-arc.ps1
.\scripts\windows\arc.ps1 start
.\scripts\windows\arc.ps1 status
.\scripts\windows\arc.ps1 submit .\samples\tasks\local_model_preview.json
.\scripts\windows\arc.ps1 history
.\scripts\windows\arc.ps1 evidence
.\scripts\windows\arc.ps1 doctor
.\scripts\windows\arc.ps1 diagnostics
.\scripts\windows\arc.ps1 startup-enable
.\scripts\windows\arc.ps1 startup-disable
.\scripts\windows\arc.ps1 stop
```

Upgrade requires an explicit release tag:

```powershell
.\scripts\windows\upgrade-arc.ps1 -Tag <approved-tag>
```

The audited rollback anchor is:

```powershell
.\scripts\windows\rollback-arc.ps1 -Tag arc-harness-shell-v0.10
```

Safe uninstall preserves data:

```powershell
.\scripts\windows\uninstall-arc.ps1
```

Permanent data removal requires `-RemoveData` and an explicit confirmation
unless the operator also supplies an automation-oriented force flag.

## Acceptance

`scripts/windows/smoke-arc-windows-operator.ps1` installs into a unique
temporary root, uses mocked Task Scheduler state, runs one real local preview,
proves external email remains denied before execution, checks failed-upgrade
recovery, verifies the v0.10 rollback anchor, and confirms uninstall preserves
data. It never changes a production Arc installation.
