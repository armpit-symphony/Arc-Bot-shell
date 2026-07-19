Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:ArcTaskName = "SparkPitLabs-ArcBot"
$script:ArcRollbackTag = "arc-harness-shell-v0.10"
$script:ArcRollbackCommit = "fa1e93ff18203218a863b679f3d3608aa46bd5a4"
$script:GuardianTag = "guardian-core-v1.1-local-model-preview-policy"
$script:GuardianCommit = "69e843218c521b913edcec404dea6b7be8c64f06"
$script:LimaTag = "lima-runtime-v1.1-loopback-ollama-executor"
$script:LimaCommit = "deea1c4f5b6d3455a7e97e4b621e22b8d22a6244"

function Get-ArcDefaultInstallRoot {
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        throw "LOCALAPPDATA is required for the default per-user Arc installation."
    }
    return Join-Path $env:LOCALAPPDATA "SparkPitLabs\ArcBot"
}

function Get-ArcPaths {
    param([Parameter(Mandatory = $true)][string]$InstallRoot)

    $root = [System.IO.Path]::GetFullPath($InstallRoot)
    return [ordered]@{
        Root = $root
        App = Join-Path $root "app"
        Venv = Join-Path $root "venv"
        Data = Join-Path $root "data"
        Logs = Join-Path $root "logs"
        Config = Join-Path $root "config"
        Releases = Join-Path $root "releases"
        Current = Join-Path $root "current"
        Backups = Join-Path $root "backups"
        Manager = Join-Path $root "manager"
        ConfigFile = Join-Path $root "config\arc-config.json"
        Manifest = Join-Path $root "config\installation-manifest.json"
        History = Join-Path $root "config\installation-history.jsonl"
        StartupState = Join-Path $root "config\startup-state.json"
        InstallLog = Join-Path $root "logs\install.jsonl"
        OperatorLog = Join-Path $root "logs\operator-audit.jsonl"
        Launcher = Join-Path $root "manager\scripts\arc.ps1"
        ManagerPython = Join-Path $root "venv\Scripts\python.exe"
        ReleasePointer = Join-Path $root "current\release.json"
    }
}

function Assert-ArcSafeInstallRoot {
    param([Parameter(Mandatory = $true)][string]$InstallRoot)

    $resolved = [System.IO.Path]::GetFullPath($InstallRoot)
    $driveRoot = [System.IO.Path]::GetPathRoot($resolved)
    if ($resolved -eq $driveRoot) {
        throw "Arc install root cannot be a drive root."
    }
    if ($resolved.Length -lt 12) {
        throw "Arc install root is too broad."
    }
    return $resolved
}

function Assert-ArcLoopbackOllamaUrl {
    param([Parameter(Mandatory = $true)][string]$Url)

    if ($Url -ne $Url.Trim()) {
        throw "Ollama URL cannot contain surrounding whitespace."
    }
    try {
        $uri = [System.Uri]$Url
    }
    catch {
        throw "Ollama URL is malformed."
    }
    if (-not $uri.IsAbsoluteUri -or $uri.Scheme -ne "http") {
        throw "Ollama URL must use HTTP."
    }
    if ($uri.Host -notin @("127.0.0.1", "localhost")) {
        throw "Ollama URL must use 127.0.0.1 or localhost."
    }
    if (-not [string]::IsNullOrEmpty($uri.UserInfo)) {
        throw "Ollama URL credentials are forbidden."
    }
    if ($uri.IsDefaultPort -or $uri.Port -lt 1 -or $uri.Port -gt 65535) {
        throw "Ollama URL requires an explicit valid port."
    }
    if ($uri.AbsolutePath -notin @("", "/")) {
        throw "Ollama URL must be a base endpoint without a path."
    }
    if (-not [string]::IsNullOrEmpty($uri.Query) -or -not [string]::IsNullOrEmpty($uri.Fragment)) {
        throw "Ollama URL cannot contain a query or fragment."
    }
    return "http://$($uri.Host):$($uri.Port)"
}

function Write-ArcJsonAtomic {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )

    $parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $temporary = "$Path.tmp"
    $Value | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $temporary -Encoding UTF8
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Write-ArcAuditEvent {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Event,
        [hashtable]$Metadata = @{}
    )

    $parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $payload = [ordered]@{
        at = [DateTime]::UtcNow.ToString("o")
        event = $Event
    }
    foreach ($key in $Metadata.Keys) {
        $payload[$key] = $Metadata[$key]
    }
    Add-Content -LiteralPath $Path -Value ($payload | ConvertTo-Json -Compress -Depth 10) -Encoding UTF8
}

