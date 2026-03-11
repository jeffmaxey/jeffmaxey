<#
.SYNOPSIS
    Build the Windows Cleaner GUI into a Windows executable using PyInstaller.

.DESCRIPTION
    This script:
    1. Creates / activates a virtual environment.
    2. Installs all required dependencies (windows_cleaner backend + GUI extras).
    3. Runs PyInstaller using the project spec file.
    4. Optionally runs a smoke-test on the resulting executable.

.PARAMETER OutputDir
    Directory where build artifacts are placed.  Defaults to "dist".

.PARAMETER VenvDir
    Virtual environment directory.  Defaults to ".venv".

.PARAMETER SmokeTest
    When specified, launches the built exe for 3 seconds as a smoke test.

.EXAMPLE
    .\scripts\build_exe.ps1
    .\scripts\build_exe.ps1 -OutputDir C:\build -SmokeTest

.NOTES
    Requires Python 3.11+ and pip in PATH.
    Run from the repository root directory.
#>

[CmdletBinding()]
param(
    [string]$OutputDir = "dist",
    [string]$VenvDir   = ".venv",
    [switch]$SmokeTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------
function Write-Step([string]$msg) {
    Write-Host "`n==> $msg" -ForegroundColor Cyan
}

function Invoke-Checked([string]$desc, [scriptblock]$block) {
    Write-Step $desc
    & $block
    if ($LASTEXITCODE -ne 0) {
        Write-Error "FAILED: $desc (exit code $LASTEXITCODE)"
        exit $LASTEXITCODE
    }
}

# -----------------------------------------------------------------------
# Resolve repo root (script lives in scripts/)
# -----------------------------------------------------------------------
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
Write-Host "Repository root: $RepoRoot" -ForegroundColor Yellow

# -----------------------------------------------------------------------
# 1. Python check
# -----------------------------------------------------------------------
Write-Step "Checking Python version"
$PyVersion = python --version 2>&1
Write-Host $PyVersion
if (-not ($PyVersion -match "Python 3\.(1[1-9]|[2-9]\d)")) {
    Write-Warning "Python 3.11+ is required.  Found: $PyVersion"
}

# -----------------------------------------------------------------------
# 2. Virtual environment
# -----------------------------------------------------------------------
if (-not (Test-Path "$VenvDir\Scripts\activate.ps1")) {
    Write-Step "Creating virtual environment at $VenvDir"
    python -m venv $VenvDir
}

Write-Step "Activating virtual environment"
& "$VenvDir\Scripts\Activate.ps1"

# -----------------------------------------------------------------------
# 3. Install dependencies
# -----------------------------------------------------------------------
Invoke-Checked "Upgrading pip" {
    python -m pip install --upgrade pip --quiet
}

Invoke-Checked "Installing project with GUI extras" {
    pip install -e ".[gui]" --quiet
}

Invoke-Checked "Installing PyInstaller" {
    pip install "pyinstaller>=6.0" --quiet
}

# -----------------------------------------------------------------------
# 4. Clean previous build
# -----------------------------------------------------------------------
Write-Step "Cleaning previous build artefacts"
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path $OutputDir) { Remove-Item -Recurse -Force $OutputDir }

# -----------------------------------------------------------------------
# 5. Run PyInstaller
# -----------------------------------------------------------------------
Invoke-Checked "Running PyInstaller" {
    pyinstaller windows_cleaner_gui.spec --distpath $OutputDir --workpath build --noconfirm
}

$ExePath = Join-Path $OutputDir "WindowsCleaner\WindowsCleaner.exe"
if (-not (Test-Path $ExePath)) {
    # Fallback: single-file build
    $ExePath = Join-Path $OutputDir "WindowsCleaner.exe"
}

Write-Host "`n✅  Build complete: $ExePath" -ForegroundColor Green

# -----------------------------------------------------------------------
# 6. Optional smoke test
# -----------------------------------------------------------------------
if ($SmokeTest) {
    Write-Step "Running smoke test (3 s)"
    $proc = Start-Process -FilePath $ExePath -PassThru
    Start-Sleep -Seconds 3
    if (-not $proc.HasExited) {
        $proc.Kill()
        Write-Host "✅  Smoke test passed (process started and stayed alive)." -ForegroundColor Green
    } else {
        Write-Warning "Process exited early with code $($proc.ExitCode)."
    }
}

Pop-Location
