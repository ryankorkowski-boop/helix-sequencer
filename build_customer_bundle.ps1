Param(
  [switch]$Clean,
  [switch]$SkipBuild,
  [switch]$Sign,
  [string]$CertThumbprint,
  [string]$PfxPath,
  [string]$PfxPassword,
  [string]$TimestampUrl = "http://timestamp.digicert.com",
  [string]$SignToolPath,
  [string]$SignatureDescription = "Dream Sequence Weaver xLights sequencer"
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not $SkipBuild) {
  $buildArgs = @()
  if ($Clean) {
    $buildArgs += "-Clean"
  }
  if ($Sign) { $buildArgs += "-Sign" }
  if (-not [string]::IsNullOrWhiteSpace($CertThumbprint)) { $buildArgs += @("-CertThumbprint", $CertThumbprint) }
  if (-not [string]::IsNullOrWhiteSpace($PfxPath)) { $buildArgs += @("-PfxPath", $PfxPath) }
  if (-not [string]::IsNullOrWhiteSpace($PfxPassword)) { $buildArgs += @("-PfxPassword", $PfxPassword) }
  if (-not [string]::IsNullOrWhiteSpace($TimestampUrl)) { $buildArgs += @("-TimestampUrl", $TimestampUrl) }
  if (-not [string]::IsNullOrWhiteSpace($SignToolPath)) { $buildArgs += @("-SignToolPath", $SignToolPath) }
  if (-not [string]::IsNullOrWhiteSpace($SignatureDescription)) { $buildArgs += @("-SignatureDescription", $SignatureDescription) }
  & "$PSScriptRoot\build_exe.ps1" @buildArgs
}
elseif (
  $Sign -or
  (-not [string]::IsNullOrWhiteSpace($CertThumbprint)) -or
  (-not [string]::IsNullOrWhiteSpace($PfxPath))
) {
  Write-Warning "Signing options were provided with -SkipBuild; they are ignored unless build_exe.ps1 runs."
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

$bundleExe = Join-Path $bundleDir "HelixSequenceWeaverBeta.exe"
$signature = Get-AuthenticodeSignature $bundleExe
if ($signature.Status -ne "Valid") {
  Write-Warning "Bundle EXE is not Authenticode signed (status: $($signature.Status))."
}

$versionInfo = (Get-Item $bundleExe).VersionInfo
if ([string]::IsNullOrWhiteSpace($versionInfo.FileVersion) -or [string]::IsNullOrWhiteSpace($versionInfo.ProductVersion)) {
  Write-Warning "Bundle EXE is missing version metadata fields."
}

Write-Host "Customer bundle ready:"
Write-Host "  $bundleDir"