function Get-ArcConfig {
    param([Parameter(Mandatory = $true)][string]$InstallRoot)

    $paths = Get-ArcPaths -InstallRoot $InstallRoot
    if (-not (Test-Path -LiteralPath $paths.ConfigFile -PathType Leaf)) {
        throw "Arc is not installed at $($paths.Root)."
    }
    return Get-Content -Raw -LiteralPath $paths.ConfigFile | ConvertFrom-Json
}

function Get-ArcReleasePointer {
    param([Parameter(Mandatory = $true)][string]$InstallRoot)

    $paths = Get-ArcPaths -InstallRoot $InstallRoot
    if (-not (Test-Path -LiteralPath $paths.ReleasePointer -PathType Leaf)) {
        throw "Arc active release pointer is missing."
    }
    return Get-Content -Raw -LiteralPath $paths.ReleasePointer | ConvertFrom-Json
}

function Invoke-ArcManager {
    param(
        [Parameter(Mandatory = $true)][string]$InstallRoot,
        [Parameter(Mandatory = $true)][string]$Command,
        [string]$TaskFile,
        [int]$Limit = 20
    )

    $paths = Get-ArcPaths -InstallRoot $InstallRoot
    if (-not (Test-Path -LiteralPath $paths.ManagerPython -PathType Leaf)) {
        throw "Arc manager Python is missing: $($paths.ManagerPython)"
    }
    $arguments = @(
        "-m", "arc_bot_shell.service.operator_runtime_cli",
        $Command,
        "--config", $paths.ConfigFile,
        "--limit", [string]$Limit
    )
    if (-not [string]::IsNullOrWhiteSpace($TaskFile)) {
        $arguments += @("--task-file", [System.IO.Path]::GetFullPath($TaskFile))
    }
    & $paths.ManagerPython @arguments
}

function Copy-ArcTrackedSource {
    param(
        [Parameter(Mandatory = $true)][string]$SourcePath,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    if (-not (Test-Path -LiteralPath (Join-Path $SourcePath ".git"))) {
        throw "SourcePath must be an Arc Git checkout."
    }
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    $archive = Join-Path ([System.IO.Path]::GetTempPath()) ("arc-source-" + [guid]::NewGuid().ToString("N") + ".zip")
    try {
        & git -C $SourcePath archive --format=zip --output=$archive HEAD
        if ($LASTEXITCODE -ne 0) {
            throw "git archive failed."
        }
        Expand-Archive -LiteralPath $archive -DestinationPath $Destination -Force
    }
    finally {
        if (Test-Path -LiteralPath $archive) {
            Remove-Item -LiteralPath $archive -Force
        }
    }
}

function Get-ArcSourceCommit {
    param([Parameter(Mandatory = $true)][string]$SourcePath)
    $commit = (& git -C $SourcePath rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $commit -notmatch "^[0-9a-f]{40}$") {
        throw "Unable to resolve Arc source commit."
    }
    return $commit
}

function Get-ArcSourceTag {
    param([Parameter(Mandatory = $true)][string]$SourcePath)
    $tag = (& git -C $SourcePath describe --tags --exact-match 2>$null)
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($tag)) {
        return $tag.Trim()
    }
    return (& git -C $SourcePath branch --show-current).Trim()
}

function Test-ArcModelInstalled {
    param([Parameter(Mandatory = $true)][string]$Model)
    $lines = & ollama list 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }
    foreach ($line in $lines) {
        if ($line -match ("^" + [regex]::Escape($Model) + "\s")) {
            return $true
        }
    }
    return $false
}

function Test-ArcStartupRegistered {
    param(
        [Parameter(Mandatory = $true)][string]$InstallRoot,
        [switch]$TestMode
    )

    $paths = Get-ArcPaths -InstallRoot $InstallRoot
    if ($TestMode) {
        if (-not (Test-Path -LiteralPath $paths.StartupState -PathType Leaf)) {
            return $false
        }
        $state = Get-Content -Raw -LiteralPath $paths.StartupState | ConvertFrom-Json
        return $state.registered -eq $true
    }
    & schtasks.exe /Query /TN $script:ArcTaskName *> $null
    return $LASTEXITCODE -eq 0
}
