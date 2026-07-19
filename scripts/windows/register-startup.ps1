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
$config = Get-ArcConfig -InstallRoot $InstallRoot
$launcher = Join-Path $paths.App "scripts\windows\arc.ps1"
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    throw "Installed Arc launcher is missing."
}

if ($TestMode) {
    $registration = [ordered]@{
        registered = $true
        task_name = $script:ArcTaskName
        trigger = "user_logon"
        current_user_only = $true
        highest_privileges = $false
        launcher = $launcher
        install_root = $paths.Root
        test_mode = $true
        registered_at = [DateTime]::UtcNow.ToString("o")
    }
}
else {
    $taskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$launcher`" start -InstallRoot `"$($paths.Root)`""
    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    & schtasks.exe /Create /F /SC ONLOGON /TN $script:ArcTaskName /TR $taskCommand /RU $currentUser /IT /RL LIMITED
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to register the per-user Arc startup task."
    }
    $registration = [ordered]@{
        registered = $true
        task_name = $script:ArcTaskName
        trigger = "user_logon"
        current_user_only = $true
        highest_privileges = $false
        launcher = $launcher
        install_root = $paths.Root
        test_mode = $false
        registered_at = [DateTime]::UtcNow.ToString("o")
    }
}
Write-ArcJsonAtomic -Path $paths.StartupState -Value $registration
$config.startup_registered = $true
Write-ArcJsonAtomic -Path $paths.ConfigFile -Value $config
Write-ArcAuditEvent -Path $paths.OperatorLog -Event "startup_registered" -Metadata @{
    task_name = $script:ArcTaskName
    test_mode = [bool]$TestMode
}
Write-Output ($registration | ConvertTo-Json -Depth 10)
