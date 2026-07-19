[CmdletBinding()]
param(
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet(
        "start", "stop", "restart", "status", "doctor", "health", "submit",
        "tasks", "history", "approvals", "evidence", "logs", "version",
        "startup-enable", "startup-disable", "diagnostics"
    )]
    [string]$Command,
    [Parameter(Position = 1)]
    [string]$TaskFile,
    [string]$InstallRoot,
    [int]$Limit = 20,
    [switch]$TestMode
)

. (Join-Path $PSScriptRoot "common.ps1")

if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Get-ArcDefaultInstallRoot
}
$InstallRoot = Assert-ArcSafeInstallRoot -InstallRoot $InstallRoot
$paths = Get-ArcPaths -InstallRoot $InstallRoot

switch ($Command) {
    "startup-enable" {
        & (Join-Path $paths.App "scripts\windows\register-startup.ps1") -InstallRoot $paths.Root -TestMode:$TestMode
        exit $LASTEXITCODE
    }
    "startup-disable" {
        & (Join-Path $paths.App "scripts\windows\unregister-startup.ps1") -InstallRoot $paths.Root -TestMode:$TestMode
        exit $LASTEXITCODE
    }
    "logs" {
        $serviceLog = Join-Path $paths.Logs "service.jsonl"
        $auditLog = Join-Path $paths.Logs "operator-audit.jsonl"
        $result = [ordered]@{
            service_log = $serviceLog
            operator_log = $auditLog
            service = $(if (Test-Path -LiteralPath $serviceLog) { Get-Content -Tail $Limit -LiteralPath $serviceLog } else { @() })
            operator = $(if (Test-Path -LiteralPath $auditLog) { Get-Content -Tail $Limit -LiteralPath $auditLog } else { @() })
        }
        Write-Output ($result | ConvertTo-Json -Depth 10)
        exit 0
    }
    "submit" {
        if ([string]::IsNullOrWhiteSpace($TaskFile)) {
            throw "submit requires a task packet path."
        }
        if (-not (Test-Path -LiteralPath $TaskFile -PathType Leaf)) {
            throw "Task packet not found: $TaskFile"
        }
        Invoke-ArcManager -InstallRoot $paths.Root -Command "submit" -TaskFile $TaskFile -Limit $Limit
        $exitCode = $LASTEXITCODE
        exit $exitCode
    }
    default {
        Invoke-ArcManager -InstallRoot $paths.Root -Command $Command -Limit $Limit
        $exitCode = $LASTEXITCODE
        exit $exitCode
    }
}
