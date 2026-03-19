param(
    [string]$BaseHost = "http://localhost"
)

$ErrorActionPreference = "Continue"

$checks = @(
    @{ Name = "Clinical"; Url = "$BaseHost`:8001/health" },
    @{ Name = "Literature"; Url = "$BaseHost`:8002/" },
    @{ Name = "Patent"; Url = "$BaseHost`:8003/health" },
    @{ Name = "Market"; Url = "$BaseHost`:8004/health" },
    @{ Name = "Regulatory"; Url = "$BaseHost`:8005/" },
    @{ Name = "Orchestrator"; Url = "$BaseHost`:8000/docs" }
)

foreach ($check in $checks) {
    try {
        $response = Invoke-WebRequest -Uri $check.Url -UseBasicParsing -TimeoutSec 8
        Write-Host ("{0,-14} OK    {1} ({2})" -f $check.Name, $check.Url, $response.StatusCode)
    }
    catch {
        Write-Host ("{0,-14} FAIL  {1}" -f $check.Name, $check.Url)
        Write-Host "  $($_.Exception.Message)"
    }
}
