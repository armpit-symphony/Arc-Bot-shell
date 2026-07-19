[CmdletBinding()]
param(
    [string]$InstallRoot,
    [switch]$TestMode
)

. (Join-Path $PSScriptRoot "common.ps1")

if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Get-ArcDefaultInstallRoot
}
$InstallRoot = Assert-ArcSafeInstallRoot -InstallRoot $InstallRoot
$paths = Get-ArcPaths -InstallRoot $InstallRoot

if (-not $TestMode) {
    & schtasks.exe /Query /TN $script:ArcTaskName *> $null
    if ($LASTEXITCODE -eq 0) {
        & schtasks.exe /Delete /F /TN $script:ArcTaskName
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to unregister the Arc startup task."
        }
    }
}

$state = [ordered]@{
    registered = $false
    task_name = $script:ArcTaskName
    removed_at = [DateTime]::UtcNow.ToString("o")
    test_mode = [bool]$TestMode
}
Write-ArcJsonAtomic -Path $paths.StartupState -Value $state
if (Test-Path -LiteralPath $paths.ConfigFile -PathType Leaf) {
    $config = Get-Content -Raw -LiteralPath $paths.ConfigFile | ConvertFrom-Json
    $config.startup_registered = $false
    Write-ArcJsonAtomic -Path $paths.ConfigFile -Value $config
}
Write-ArcAuditEvent -Path $paths.OperatorLog -Event "startup_unregistered" -Metadata @{
    task_name = $script:ArcTaskName
    test_mode = [bool]$TestMode
}
Write-Output ($state | ConvertTo-Json -Depth 10)
