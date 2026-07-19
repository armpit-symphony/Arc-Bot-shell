[CmdletBinding()]
param(
    [string]$InstallRoot,
    [switch]$KeepArtifacts
)

$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$guardianPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "..\LIMA-Guardian-Suite"))
if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("SparkPitLabs\ArcBot-v0.11-smoke-" + [guid]::NewGuid().ToString("N"))
}
$InstallRoot = [System.IO.Path]::GetFullPath($InstallRoot)
$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
if (-not $InstallRoot.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Windows operator smoke must use a temporary install root."
}
$previewTask = Join-Path $repoRoot "samples\tasks\local_model_preview.json"
$emailTask = Join-Path $repoRoot "samples\tasks\external_email_send.json"
$installScript = Join-Path $repoRoot "scripts\windows\install-arc.ps1"
$sourceLauncher = Join-Path $repoRoot "scripts\windows\arc.ps1"
$rollbackScript = Join-Path $repoRoot "scripts\windows\rollback-arc.ps1"
$upgradeScript = Join-Path $repoRoot "scripts\windows\upgrade-arc.ps1"
$uninstallScript = Join-Path $repoRoot "scripts\windows\uninstall-arc.ps1"
$model = $(if ([string]::IsNullOrWhiteSpace($env:ARC_OLLAMA_MODEL)) { "qwen2.5:7b" } else { $env:ARC_OLLAMA_MODEL })
$ollamaUrl = $(if ([string]::IsNullOrWhiteSpace($env:ARC_OLLAMA_URL)) { "http://127.0.0.1:11434" } else { $env:ARC_OLLAMA_URL })

function Convert-ArcOutputToJson {
    param([Parameter(Mandatory = $true)]$Lines)
    $text = ($Lines | ForEach-Object { $_.ToString() }) -join "`n"
    return $text | ConvertFrom-Json
}

