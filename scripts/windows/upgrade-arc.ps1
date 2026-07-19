[CmdletBinding()]
param(
    [string]$InstallRoot,
    [Parameter(Mandatory = $true)][string]$Tag,
    [string]$Repository = "https://github.com/armpit-symphony/Arc-Bot-shell.git",
    [string]$SourcePath,
    [switch]$TestMode,
    [switch]$RollbackMode
)

. (Join-Path $PSScriptRoot "common.ps1")

if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Get-ArcDefaultInstallRoot
}
$InstallRoot = Assert-ArcSafeInstallRoot -InstallRoot $InstallRoot
$paths = Get-ArcPaths -InstallRoot $InstallRoot
$config = Get-ArcConfig -InstallRoot $InstallRoot
$previousPointerJson = Get-Content -Raw -LiteralPath $paths.ReleasePointer
$previousPointer = $previousPointerJson | ConvertFrom-Json
$safeTag = $Tag -replace "[^A-Za-z0-9._-]", "_"
$releaseRoot = Join-Path $paths.Releases $safeTag
$releaseApp = Join-Path $releaseRoot "app"
$releaseVenv = Join-Path $releaseRoot "venv"
$releasePython = Join-Path $releaseVenv "Scripts\python.exe"
$stagingRoot = "$releaseRoot.staging-" + [guid]::NewGuid().ToString("N")
$stagingApp = Join-Path $stagingRoot "app"
$stagingVenv = Join-Path $stagingRoot "venv"
$stagingPython = Join-Path $stagingVenv "Scripts\python.exe"
$serviceWasRunning = $false

