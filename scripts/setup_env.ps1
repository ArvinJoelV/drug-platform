param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

function Resolve-Python {
    param([string]$Requested)

    if ($Requested -and (Test-Path $Requested)) {
        return $Requested
    }

    $candidates = @(
        (Join-Path (Split-Path -Parent $PSScriptRoot) "drug\Scripts\python.exe"),
        "C:\Users\Anirudh\AppData\Local\Programs\Python\Python312\python.exe",
        "C:\Users\Anirudh\AppData\Local\Programs\Python\Python310\python.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Could not find a usable python.exe. Pass -PythonExe explicitly."
}

$python = Resolve-Python -Requested $PythonExe
$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Using Python: $python"
Write-Host "Repo Root: $repoRoot"

Push-Location $repoRoot
try {
    & $python -m pip install -r requirements.txt
    & $python -m pip install -r orchestrator\requirements.txt
    & $python -m pip install -r clinical-agent\requirements.txt
    & $python -m pip install -r patent-agent\requirements.txt
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Dependency setup complete."
