Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $RepoRoot
try {
    python -m pip install --upgrade pip
    python -m pip install -r requirements-dev.txt
    & (Join-Path $PSScriptRoot "run_smoke.ps1")
}
finally {
    Pop-Location
}