try {
    Write-ArcAuditEvent -Path (Join-Path $paths.Logs ($(if ($RollbackMode) { "rollback.jsonl" } else { "upgrade.jsonl" }))) -Event "release_prepare_started" -Metadata @{
        target_tag = $Tag
        previous_tag = $previousPointer.tag
    }
    if (Test-Path -LiteralPath $releaseRoot -PathType Container) {
        $existingPointer = [ordered]@{
            tag = $Tag
            commit = (& git -C $releaseApp rev-parse HEAD).Trim()
            app_root = $releaseApp
            python_executable = $releasePython
            activated_at = [DateTime]::UtcNow.ToString("o")
            rollback_anchor = $script:ArcRollbackTag
        }
        if (-not (Test-Path -LiteralPath $releasePython -PathType Leaf)) {
            throw "Existing release is incomplete: $releaseRoot"
        }
        $newPointer = $existingPointer
    }
    else {
        New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null
        $cloneSource = $(if ([string]::IsNullOrWhiteSpace($SourcePath)) { $Repository } else { [System.IO.Path]::GetFullPath($SourcePath) })
        & git clone --quiet --branch $Tag --depth 1 $cloneSource $stagingApp
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to resolve Arc release tag '$Tag'."
        }
        $targetCommit = (& git -C $stagingApp rev-parse HEAD).Trim()
        if ($targetCommit -notmatch "^[0-9a-f]{40}$") {
            throw "Resolved Arc release commit is invalid."
        }
        if ($Tag -eq $script:ArcRollbackTag -and $targetCommit -ne $script:ArcRollbackCommit) {
            throw "The v0.10 rollback tag does not resolve to the durable baseline."
        }
        if ($TestMode) {
            & python -m venv --system-site-packages $stagingVenv
        }
        else {
            & python -m venv $stagingVenv
        }
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to create isolated release environment."
        }
        if ($TestMode) {
            & $stagingPython -m pip install --disable-pip-version-check --no-deps $stagingApp
        }
        else {
            Assert-ArcRemoteTagPin -Repository "https://github.com/armpit-symphony/LIMA-Guardian-Suite.git" -Tag $script:GuardianTag -Commit $script:GuardianCommit | Out-Null
            Assert-ArcRemoteTagPin -Repository "https://github.com/armpit-symphony/LIMA-AI-OS.git" -Tag $script:LimaTag -Commit $script:LimaCommit | Out-Null
            & $stagingPython -m pip install --disable-pip-version-check "git+https://github.com/armpit-symphony/LIMA-Guardian-Suite.git@$script:GuardianCommit"
            if ($LASTEXITCODE -ne 0) {
                throw "Pinned Guardian installation failed for the release."
            }
            & $stagingPython -m pip install --disable-pip-version-check "git+https://github.com/armpit-symphony/LIMA-AI-OS.git@$script:LimaCommit"
            if ($LASTEXITCODE -ne 0) {
                throw "Pinned LIMA installation failed for the release."
            }
            & $stagingPython -m pip install --disable-pip-version-check --no-deps $stagingApp
        }
        if ($LASTEXITCODE -ne 0) {
            throw "Arc release package installation failed."
        }
        & $stagingPython -m compileall (Join-Path $stagingApp "arc_bot_shell") | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Arc release compilation failed."
        }
        Move-Item -LiteralPath $stagingRoot -Destination $releaseRoot
        $newPointer = [ordered]@{
            tag = $Tag
            commit = $targetCommit
            app_root = $releaseApp
            python_executable = $releasePython
            activated_at = [DateTime]::UtcNow.ToString("o")
            rollback_anchor = $script:ArcRollbackTag
        }
    }

    $serviceStatus = & $paths.ManagerPython -m arc_bot_shell.service.local_service status --config $paths.ConfigFile | ConvertFrom-Json
    $serviceWasRunning = $serviceStatus.running -eq $true
    if ($serviceWasRunning) {
        & $paths.ManagerPython -m arc_bot_shell.service.local_service stop --config $paths.ConfigFile | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to stop Arc before release activation."
        }
    }
    Write-ArcJsonAtomic -Path $paths.ReleasePointer -Value $newPointer

    & $paths.ManagerPython -m arc_bot_shell.service.operator_runtime_cli doctor --config $paths.ConfigFile | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Activated Arc release failed doctor."
    }
    & $paths.ManagerPython -m arc_bot_shell.service.operator_runtime_cli health --config $paths.ConfigFile | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Activated Arc release failed health."
    }
    if ($serviceWasRunning) {
        & $paths.ManagerPython -m arc_bot_shell.service.local_service start --config $paths.ConfigFile | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Activated Arc release service did not start."
        }
    }

    $manifest = Get-Content -Raw -LiteralPath $paths.Manifest | ConvertFrom-Json
    $manifest.previous_release = $previousPointer.tag
    $manifest.arc_tag = $newPointer.tag
    $manifest.arc_commit = $newPointer.commit
    $manifest | Add-Member -NotePropertyName "last_activation_at" -NotePropertyValue ([DateTime]::UtcNow.ToString("o")) -Force
    Write-ArcJsonAtomic -Path $paths.Manifest -Value $manifest
    $history = [ordered]@{
        at = [DateTime]::UtcNow.ToString("o")
        event = $(if ($RollbackMode) { "rollback_completed" } else { "upgrade_completed" })
        from_tag = $previousPointer.tag
        to_tag = $newPointer.tag
        to_commit = $newPointer.commit
        data_preserved = $true
    }
    Add-Content -LiteralPath $paths.History -Value ($history | ConvertTo-Json -Compress -Depth 10) -Encoding UTF8
    Write-Output ($history | ConvertTo-Json -Depth 10)
}
catch {
    if (Test-Path -LiteralPath $paths.ReleasePointer) {
        $previousPointerJson | Set-Content -LiteralPath $paths.ReleasePointer -Encoding UTF8
    }
    if ($serviceWasRunning) {
        try {
            & $paths.ManagerPython -m arc_bot_shell.service.local_service start --config $paths.ConfigFile | Out-Null
        }
        catch {
            Write-Warning "Previous Arc service could not be restarted automatically."
        }
    }
    if (Test-Path -LiteralPath $stagingRoot) {
        $failedRoot = Join-Path $paths.Backups ("failed-release-" + [guid]::NewGuid().ToString("N"))
        Move-Item -LiteralPath $stagingRoot -Destination $failedRoot
    }
    Write-ArcAuditEvent -Path (Join-Path $paths.Logs ($(if ($RollbackMode) { "rollback.jsonl" } else { "upgrade.jsonl" }))) -Event "release_activation_failed" -Metadata @{
        target_tag = $Tag
        restored_tag = $previousPointer.tag
        error = $_.Exception.Message
    }
    throw
}
