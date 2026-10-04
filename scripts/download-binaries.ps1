# =============================================================================
# Career Forge — download the 4 Executa binaries from the GitHub Release built
# by .github/workflows/build-executa-binaries.yml into
#   executas\career-engine-python\dist\
#
# Usage (from the project root, in PowerShell):
#   pwsh .\scripts\download-binaries.ps1 -Version 1.0.1 -Repo <owner>/<repo>
# =============================================================================
param(
    [string]$Version = "1.0.1",
    [string]$Repo = "REPLACE-ME/career-forge"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$dir  = Join-Path $root "executas\career-engine-python\dist"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$base = "https://github.com/$Repo/releases/download/career-engine-v$Version"

$files = @(
    "career-engine-$Version-darwin-arm64.tar.gz",
    "career-engine-$Version-darwin-x86_64.tar.gz",
    "career-engine-$Version-linux-x86_64.tar.gz",
    "career-engine-$Version-windows-x86_64.zip"
)

foreach ($f in $files) {
    $out = Join-Path $dir $f
    Write-Host "downloading $f"
    Invoke-WebRequest -Uri "$base/$f" -OutFile $out
    $size = (Get-Item $out).Length
    if ($size -lt 1024) { throw "$f is only $size bytes - the download failed. Check the repo/tag/version." }
    Write-Host ("  -> {0:N0} bytes" -f $size)
}

Write-Host ""
Write-Host "All 4 archives are in: $dir" -ForegroundColor Green
Write-Host "Next: anna-app apps publish"