try {
    $installOutput = & $installScript `
        -InstallRoot $InstallRoot `
        -Model $model `
        -OllamaUrl $ollamaUrl `
        -RegisterStartup `
        -NonInteractive `
        -SourcePath $repoRoot `
        -GuardianPath $guardianPath `
        -TestMode
    if ($LASTEXITCODE -ne 0) {
        throw "Temporary Arc installation failed."
    }
    $manifestPath = Join-Path $InstallRoot "config\installation-manifest.json"
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "Installation manifest was not written."
    }
    $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
    if ($manifest.guardian_tag -ne "guardian-core-v1.1-local-model-preview-policy") {
        throw "Guardian pin changed during installation."
    }
    if ($manifest.lima_tag -ne "lima-runtime-v1.1-loopback-ollama-executor") {
        throw "LIMA pin changed during installation."
    }

    $secondInstall = & $installScript `
        -InstallRoot $InstallRoot `
        -Model $model `
        -OllamaUrl $ollamaUrl `
        -NonInteractive `
        -SourcePath $repoRoot `
        -GuardianPath $guardianPath `
        -TestMode
    if ($LASTEXITCODE -ne 0) {
        throw "Idempotent installer rerun failed."
    }

    $start = Convert-ArcOutputToJson (& $sourceLauncher start -InstallRoot $InstallRoot -TestMode)
    if ($start.running -ne $true) {
        throw "Arc managed service did not start."
    }
    $status = Convert-ArcOutputToJson (& $sourceLauncher status -InstallRoot $InstallRoot -TestMode)
    if ($status.service.running -ne $true) {
        throw "Arc status did not report a running service."
    }
    if ($status.network_listener -ne $null) {
        throw "Arc service unexpectedly reported a network listener."
    }
    if ($status.integrated_runtime_ready -ne $true) {
        throw "Installed Arc runtime is not ready."
    }

    $previewLines = & $sourceLauncher submit $previewTask -InstallRoot $InstallRoot -TestMode
    $previewExit = $LASTEXITCODE
    $preview = Convert-ArcOutputToJson $previewLines
    if ($previewExit -ne 0 -or $preview.result_status -ne "lima_ollama_preview_completed") {
        throw "Installed local preview failed."
    }
    if ($preview.guardian_status -ne "allow" -or [string]::IsNullOrWhiteSpace($preview.guardian_decision_id)) {
        throw "Installed local preview did not preserve Guardian allow lineage."
    }
    if ($preview.lima_called -ne $true -or $preview.executor_call_count -ne 1 -or $preview.ollama_called -ne $true) {
        throw "Installed local preview did not follow Guardian -> LIMA -> Ollama."
    }
    if ([string]::IsNullOrWhiteSpace($preview.output_text)) {
        throw "Installed local preview returned empty output."
    }
    if (-not (Test-Path -LiteralPath $preview.evidence_path -PathType Leaf)) {
        throw "Installed local preview evidence was not written."
    }

    $emailLines = & $sourceLauncher submit $emailTask -InstallRoot $InstallRoot -TestMode
    $emailExit = $LASTEXITCODE
    $email = Convert-ArcOutputToJson $emailLines
    if ($emailExit -ne 2 -or $email.guardian_status -ne "deny") {
        throw "External email negative control did not deny."
    }
    if ($email.lima_called -ne $false -or $email.ollama_called -ne $false -or $email.network_called -ne $false -or $email.execution_allowed -ne $false) {
        throw "Denied external email crossed the execution boundary."
    }

    $history = Convert-ArcOutputToJson (& $sourceLauncher history -InstallRoot $InstallRoot -TestMode)
    $evidence = Convert-ArcOutputToJson (& $sourceLauncher evidence -InstallRoot $InstallRoot -TestMode)
    if ($history.Count -lt 2 -or $evidence.Count -lt 2) {
        throw "Installed history/evidence commands did not expose both smoke runs."
    }

    $stop = Convert-ArcOutputToJson (& $sourceLauncher stop -InstallRoot $InstallRoot -TestMode)
    if ($stop.running -ne $false) {
        throw "Arc managed service did not stop."
    }
    & $sourceLauncher startup-enable -InstallRoot $InstallRoot -TestMode | Out-Null
    & $sourceLauncher startup-enable -InstallRoot $InstallRoot -TestMode | Out-Null
    & $sourceLauncher startup-disable -InstallRoot $InstallRoot -TestMode | Out-Null
    & $sourceLauncher startup-disable -InstallRoot $InstallRoot -TestMode | Out-Null
    $startupState = Get-Content -Raw -LiteralPath (Join-Path $InstallRoot "config\startup-state.json") | ConvertFrom-Json
    if ($startupState.registered -ne $false) {
        throw "Startup unregister was not idempotent."
    }

    $rollback = Convert-ArcOutputToJson (& $rollbackScript `
        -InstallRoot $InstallRoot `
        -Tag "arc-harness-shell-v0.10" `
        -SourcePath $repoRoot `
        -ResolveOnly `
        -TestMode)
    if ($rollback.verified -ne $true -or $rollback.commit -ne "fa1e93ff18203218a863b679f3d3608aa46bd5a4") {
        throw "v0.10 rollback anchor did not resolve exactly."
    }

    $pointerPath = Join-Path $InstallRoot "current\release.json"
    $pointerBefore = Get-Content -Raw -LiteralPath $pointerPath | ConvertFrom-Json
    $failedUpgrade = $false
    try {
        & $upgradeScript `
            -InstallRoot $InstallRoot `
            -Tag "arc-nonexistent-release-for-smoke" `
            -SourcePath $repoRoot `
            -TestMode | Out-Null
    }
    catch {
        $failedUpgrade = $true
    }
    if (-not $failedUpgrade) {
        throw "Invalid upgrade unexpectedly succeeded."
    }
    $pointerAfter = Get-Content -Raw -LiteralPath $pointerPath | ConvertFrom-Json
    if (
        $pointerAfter.tag -ne $pointerBefore.tag -or
        $pointerAfter.commit -ne $pointerBefore.commit -or
        $pointerAfter.app_root -ne $pointerBefore.app_root -or
        $pointerAfter.python_executable -ne $pointerBefore.python_executable
    ) {
        throw "Failed upgrade did not restore the previous release pointer."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $InstallRoot "data\state\runs.jsonl"))) {
        throw "Upgrade failure removed operator run history."
    }

    $uninstall = Convert-ArcOutputToJson (& $uninstallScript `
        -InstallRoot $InstallRoot `
        -KeepData `
        -Force `
        -NonInteractive `
        -TestMode)
    if ($uninstall.data_preserved -ne $true) {
        throw "Uninstall did not preserve data by default."
    }
    if (Test-Path -LiteralPath (Join-Path $InstallRoot "app")) {
        throw "Uninstall left the Arc application installed."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $InstallRoot "data"))) {
        throw "Uninstall removed preserved Arc data."
    }

    $summary = [ordered]@{
        status = "ok"
        install_root = $InstallRoot
        installation_result = "passed"
        installer_idempotent = $true
        startup_lifecycle = "start/status/stop passed"
        startup_registration = "idempotent mock create/remove passed"
        task_submission = "guarded queue path passed"
        local_preview = @{
            guardian_status = $preview.guardian_status
            guardian_decision_id = $preview.guardian_decision_id
            lima_called = $preview.lima_called
            executor_call_count = $preview.executor_call_count
            ollama_called = $preview.ollama_called
            output_nonempty = -not [string]::IsNullOrWhiteSpace($preview.output_text)
            evidence_written = $true
        }
        external_email = @{
            guardian_status = $email.guardian_status
            lima_called = $email.lima_called
            ollama_called = $email.ollama_called
            network_called = $email.network_called
            execution_allowed = $email.execution_allowed
        }
        failed_upgrade_rolled_back = $true
        rollback_anchor_verified = $rollback.verified
        rollback_commit = $rollback.commit
        uninstall_application_removed = $true
        uninstall_data_preserved = $uninstall.data_preserved
    }
    Write-Output ($summary | ConvertTo-Json -Depth 10)
}
finally {
    if (-not $KeepArtifacts -and (Test-Path -LiteralPath $InstallRoot)) {
        $resolved = [System.IO.Path]::GetFullPath($InstallRoot)
        if ($resolved.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $resolved -Recurse -Force
        }
    }
}
