param(
    [string]$Molecule = "Metformin",
    [string]$BaseUrl = "http://localhost:8000",
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

$safeName = $Molecule.Trim().ToLower().Replace(" ", "_")
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

if (-not $OutputPath) {
    $outputDir = Join-Path (Split-Path -Parent $PSScriptRoot) "outputs"
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir | Out-Null
    }
    $OutputPath = Join-Path $outputDir "${safeName}_orchestrator_${timestamp}.json"
}

$payload = @{ molecule = $Molecule } | ConvertTo-Json
$analyzeUrl = "$BaseUrl/analyze"

Write-Host "Calling: $analyzeUrl"
Write-Host "Molecule: $Molecule"

$response = Invoke-RestMethod -Method Post -Uri $analyzeUrl -ContentType "application/json" -Body $payload -TimeoutSec 300
$response | ConvertTo-Json -Depth 100 | Set-Content -Path $OutputPath -Encoding UTF8

Write-Host ""
Write-Host "Saved response to: $OutputPath"
Write-Host "Analysis ID: $($response.analysis_id)"
Write-Host "Top-level keys: $((($response.PSObject.Properties.Name) -join ', '))"

if ($response.summary) {
    Write-Host "Clinical Signal: $($response.summary.clinical_signal)"
    Write-Host "Market Signal: $($response.summary.market_signal)"
}
