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
  $buildSplat = @{}
  if ($Clean) {
    $buildSplat["Clean"] = $true
  }
  if ($Sign) { $buildSplat["Sign"] = $true }
  if (-not [string]::IsNullOrWhiteSpace($CertThumbprint)) { $buildSplat["CertThumbprint"] = $CertThumbprint }
  if (-not [string]::IsNullOrWhiteSpace($PfxPath)) { $buildSplat["PfxPath"] = $PfxPath }
  if (-not [string]::IsNullOrWhiteSpace($PfxPassword)) { $buildSplat["PfxPassword"] = $PfxPassword }
  if (-not [string]::IsNullOrWhiteSpace($TimestampUrl)) { $buildSplat["TimestampUrl"] = $TimestampUrl }
  if (-not [string]::IsNullOrWhiteSpace($SignToolPath)) { $buildSplat["SignToolPath"] = $SignToolPath }
  if (-not [string]::IsNullOrWhiteSpace($SignatureDescription)) { $buildSplat["SignatureDescription"] = $SignatureDescription }
  & "$PSScriptRoot\build_exe.ps1" @buildSplat
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

$commitRef = ""
try {
  $commitRef = (git -C $PSScriptRoot rev-parse --short HEAD 2>$null).Trim()
}
catch {
  $commitRef = ""
}

$checksumsPath = Join-Path $bundleDir "release_checksums.txt"
$hashLines = Get-ChildItem -Path $bundleDir -File |
  Sort-Object Name |
  ForEach-Object {
    $hash = (Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "{0} *{1}" -f $hash, $_.Name
  }
$checksumsText = @(
  "Dream Sequence Weaver release checksums"
  "Generated (local): $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
  "Bundle: $(Split-Path -Leaf $bundleDir)"
  "Source commit: $(if ([string]::IsNullOrWhiteSpace($commitRef)) { '<unknown>' } else { $commitRef })"
  ""
  "Verify with PowerShell:"
  "  Get-FileHash .\HelixSequenceWeaverBeta.exe -Algorithm SHA256"
  ""
  "Format: SHA256 *filename"
  ""
) + $hashLines
Set-Content -Path $checksumsPath -Value $checksumsText -Encoding UTF8

$releaseNotesTemplateSource = Join-Path $PSScriptRoot "RELEASE_NOTES_TEMPLATE.md"
$releaseNotesTemplateDest = Join-Path $bundleDir "RELEASE_NOTES_TEMPLATE.md"
$resolvedVersion = if ([string]::IsNullOrWhiteSpace($versionInfo.ProductVersion)) { "<version>" } else { $versionInfo.ProductVersion }
$resolvedCommit = if ([string]::IsNullOrWhiteSpace($commitRef)) { "<commit-hash>" } else { $commitRef }
if (Test-Path $releaseNotesTemplateSource) {
  $releaseNotes = Get-Content -Path $releaseNotesTemplateSource -Raw
  $releaseNotes = $releaseNotes.Replace("{{RELEASE_DATE}}", (Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"))
  $releaseNotes = $releaseNotes.Replace("{{BUNDLE_NAME}}", (Split-Path -Leaf $bundleDir))
  $releaseNotes = $releaseNotes.Replace("{{EXE_NAME}}", "HelixSequenceWeaverBeta.exe")
  $releaseNotes = $releaseNotes.Replace("{{EXE_VERSION}}", $resolvedVersion)
  $releaseNotes = $releaseNotes.Replace("{{SOURCE_COMMIT}}", $resolvedCommit)
  $releaseNotes = $releaseNotes.Replace("{{CHECKSUM_FILE}}", "release_checksums.txt")
  Set-Content -Path $releaseNotesTemplateDest -Value $releaseNotes -Encoding UTF8
}
else {
  $fallbackNotes = @(
    "# Dream Sequence Weaver Release Notes Template"
    ""
    "## Release Metadata"
    "- Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
    "- Bundle: $(Split-Path -Leaf $bundleDir)"
    "- EXE: HelixSequenceWeaverBeta.exe"
    "- Version: $resolvedVersion"
    "- Source commit: $resolvedCommit"
    ""
    "## Highlights"
    "- "
    ""
    "## Quality Checks"
    "- [ ] release_audit.ps1 -RequireSignature"
    "- [ ] Manual launch smoke test"
    ""
    "## Artifacts"
    "- HelixSequenceWeaverBeta.exe"
    "- release_checksums.txt"
    ""
    "## Notes for Users"
    "- Verify SHA256 checksums from release_checksums.txt before launch."
  )
  Set-Content -Path $releaseNotesTemplateDest -Value $fallbackNotes -Encoding UTF8
}

Write-Host "Customer bundle ready:"
Write-Host "  $bundleDir"
