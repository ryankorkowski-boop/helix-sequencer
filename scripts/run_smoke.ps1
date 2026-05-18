Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $RepoRoot
try {
    python -m compileall core ai xlights tools tests main.py gui_launcher.py
    python main.py --list-profiles
    python -m pytest -q
}
finally {
    Pop-Location
}
