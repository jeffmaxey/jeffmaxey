<#
.SYNOPSIS
    Package the PyInstaller output into a Windows MSI installer using WiX Toolset.

.DESCRIPTION
    This script:
    1. Optionally calls build_exe.ps1 to (re)build the executable.
    2. Discovers or downloads the WiX Toolset (dotnet tool or standalone).
    3. Runs "wix build" (WiX v4) or "candle + light" (WiX v3) against
       installer\Product.wxs to produce an MSI.

.PARAMETER SkipExeBuild
    Skip the PyInstaller step (use previously built dist\ output).

.PARAMETER WixVersion
    WiX major version to use: 3 or 4 (default: 4).

.PARAMETER OutputDir
    Directory for final MSI file.  Defaults to "dist".

.EXAMPLE
    .\scripts\build_msi.ps1
    .\scripts\build_msi.ps1 -SkipExeBuild -WixVersion 3

.NOTES
    WiX v4 is installed as a .NET global tool:
        dotnet tool install --global wix
    WiX v3 binaries must be in PATH or installed at default location.
#>

[CmdletBinding()]
param(
    [switch]$SkipExeBuild,
    [ValidateSet(3, 4)]
    [int]$WixVersion = 4,
    [string]$OutputDir = "dist"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step([string]$msg) {
    Write-Host "`n==> $msg" -ForegroundColor Cyan
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot

# -----------------------------------------------------------------------
# 1. Build executable (unless skipped)
# -----------------------------------------------------------------------
if (-not $SkipExeBuild) {
    Write-Step "Building executable"
    & "$PSScriptRoot\build_exe.ps1" -OutputDir $OutputDir
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$ExeDir = Join-Path $OutputDir "WindowsCleaner"
if (-not (Test-Path $ExeDir)) {
    Write-Error "Executable directory not found: $ExeDir.  Run build_exe.ps1 first."
    exit 1
}

# -----------------------------------------------------------------------
# 2. Collect version
# -----------------------------------------------------------------------
$Version = "1.0.0"
try {
    $VerLine = (python -c "from windows_cleaner_gui import __version__; print(__version__)") 2>&1
    if ($VerLine -match "^\d+\.\d+\.\d+") { $Version = $VerLine.Trim() }
} catch {}
Write-Host "App version: $Version"

# -----------------------------------------------------------------------
# 3. Ensure WiX is available
# -----------------------------------------------------------------------
if ($WixVersion -eq 4) {
    Write-Step "Checking WiX v4 (dotnet tool)"
    $wixExe = (Get-Command wix -ErrorAction SilentlyContinue)?.Source
    if (-not $wixExe) {
        Write-Step "Installing WiX v4 as a .NET global tool"
        dotnet tool install --global wix
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install WiX v4.  Install .NET SDK first: https://dotnet.microsoft.com/download"
            exit 1
        }
        # Refresh PATH
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + $env:PATH
    }
    Write-Host "WiX found: $(wix --version)"
} else {
    Write-Step "Checking WiX v3 (candle / light)"
    if (-not (Get-Command candle -ErrorAction SilentlyContinue)) {
        $wix3Default = "C:\Program Files (x86)\WiX Toolset v3.11\bin"
        if (Test-Path $wix3Default) {
            $env:PATH += ";$wix3Default"
        } else {
            Write-Error "WiX v3 not found.  Install from https://github.com/wixtoolset/wix3/releases"
            exit 1
        }
    }
    Write-Host "candle: $(candle -? 2>&1 | Select-Object -First 1)"
}

# -----------------------------------------------------------------------
# 4. Build MSI
# -----------------------------------------------------------------------
$MsiPath = Join-Path $OutputDir "WindowsCleaner-$Version.msi"
$WxsPath = Join-Path $RepoRoot "installer\Product.wxs"

if ($WixVersion -eq 4) {
    Write-Step "Building MSI with WiX v4"
    wix build $WxsPath `
        -d "SourceDir=$ExeDir" `
        -d "Version=$Version" `
        -o $MsiPath
    if ($LASTEXITCODE -ne 0) { Write-Error "WiX build failed."; exit $LASTEXITCODE }
} else {
    Write-Step "Building MSI with WiX v3 (candle + light)"
    $ObjDir = Join-Path $OutputDir "wix_obj"
    New-Item -ItemType Directory -Force $ObjDir | Out-Null

    candle -nologo `
        -dSourceDir="$ExeDir" `
        -dVersion="$Version" `
        -out "$ObjDir\" `
        $WxsPath
    if ($LASTEXITCODE -ne 0) { Write-Error "candle failed."; exit $LASTEXITCODE }

    light -nologo `
        -ext WixUIExtension `
        -out $MsiPath `
        "$ObjDir\Product.wixobj"
    if ($LASTEXITCODE -ne 0) { Write-Error "light failed."; exit $LASTEXITCODE }
}

Write-Host "`n✅  MSI created: $MsiPath" -ForegroundColor Green
Pop-Location
