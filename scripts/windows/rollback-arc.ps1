[CmdletBinding()]
param(
    [string]$InstallRoot,
    [string]$Tag = "arc-harness-shell-v0.10",
    [string]$Repository = "https://github.com/armpit-symphony/Arc-Bot-shell.git",
    [string]$SourcePath,
    [switch]$ResolveOnly,
    [switch]$TestMode
)

. (Join-Path $PSScriptRoot "common.ps1")

if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Get-ArcDefaultInstallRoot
}
$InstallRoot = Assert-ArcSafeInstallRoot -InstallRoot $InstallRoot
if ($Tag -ne $script:ArcRollbackTag) {
    throw "v0.11 supports only the audited rollback anchor $script:ArcRollbackTag."
}

if (-not [string]::IsNullOrWhiteSpace($SourcePath)) {
    $resolvedCommit = (& git -C $SourcePath rev-parse "$Tag^{}").Trim()
}
else {
    $lines = & git ls-remote --tags $Repository "refs/tags/$Tag^{}"
    if ($LASTEXITCODE -ne 0 -or $lines.Count -eq 0) {
        throw "Unable to resolve rollback tag $Tag."
    }
    $resolvedCommit = (($lines | Select-Object -First 1) -split "\s+")[0]
}
if ($resolvedCommit -ne $script:ArcRollbackCommit) {
    throw "Rollback tag $Tag does not resolve to the durable v0.10 commit."
}

if ($ResolveOnly) {
    Write-Output ([ordered]@{
        tag = $Tag
        commit = $resolvedCommit
        verified = $true
        activated = $false
    } | ConvertTo-Json -Depth 10)
    exit 0
}

$arguments = @{
    InstallRoot = $InstallRoot
    Tag = $Tag
    Repository = $Repository
    RollbackMode = $true
    TestMode = [bool]$TestMode
}
if (-not [string]::IsNullOrWhiteSpace($SourcePath)) {
    $arguments.SourcePath = $SourcePath
}
& (Join-Path $PSScriptRoot "upgrade-arc.ps1") @arguments
exit $LASTEXITCODE
