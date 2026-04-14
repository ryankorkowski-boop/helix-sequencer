Param(
  [switch]$Clean
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Resolve-PythonExe {
  $candidates = @(
    (Join-Path $PSScriptRoot ".venv\Scripts\python.exe"),
    "C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"
  )

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCmd) {
    return $pythonCmd.Source
  }

  throw "Could not find a usable Python runtime for packaging."
}

$pythonExe = Resolve-PythonExe

if ($Clean) {
  if (Test-Path ".\build") { Remove-Item ".\build" -Recurse -Force }
  if (Test-Path ".\dist") { Remove-Item ".\dist" -Recurse -Force }
}

Write-Host "Installing/updating dependencies..."
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r requirements.txt

Write-Host "Building HelixSequenceWeaverBeta.exe with PyInstaller..."
& $pythonExe -m PyInstaller --noconfirm --clean .\dream_sequence_weaver.spec

$distExe = Join-Path $PSScriptRoot "dist\HelixSequenceWeaverBeta.exe"
if (Test-Path $distExe) {
  Copy-Item $distExe (Join-Path $PSScriptRoot "HelixSequenceWeaverBeta.exe") -Force
  Write-Host "Build complete: $distExe"
  Write-Host "Copied customer-ready exe to: $(Join-Path $PSScriptRoot 'HelixSequenceWeaverBeta.exe')"
} else {
  Write-Host "Build finished, but executable was not found at expected path: $distExe"
}
