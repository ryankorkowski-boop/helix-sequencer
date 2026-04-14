Param(
  [switch]$Clean,
  [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not $SkipBuild) {
  if ($Clean) {
    & "$PSScriptRoot\build_exe.ps1" -Clean
  } else {
    & "$PSScriptRoot\build_exe.ps1"
  }
}

$distExe = Join-Path $PSScriptRoot "dist\HelixSequenceWeaverBeta.exe"
if (Test-Path $distExe) {
Copy-Item $distExe (Join-Path $PSScriptRoot "HelixSequenceWeaverBeta.exe") -Force
}

$sourceExe = Join-Path $PSScriptRoot "HelixSequenceWeaverBeta.exe"
if (-not (Test-Path $sourceExe)) {
$fallback = Join-Path $PSScriptRoot "dist\HelixSequenceWeaverBeta.exe"
  if (Test-Path $fallback) {
    Copy-Item $fallback $sourceExe -Force
  } else {
    throw "No packaged executable found. Run build_exe.ps1 first."
  }
}

$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$releaseRoot = Join-Path $PSScriptRoot "release"
$bundleDir = Join-Path $releaseRoot "DreamSequenceWeaver_$stamp"
New-Item -ItemType Directory -Force -Path $bundleDir | Out-Null

Copy-Item $sourceExe (Join-Path $bundleDir "HelixSequenceWeaverBeta.exe") -Force

$readmeSource = Join-Path $PSScriptRoot "CUSTOMER_README.txt"
if (Test-Path $readmeSource) {
  Copy-Item $readmeSource (Join-Path $bundleDir "README.txt") -Force
}

$instructions = Join-Path $PSScriptRoot "SEQUENCER_INSTRUCTIONS.txt"
if (Test-Path $instructions) {
  Copy-Item $instructions (Join-Path $bundleDir "SEQUENCER_INSTRUCTIONS.txt") -Force
}

$launchCmd = Join-Path $bundleDir "Launch Dream Sequence Weaver.cmd"
$cmdContent = @(
  "@echo off"
  "setlocal"
  "cd /d %~dp0"
'start "" "%~dp0HelixSequenceWeaverBeta.exe"'
)
Set-Content -Path $launchCmd -Value $cmdContent -Encoding ASCII

$iconScript = Join-Path $PSScriptRoot "set_folder_icons.ps1"
if (Test-Path $iconScript) {
  & $iconScript -TargetFolders @($bundleDir) | Out-Null
}

Write-Host "Customer bundle ready:"
Write-Host "  $bundleDir"
