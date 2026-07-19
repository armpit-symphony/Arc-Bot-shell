[CmdletBinding()]
param(
    [string]$InstallRoot,
    [string]$Model = "qwen2.5:7b",
    [string]$OllamaUrl = "http://127.0.0.1:11434",
    [switch]$InstallModel,
    [switch]$RegisterStartup,
    [switch]$Force,
    [switch]$NonInteractive,
    [string]$SourcePath,
    [string]$GuardianPath,
    [switch]$TestMode
)

. (Join-Path $PSScriptRoot "common.ps1")

if ($env:OS -ne "Windows_NT") {
    throw "Arc v0.11 installer supports Windows only."
}
if ($PSVersionTable.PSVersion -lt [version]"5.1") {
    throw "PowerShell 5.1 or newer is required."
}
if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Get-ArcDefaultInstallRoot
}
$InstallRoot = Assert-ArcSafeInstallRoot -InstallRoot $InstallRoot
$paths = Get-ArcPaths -InstallRoot $InstallRoot
$OllamaUrl = Assert-ArcLoopbackOllamaUrl -Url $OllamaUrl
if ([string]::IsNullOrWhiteSpace($Model) -or $Model -match "\s") {
    throw "Arc Ollama model must be a non-empty model name without whitespace."
}
if ([string]::IsNullOrWhiteSpace($SourcePath)) {
    $SourcePath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
}
else {
    $SourcePath = [System.IO.Path]::GetFullPath($SourcePath)
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pythonCommand) {
    throw "Python is required. Install Python 3.11 or newer."
}
$pythonVersionText = (& $pythonCommand.Source -c "import platform; print(platform.python_version())").Trim()
$pythonVersion = [version]$pythonVersionText
if ($pythonVersion -lt [version]"3.11") {
    throw "Python 3.11 or newer is required; found $pythonVersionText."
}
if ($null -eq (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required for audited Arc release installation."
}
if ($null -eq (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "Ollama is required but was not found. Arc will not install it silently."
}
$ollamaVersion = (& ollama --version 2>&1 | Select-Object -First 1).ToString().Trim()
$modelInstalled = Test-ArcModelInstalled -Model $Model
if (-not $modelInstalled -and $InstallModel) {
    if ($NonInteractive -and -not $InstallModel) {
        throw "Non-interactive model installation requires -InstallModel."
    }
    & ollama pull $Model
    if ($LASTEXITCODE -ne 0) {
        throw "Ollama model installation failed."
    }
    $modelInstalled = Test-ArcModelInstalled -Model $Model
}
if (-not $modelInstalled) {
    throw "Configured model '$Model' is not installed. Re-run with -InstallModel only after explicit operator approval."
}

if (Test-Path -LiteralPath $paths.Manifest -PathType Leaf) {
    if (-not $Force) {
        Write-Output (Get-Content -Raw -LiteralPath $paths.Manifest)
        exit 0
    }
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $backup = Join-Path $paths.Backups "pre-install-$stamp"
    New-Item -ItemType Directory -Force -Path $backup | Out-Null
    foreach ($name in @("app", "venv", "config", "current", "manager")) {
        $candidate = Join-Path $paths.Root $name
        if (Test-Path -LiteralPath $candidate) {
            Move-Item -LiteralPath $candidate -Destination (Join-Path $backup $name)
        }
    }
}

foreach ($directory in @(
    $paths.Root, $paths.App, $paths.Data, $paths.Logs, $paths.Config,
    $paths.Releases, $paths.Current, $paths.Backups, $paths.Manager
)) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

$startupWasCreated = $false
try {
    Write-ArcAuditEvent -Path $paths.InstallLog -Event "install_started" -Metadata @{
        install_root = $paths.Root
        source_path = $SourcePath
        test_mode = [bool]$TestMode
    }
    if ($TestMode) {
        foreach ($directoryName in @("arc_bot_shell", "scripts", "samples")) {
            Copy-Item -Path (Join-Path $SourcePath $directoryName) -Destination $paths.App -Recurse -Force
        }
        foreach ($fileName in @("pyproject.toml", "README.md", "workspace.lock.json")) {
            Copy-Item -LiteralPath (Join-Path $SourcePath $fileName) -Destination $paths.App -Force
        }
    }
    else {
        Copy-ArcTrackedSource -SourcePath $SourcePath -Destination $paths.App
    }

    if ($TestMode) {
        & $pythonCommand.Source -m venv --system-site-packages $paths.Venv
    }
    else {
        & $pythonCommand.Source -m venv $paths.Venv
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to create the Arc virtual environment."
    }
    $venvPython = Join-Path $paths.Venv "Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        throw "Arc virtual environment Python is missing."
    }

    if ($TestMode) {
        & $venvPython -m pip install --disable-pip-version-check --no-deps $paths.App
    }
    else {
        & $venvPython -m pip install --disable-pip-version-check --upgrade pip
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to update pip in the Arc virtual environment."
        }
        Assert-ArcRemoteTagPin -Repository "https://github.com/armpit-symphony/LIMA-Guardian-Suite.git" -Tag $script:GuardianTag -Commit $script:GuardianCommit | Out-Null
        Assert-ArcRemoteTagPin -Repository "https://github.com/armpit-symphony/LIMA-AI-OS.git" -Tag $script:LimaTag -Commit $script:LimaCommit | Out-Null
        & $venvPython -m pip install --disable-pip-version-check "git+https://github.com/armpit-symphony/LIMA-Guardian-Suite.git@$script:GuardianCommit"
        if ($LASTEXITCODE -ne 0) {
            throw "Pinned Guardian installation failed."
        }
        & $venvPython -m pip install --disable-pip-version-check "git+https://github.com/armpit-symphony/LIMA-AI-OS.git@$script:LimaCommit"
        if ($LASTEXITCODE -ne 0) {
            throw "Pinned LIMA installation failed."
        }
        & $venvPython -m pip install --disable-pip-version-check --no-deps $paths.App
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Arc package installation failed."
    }

    if ([string]::IsNullOrWhiteSpace($GuardianPath) -and $TestMode) {
        $candidateGuardian = [System.IO.Path]::GetFullPath((Join-Path $SourcePath "..\LIMA-Guardian-Suite"))
        if (Test-Path -LiteralPath (Join-Path $candidateGuardian "guardian_core\__init__.py")) {
            $GuardianPath = $candidateGuardian
        }
    }
    $sourceCommit = Get-ArcSourceCommit -SourcePath $SourcePath
    $sourceTag = Get-ArcSourceTag -SourcePath $SourcePath
    $configPayload = [ordered]@{
        install_root = $paths.Root
        app_root = $paths.App
        python_executable = $venvPython
        guardian_mode = "guardian_core"
        guardian_path = $(if ([string]::IsNullOrWhiteSpace($GuardianPath)) { $null } else { [System.IO.Path]::GetFullPath($GuardianPath) })
        guardian_reference = $script:GuardianTag
        lima_reference = $script:LimaTag
        lima_commit = $script:LimaCommit
        ollama_url = $OllamaUrl
        model = $Model
        installed_version = "0.11"
        installed_tag = $sourceTag
        installed_commit = $sourceCommit
        startup_task_name = $script:ArcTaskName
        startup_registered = $false
        health_interval_seconds = 60
        schema_version = "arc-windows-operator-config-v1"
    }
    Write-ArcJsonAtomic -Path $paths.ConfigFile -Value $configPayload
    $releasePointer = [ordered]@{
        tag = $sourceTag
        commit = $sourceCommit
        app_root = $paths.App
        python_executable = $venvPython
        activated_at = [DateTime]::UtcNow.ToString("o")
        rollback_anchor = $script:ArcRollbackTag
    }
    Write-ArcJsonAtomic -Path $paths.ReleasePointer -Value $releasePointer

    $managerScripts = Join-Path $paths.Manager "scripts"
    New-Item -ItemType Directory -Force -Path $managerScripts | Out-Null
    Copy-Item -Path (Join-Path $paths.App "scripts\windows\*") -Destination $managerScripts -Recurse -Force

    & $venvPython -m compileall (Join-Path $paths.App "arc_bot_shell") | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Installed Arc compilation failed."
    }
    & $venvPython -m arc_bot_shell.service.operator_runtime_cli doctor --config $paths.ConfigFile
    if ($LASTEXITCODE -ne 0) {
        throw "Installed Arc doctor reported blockers."
    }
    & $venvPython -m arc_bot_shell.service.operator_runtime_cli health --config $paths.ConfigFile
    if ($LASTEXITCODE -ne 0) {
        throw "Installed Arc health check failed."
    }

    $manifest = [ordered]@{
        schema_version = "arc-installation-manifest-v1"
        installed_at = [DateTime]::UtcNow.ToString("o")
        arc_version = "0.11"
        arc_tag = $sourceTag
        arc_commit = $sourceCommit
        rollback_tag = $script:ArcRollbackTag
        rollback_commit = $script:ArcRollbackCommit
        guardian_tag = $script:GuardianTag
        guardian_commit = $script:GuardianCommit
        lima_tag = $script:LimaTag
        lima_commit = $script:LimaCommit
        python_version = $pythonVersionText
        ollama_version = $ollamaVersion
        configured_model = $Model
        ollama_url = $OllamaUrl
        install_root = $paths.Root
        virtual_environment_path = $paths.Venv
        data_path = $paths.Data
        log_path = $paths.Logs
        startup_registration_state = $false
        previous_release = $null
        manager_separate_from_runtime = $true
    }
    Write-ArcJsonAtomic -Path $paths.Manifest -Value $manifest
    Add-Content -LiteralPath $paths.History -Value ($manifest | ConvertTo-Json -Compress -Depth 10) -Encoding UTF8

    if ($RegisterStartup) {
        & (Join-Path $paths.App "scripts\windows\register-startup.ps1") -InstallRoot $paths.Root -TestMode:$TestMode
        if ($LASTEXITCODE -ne 0) {
            throw "Arc startup registration failed."
        }
        $startupWasCreated = $true
        $manifest.startup_registration_state = $true
        Write-ArcJsonAtomic -Path $paths.Manifest -Value $manifest
    }
    Write-ArcAuditEvent -Path $paths.InstallLog -Event "install_completed" -Metadata @{
        arc_commit = $sourceCommit
        startup_registered = $startupWasCreated
    }
    Write-Output ($manifest | ConvertTo-Json -Depth 10)
}
catch {
    if ($startupWasCreated) {
        try {
            & (Join-Path $paths.App "scripts\windows\unregister-startup.ps1") -InstallRoot $paths.Root -TestMode:$TestMode
        }
        catch {
            Write-Warning "Unable to clean up the Arc startup task after installation failure."
        }
    }
    Write-ArcAuditEvent -Path $paths.InstallLog -Event "install_failed" -Metadata @{
        error = $_.Exception.Message
        startup_active = $false
    }
    throw
}
