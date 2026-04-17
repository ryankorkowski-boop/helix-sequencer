Param(
  [switch]$SkipBuild,
  [switch]$IncludeEndToEnd,
  [switch]$RequireSignature,
  [switch]$Sign,
  [string]$CertThumbprint,
  [string]$PfxPath,
  [string]$PfxPassword,
  [string]$TimestampUrl = "http://timestamp.digicert.com",
  [string]$SignToolPath,
  [string]$SignatureDescription = "Dream Sequence Weaver xLights sequencer",
  [string]$Profile = "master",
  [string]$Template = "template.xsq",
  [string]$Audio = "2.wav"
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$results = New-Object System.Collections.Generic.List[object]
$hasFailures = $false

function Add-GateResult {
  Param(
    [string]$Gate,
    [string]$Status,
    [string]$Details
  )
  $results.Add([pscustomobject]@{
      Gate    = $Gate
      Status  = $Status
      Details = $Details
    }) | Out-Null
  if ($Status -eq "FAIL") {
    $script:hasFailures = $true
  }
}

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

  throw "Could not find a usable Python runtime."
}

function Assert-LastExitCode {
  Param(
    [string]$Gate,
    [string]$OkDetails,
    [string]$FailDetails
  )
  if ($LASTEXITCODE -eq 0) {
    Add-GateResult -Gate $Gate -Status "PASS" -Details $OkDetails
    return $true
  }
  Add-GateResult -Gate $Gate -Status "FAIL" -Details "$FailDetails (exit=$LASTEXITCODE)"
  return $false
}

$pythonExe = Resolve-PythonExe
Add-GateResult -Gate "python-runtime" -Status "PASS" -Details $pythonExe

Write-Host "==> Unit tests"
& $pythonExe -m unittest discover -s tests -p "test_*.py" -v
Assert-LastExitCode -Gate "unit-tests" -OkDetails "All discovered tests passed." -FailDetails "Unit tests failed." | Out-Null

Write-Host "==> Profile list smoke test"
& $pythonExe main.py --list-profiles
Assert-LastExitCode -Gate "profile-list" -OkDetails "Profile listing succeeded." -FailDetails "Could not list profiles." | Out-Null

if (-not $SkipBuild) {
  Write-Host "==> Build executable"
  try {
    $buildArgs = @()
    if ($Sign -or $RequireSignature) { $buildArgs += "-Sign" }
    if (-not [string]::IsNullOrWhiteSpace($CertThumbprint)) { $buildArgs += @("-CertThumbprint", $CertThumbprint) }
    if (-not [string]::IsNullOrWhiteSpace($PfxPath)) { $buildArgs += @("-PfxPath", $PfxPath) }
    if (-not [string]::IsNullOrWhiteSpace($PfxPassword)) { $buildArgs += @("-PfxPassword", $PfxPassword) }
    if (-not [string]::IsNullOrWhiteSpace($TimestampUrl)) { $buildArgs += @("-TimestampUrl", $TimestampUrl) }
    if (-not [string]::IsNullOrWhiteSpace($SignToolPath)) { $buildArgs += @("-SignToolPath", $SignToolPath) }
    if (-not [string]::IsNullOrWhiteSpace($SignatureDescription)) { $buildArgs += @("-SignatureDescription", $SignatureDescription) }
    & "$PSScriptRoot\build_exe.ps1" @buildArgs
    if ($RequireSignature -or $Sign) {
      Add-GateResult -Gate "build-script" -Status "PASS" -Details "build_exe.ps1 completed with signing requested."
    }
    else {
      Add-GateResult -Gate "build-script" -Status "PASS" -Details "build_exe.ps1 completed."
    }
  }
  catch {
    Add-GateResult -Gate "build-script" -Status "FAIL" -Details $_.Exception.Message
  }
}
else {
  Add-GateResult -Gate "build-script" -Status "WARN" -Details "Skipped by request (-SkipBuild)."
}

$distExe = Join-Path $PSScriptRoot "dist\HelixSequenceWeaverBeta.exe"
if (Test-Path $distExe) {
  Add-GateResult -Gate "dist-artifact" -Status "PASS" -Details $distExe
}
else {
  Add-GateResult -Gate "dist-artifact" -Status "FAIL" -Details "Missing expected build artifact at $distExe"
}

