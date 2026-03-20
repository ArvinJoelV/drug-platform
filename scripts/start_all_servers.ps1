param(
    [string]$PythonExe = "",
    [switch]$SetupFirst
)

$ErrorActionPreference = "Stop"

function Resolve-Python {
    param([string]$Requested)

    if ($Requested -and (Test-Path $Requested)) {
        return $Requested
    }

    $candidates = @(
        (Join-Path (Split-Path -Parent $PSScriptRoot) "venv\Scripts\python.exe"),
        "python"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Could not find a usable python.exe. Pass -PythonExe explicitly."
}

function Start-AgentWindow {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Command,
        [string]$ActivateScript
    )

    $activateSegment = ""
    if ($ActivateScript) {
        $activateSegment = "& '$ActivateScript'; "
    }

    $fullCommand = "Set-Location '$WorkingDirectory'; `$host.UI.RawUI.WindowTitle = '$Title'; $activateSegment$Command"
    Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $fullCommand | Out-Null
}

$python = Resolve-Python -Requested $PythonExe
$repoRoot = Split-Path -Parent $PSScriptRoot
$activateScript = Join-Path $repoRoot "venv\Scripts\Activate.ps1"
if (-not (Test-Path $python)) {
    throw "Could not find Python interpreter: $python"
}

if (-not (Test-Path $activateScript)) {
    throw "Could not find venv activation script: $activateScript"
}

if ($SetupFirst) {
    & "$PSScriptRoot\setup_env.ps1" -PythonExe $python
}

Write-Host "Using Python: $python"
Write-Host "Using venv: $activateScript"
Write-Host "Starting all agent servers and the orchestrator..."

Start-AgentWindow -Title "Clinical Agent :8001" -WorkingDirectory (Join-Path $repoRoot "clinical-agent") -Command "& '$python' .\clinical_agent_server.py --port 8001" -ActivateScript $activateScript
Start-Sleep -Seconds 1

Start-AgentWindow -Title "Literature Agent :8002" -WorkingDirectory (Join-Path $repoRoot "literature-agent") -Command "& '$python' .\main.py" -ActivateScript $activateScript
Start-Sleep -Seconds 1

Start-AgentWindow -Title "Patent Agent :8003" -WorkingDirectory (Join-Path $repoRoot "patent-agent") -Command "& '$python' .\patent_server.py --port 8003 --database patent_database.json" -ActivateScript $activateScript
Start-Sleep -Seconds 1

Start-AgentWindow -Title "Market Agent :8004" -WorkingDirectory (Join-Path $repoRoot "market_agent") -Command "& '$python' .\market_server.py --port 8004" -ActivateScript $activateScript
Start-Sleep -Seconds 1

Start-AgentWindow -Title "Regulatory Agent :8005" -WorkingDirectory (Join-Path $repoRoot "regulatory_agent") -Command "& '$python' -m uvicorn main:app --host 0.0.0.0 --port 8005" -ActivateScript $activateScript
Start-Sleep -Seconds 1

Start-AgentWindow -Title "Orchestrator :8000" -WorkingDirectory $repoRoot -Command "& '$python' -m uvicorn orchestrator.main:app --host 0.0.0.0 --port 8000" -ActivateScript $activateScript

Write-Host ""
Write-Host "All server windows were launched."
Write-Host "Run .\scripts\check_health.ps1 after 10-20 seconds to verify startup."
