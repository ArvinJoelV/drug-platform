param(
    [switch]$IncludeLauncherWindows
)

$ErrorActionPreference = "Continue"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$targets = @(
    "clinical_agent_server.py",
    "literature-agent\main.py",
    "patent_server.py",
    "market_server.py",
    "uvicorn orchestrator.main:app",
    "uvicorn main:app --host 0.0.0.0 --port 8005"
)

function Matches-ProjectServer {
    param([string]$CommandLine)

    if (-not $CommandLine) {
        return $false
    }

    $normalized = $CommandLine.ToLower()
    $repoNormalized = $repoRoot.ToLower()

    if ($normalized -notlike "*$repoNormalized*") {
        return $false
    }

    foreach ($target in $targets) {
        if ($normalized -like ("*" + $target.ToLower() + "*")) {
            return $true
        }
    }

    return $false
}

$processes = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -in @("python.exe", "pythonw.exe", "powershell.exe") -and (Matches-ProjectServer -CommandLine $_.CommandLine)
}

if (-not $processes) {
    Write-Host "No matching drug-platform server processes were found."
    exit 0
}

Write-Host "Stopping server processes..."

foreach ($process in $processes) {
    $label = "{0} (PID {1})" -f $process.Name, $process.ProcessId
    Write-Host "  Stopping $label"
    Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
}

if ($IncludeLauncherWindows) {
    $windows = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -eq "powershell.exe" -and $_.CommandLine -and $_.CommandLine.ToLower().Contains($repoRoot.ToLower())
    }

    foreach ($window in $windows) {
        Write-Host ("  Closing PowerShell window (PID {0})" -f $window.ProcessId)
        Stop-Process -Id $window.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Done."
