# Coastal-Alpine-Core - dual-platform installer (Windows / PowerShell)
#
# One-line:
# irm https://raw.githubusercontent.com/fivepanelhat/Coastal-Alpine-Core/main/install.ps1 | iex
#
# From a clone:
# powershell -ExecutionPolicy Bypass -File .\install.ps1
#
# Creates a virtualenv and installs coastal-alpine-core for Windows development
# of the hybrid Kiwi Edge stack (Weaver | Aether | portals).

$ErrorActionPreference = "Stop"

$RepoUrl = if ($env:CORE_REPO_URL) { $env:CORE_REPO_URL } else { "https://github.com/fivepanelhat/Coastal-Alpine-Core.git" }
$InstallDir = if ($env:CORE_HOME) { $env:CORE_HOME } else { Join-Path $env:USERPROFILE ".coastal-alpine-core-app" }
$VenvDir = Join-Path $InstallDir "venv"
$CoreTag = if ($env:CORE_TAG) { $env:CORE_TAG } else { "v0.5.4" }

function Info($m) { Write-Host "[core] $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[core] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[core] $m" -ForegroundColor Red; exit 1 }
function Require-Ok([string]$Step) {
 if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) {
 Fail "$Step failed (exit code $LASTEXITCODE)"
 }
}

$PythonBin = $null
foreach ($cand in @("python", "python3", "py")) {
 if (Get-Command $cand -ErrorAction SilentlyContinue) { $PythonBin = $cand; break }
}
if (-not $PythonBin) {
 Fail "Python 3.10+ is required. Install from https://www.python.org (Add to PATH) and re-run."
}
$PyVer = & $PythonBin -c "import sys; print('%d.%d' % sys.version_info[:2])"
& $PythonBin -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) { Fail "Python 3.10+ is required (found $PyVer)" }
Info "Using Python $PyVer ($PythonBin)"

$Editable = $false
if ((Test-Path "pyproject.toml") -and (Select-String -Path "pyproject.toml" -Pattern 'name = "coastal-alpine-core"' -Quiet)) {
 $SrcDir = (Get-Location).Path
 Info "Installing from current checkout: $SrcDir"
 $Editable = $true
} else {
 if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
 Fail "git is required. Install Git for Windows from https://git-scm.com or run from a clone."
 }
 New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
 $SrcDir = Join-Path $InstallDir "src"
 if (Test-Path (Join-Path $SrcDir ".git")) {
 Info "Updating existing checkout in $SrcDir"
 git -C $SrcDir pull --ff-only 2>$null
 } else {
 Info "Cloning $RepoUrl (tag $CoreTag if available)"
 git clone --depth 1 --branch $CoreTag $RepoUrl $SrcDir 2>$null
 if (-not (Test-Path $SrcDir)) {
 git clone --depth 1 $RepoUrl $SrcDir
 Require-Ok "git clone"
 }
 }
}

Info "Creating virtualenv at $VenvDir"
& $PythonBin -m venv $VenvDir
Require-Ok "venv create"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) { Fail "venv python not found at $VenvPython" }

& $VenvPython -m pip install --upgrade pip
Require-Ok "pip upgrade"

if ($Editable) {
 Info "Installing coastal-alpine-core[dev] (editable)"
 & $VenvPython -m pip install -e "$SrcDir[dev]"
 Require-Ok "pip install core[dev]"
} else {
 Info "Installing coastal-alpine-core from $SrcDir"
 & $VenvPython -m pip install $SrcDir
 Require-Ok "pip install core"
}

Info "Verifying import"
& $VenvPython -c "from coastal_alpine_core import SovereignOllamaClient; print('ok')"
Require-Ok "import coastal_alpine_core"

Write-Host ""
Info "Done. Activate the environment with:"
Write-Host " $VenvDir\Scripts\Activate.ps1"
Write-Host ""
Info "Quick check:"
Write-Host " python -c `"from coastal_alpine_core import SovereignOllamaClient; print('ok')`""
Write-Host ""
Info "Hybrid stack next steps:"
Write-Host " Weaver: https://github.com/fivepanelhat/Weaver"
Write-Host " Aether: https://github.com/fivepanelhat/Aether"
Write-Host " Stack: https://github.com/fivepanelhat/coastal-alpine-stack"
