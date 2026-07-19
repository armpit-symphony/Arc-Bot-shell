[CmdletBinding()]
param(
    [string]$InstallRoot,
    [switch]$KeepData,
    [switch]$RemoveData,
    [switch]$Force,
    [switch]$NonInteractive,
    [switch]$TestMode
)

. (Join-Path $PSScriptRoot "common.ps1")

if ($KeepData -and $RemoveData) {
    throw "-KeepData and -RemoveData cannot be used together."
}
if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Get-ArcDefaultInstallRoot
}
$InstallRoot = Assert-ArcSafeInstallRoot -InstallRoot $InstallRoot
$paths = Get-ArcPaths -InstallRoot $InstallRoot
if (-not (Test-Path -LiteralPath $paths.Root -PathType Container)) {
    Write-Output (@{ installed = $false; install_root = $paths.Root } | ConvertTo-Json)
    exit 0
}

try {
    if (Test-Path -LiteralPath $paths.ConfigFile -PathType Leaf) {
        & $paths.ManagerPython -m arc_bot_shell.service.operator_runtime_cli stop --config $paths.ConfigFile | Out-Null
    }
}
catch {
    if (-not $Force) {
        throw
    }
}

& (Join-Path $paths.App "scripts\windows\unregister-startup.ps1") -InstallRoot $paths.Root -TestMode:$TestMode | Out-Null
if ($LASTEXITCODE -ne 0 -and -not $Force) {
    throw "Arc startup could not be unregistered."
}

$summary = [ordered]@{
    uninstalled_at = [DateTime]::UtcNow.ToString("o")
    install_root = $paths.Root
    application_removed = $true
    data_preserved = -not $RemoveData
    ollama_removed = $false
    models_removed = $false
    python_removed = $false
    git_removed = $false
}
Write-ArcAuditEvent -Path (Join-Path $paths.Logs "uninstall.jsonl") -Event "uninstall_started" -Metadata @{
    remove_data = [bool]$RemoveData
}

if ($RemoveData) {
    if (-not $Force -and -not $NonInteractive) {
        $confirmation = Read-Host "Type REMOVE ARC DATA to permanently delete Arc user data"
        if ($confirmation -ne "REMOVE ARC DATA") {
            throw "Arc data removal was not confirmed."
        }
    }
    $summaryPath = Join-Path ([System.IO.Path]::GetTempPath()) ("arc-uninstall-" + [guid]::NewGuid().ToString("N") + ".json")
    $summary | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
    Remove-Item -LiteralPath $paths.Root -Recurse -Force
    Write-Output (Get-Content -Raw -LiteralPath $summaryPath)
    Remove-Item -LiteralPath $summaryPath -Force
    exit 0
}

foreach ($candidate in @(
    $paths.App, $paths.Venv, $paths.Releases, $paths.Current,
    $paths.Backups, $paths.Manager
)) {
    if (Test-Path -LiteralPath $candidate) {
        Remove-Item -LiteralPath $candidate -Recurse -Force
    }
}
if (Test-Path -LiteralPath $paths.Manifest -PathType Leaf) {
    $manifest = Get-Content -Raw -LiteralPath $paths.Manifest | ConvertFrom-Json
    $manifest | Add-Member -NotePropertyName "uninstalled_at" -NotePropertyValue $summary.uninstalled_at -Force
    $manifest | Add-Member -NotePropertyName "data_preserved" -NotePropertyValue $true -Force
    Write-ArcJsonAtomic -Path $paths.Manifest -Value $manifest
}
Write-ArcAuditEvent -Path (Join-Path $paths.Logs "uninstall.jsonl") -Event "uninstall_completed" -Metadata @{
    data_preserved = $true
}
Write-Output ($summary | ConvertTo-Json -Depth 10)