if (Test-Path $distExe) {
  Write-Host "==> EXE help smoke test"
  & $distExe --help | Out-Null
  Assert-LastExitCode -Gate "exe-help" -OkDetails "Packaged EXE launches and prints help." -FailDetails "Packaged EXE --help failed." | Out-Null

  $versionInfo = (Get-Item $distExe).VersionInfo
  $missingMetadata = @()
  foreach ($field in @("FileVersion", "ProductVersion", "FileDescription", "CompanyName")) {
    if ([string]::IsNullOrWhiteSpace($versionInfo.$field)) {
      $missingMetadata += $field
    }
  }
  if ($missingMetadata.Count -eq 0) {
    Add-GateResult -Gate "exe-metadata" -Status "PASS" -Details "Version metadata is populated."
  }
  else {
    Add-GateResult -Gate "exe-metadata" -Status "FAIL" -Details ("Missing metadata fields: " + ($missingMetadata -join ", "))
  }

  $signature = Get-AuthenticodeSignature $distExe
  if ($signature.Status -eq "Valid") {
    Add-GateResult -Gate "exe-signature" -Status "PASS" -Details "Authenticode signature is valid."
  }
  else {
    $sigStatus = if ($RequireSignature) { "FAIL" } else { "WARN" }
    Add-GateResult -Gate "exe-signature" -Status $sigStatus -Details "Signature status: $($signature.Status)"
  }
}

$pyinstallerLog = Join-Path $PSScriptRoot "build\pyinstaller-build.log"
if (Test-Path $pyinstallerLog) {
  $tbbWarning = Select-String -Path $pyinstallerLog -Pattern "could not resolve 'tbb12.dll'" -SimpleMatch -ErrorAction SilentlyContinue
  if ($tbbWarning) {
    Add-GateResult -Gate "pyinstaller-warnings" -Status "WARN" -Details "Detected tbb12.dll dependency warning in PyInstaller build log."
  }
  else {
    Add-GateResult -Gate "pyinstaller-warnings" -Status "PASS" -Details "No tbb12.dll dependency warning detected in build log."
  }
}
else {
  Add-GateResult -Gate "pyinstaller-warnings" -Status "WARN" -Details "PyInstaller build log not found."
}

if ($IncludeEndToEnd) {
  if ((Test-Path $Template) -and (Test-Path $Audio) -and (Test-Path $distExe)) {
    $auditOutput = Join-Path $PSScriptRoot "build\release_audit_output"
    if (Test-Path $auditOutput) {
      Remove-Item -Path $auditOutput -Recurse -Force
    }
    New-Item -Path $auditOutput -ItemType Directory -Force | Out-Null

    Write-Host "==> End-to-end EXE sequencing smoke test"
    & $distExe --profile $Profile -- --no-prompt --no-save-settings --single --template $Template --audio $Audio --output-dir $auditOutput
    if (Assert-LastExitCode -Gate "end-to-end-run" -OkDetails "End-to-end run completed." -FailDetails "End-to-end run failed.") {
      $generated = Get-ChildItem -Path $auditOutput -Filter "*.xsq" -File -Recurse
      if ($generated.Count -gt 0) {
        Add-GateResult -Gate "end-to-end-artifact" -Status "PASS" -Details ("Generated XSQ count: " + $generated.Count)
      }
      else {
        Add-GateResult -Gate "end-to-end-artifact" -Status "FAIL" -Details "End-to-end run completed but no XSQ output was found."
      }
    }
  }
  else {
    Add-GateResult -Gate "end-to-end-run" -Status "FAIL" -Details "Missing template/audio/exe prerequisites for end-to-end smoke test."
  }
}
else {
  Add-GateResult -Gate "end-to-end-run" -Status "WARN" -Details "Skipped by request (use -IncludeEndToEnd)."
}

Write-Host ""
Write-Host "Release audit summary"
$results | Format-Table -AutoSize

if ($hasFailures) {
  Write-Host "`nRelease audit result: FAIL"
  exit 1
}

Write-Host "`nRelease audit result: PASS (with possible warnings)"
exit 0
