Param(
  [switch]$Clean,
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

function Resolve-SignToolExe {
  param(
    [string]$OverridePath
  )

  if (-not [string]::IsNullOrWhiteSpace($OverridePath)) {
    if (-not (Test-Path $OverridePath)) {
      throw "Provided SignToolPath does not exist: $OverridePath"
    }
    return (Resolve-Path $OverridePath).Path
  }

  $command = Get-Command signtool.exe -ErrorAction SilentlyContinue
  if (-not $command) {
    $command = Get-Command signtool -ErrorAction SilentlyContinue
  }
  if ($command) {
    return $command.Source
  }

  $kitRoots = @(
    "$env:ProgramFiles(x86)\Windows Kits\10\bin",
    "$env:ProgramFiles\Windows Kits\10\bin"
  )
  foreach ($root in $kitRoots) {
    if (-not (Test-Path $root)) {
      continue
    }
    $x64Match = Get-ChildItem -Path $root -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -match "\\x64\\signtool\.exe$" } |
      Sort-Object FullName -Descending |
      Select-Object -First 1
    if ($x64Match) {
      return $x64Match.FullName
    }
    $anyMatch = Get-ChildItem -Path $root -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
      Sort-Object FullName -Descending |
      Select-Object -First 1
    if ($anyMatch) {
      return $anyMatch.FullName
    }
  }

  throw "Could not find signtool.exe. Install Windows SDK or provide -SignToolPath."
}

function Find-CodeSigningCertThumbprint {
  $stores = @("Cert:\CurrentUser\My", "Cert:\LocalMachine\My")
  foreach ($store in $stores) {
    if (-not (Test-Path $store)) {
      continue
    }
    $cert = Get-ChildItem -Path $store -ErrorAction SilentlyContinue |
      Where-Object {
        $_.HasPrivateKey -and
        $_.NotAfter -gt (Get-Date) -and
        ($_.EnhancedKeyUsageList | Where-Object { $_.FriendlyName -eq "Code Signing" })
      } |
      Sort-Object NotAfter -Descending |
      Select-Object -First 1
    if ($cert) {
      return $cert.Thumbprint
    }
  }
  return $null
}

function Invoke-CodeSigning {
  param(
    [string]$ExePath,
    [string]$Thumbprint,
    [string]$PfxFile,
    [string]$PfxPass
  )

  if (-not (Test-Path $ExePath)) {
    throw "Cannot sign missing executable: $ExePath"
  }

  $signtoolExe = Resolve-SignToolExe -OverridePath $SignToolPath
  $signArgs = @(
    "sign",
    "/fd",
    "SHA256",
    "/td",
    "SHA256",
    "/d",
    $SignatureDescription
  )

  if (-not [string]::IsNullOrWhiteSpace($TimestampUrl)) {
    $signArgs += @("/tr", $TimestampUrl)
  }

  if (-not [string]::IsNullOrWhiteSpace($PfxFile)) {
    if (-not (Test-Path $PfxFile)) {
      throw "PFX file not found: $PfxFile"
    }
    $signArgs += @("/f", (Resolve-Path $PfxFile).Path)
    if (-not [string]::IsNullOrWhiteSpace($PfxPass)) {
      $signArgs += @("/p", $PfxPass)
    }
  }
  elseif (-not [string]::IsNullOrWhiteSpace($Thumbprint)) {
    $signArgs += @("/sha1", $Thumbprint)
  }
  else {
    throw "Signing requested but no certificate source was provided."
  }

  $signArgs += $ExePath

  Write-Host "Signing executable with: $signtoolExe"
  & $signtoolExe @signArgs
  if ($LASTEXITCODE -ne 0) {
    throw "signtool failed with exit code $LASTEXITCODE."
  }

  $signature = Get-AuthenticodeSignature $ExePath
  if ($signature.Status -ne "Valid") {
    throw "Code signing completed but signature status is '$($signature.Status)'."
  }
  Write-Host "Code signing complete: $ExePath"
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
$buildDir = Join-Path $PSScriptRoot "build"
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
$pyinstallerLog = Join-Path $buildDir "pyinstaller-build.log"
$pyinstallerStdOut = Join-Path $buildDir "pyinstaller-build.stdout.log"
Write-Host "PyInstaller log: $pyinstallerLog"
$pyinstallerArgs = @(
  "-m",
  "PyInstaller",
  "--noconfirm",
  "--clean",
  ".\dream_sequence_weaver.spec"
)
$process = Start-Process `
  -FilePath $pythonExe `
  -ArgumentList $pyinstallerArgs `
  -WorkingDirectory $PSScriptRoot `
  -NoNewWindow `
  -Wait `
  -PassThru `
  -RedirectStandardOutput $pyinstallerStdOut `
  -RedirectStandardError $pyinstallerLog
if ($process.ExitCode -ne 0) {
  if (Test-Path $pyinstallerLog) {
    Write-Host "Last 40 lines from PyInstaller log:"
    Get-Content $pyinstallerLog -Tail 40
  }
  throw "PyInstaller failed with exit code $($process.ExitCode). See $pyinstallerLog for details."
}

$distExe = Join-Path $PSScriptRoot "dist\HelixSequenceWeaverBeta.exe"
$signingRequested = $Sign -or (-not [string]::IsNullOrWhiteSpace($CertThumbprint)) -or (-not [string]::IsNullOrWhiteSpace($PfxPath))
if (-not [string]::IsNullOrWhiteSpace($CertThumbprint)) {
  $CertThumbprint = $CertThumbprint.Replace(" ", "")
}
if (Test-Path $distExe) {
  if ($signingRequested) {
    if ([string]::IsNullOrWhiteSpace($PfxPath) -and [string]::IsNullOrWhiteSpace($CertThumbprint)) {
      $autoThumbprint = Find-CodeSigningCertThumbprint
      if ([string]::IsNullOrWhiteSpace($autoThumbprint)) {
        throw "Signing requested but no code-signing certificate was found in CurrentUser/LocalMachine personal stores."
      }
      $CertThumbprint = $autoThumbprint.Replace(" ", "")
      Write-Host "Auto-selected code-signing certificate thumbprint: $CertThumbprint"
    }
    Invoke-CodeSigning -ExePath $distExe -Thumbprint $CertThumbprint -PfxFile $PfxPath -PfxPass $PfxPassword
  }
  Copy-Item $distExe (Join-Path $PSScriptRoot "HelixSequenceWeaverBeta.exe") -Force
  Write-Host "Build complete: $distExe"
  Write-Host "Copied customer-ready exe to: $(Join-Path $PSScriptRoot 'HelixSequenceWeaverBeta.exe')"
} else {
  Write-Host "Build finished, but executable was not found at expected path: $distExe"
}
