#!/usr/bin/env pwsh
# activate.ps1 — PowerShell venv activator for Agent Foundry.
# Cross-platform: works on Windows PowerShell 5+ and PowerShell 7+ (incl. macOS/Linux).
#
# Usage:
#   pwsh -File scripts/activate.ps1
# Or from a PowerShell session:
#   . ./scripts/activate.ps1
#
# This script does NOT call Set-ExecutionPolicy — it respects whatever
# policy the parent shell enforces. If activation fails, fall back to
# activate.bat (Windows CMD) or activate.sh (POSIX bash).

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = Split-Path -Parent $ScriptDir
$Venv = Join-Path $RepoRoot ".venv"

if (-not (Test-Path $Venv)) {
    Write-Host "No .venv found at $Venv" -ForegroundColor Red
    Write-Host "Run: python -m venv .venv && .venv/Scripts/pip install -e ." -ForegroundColor Yellow
    exit 1
}

# Detect platform
$IsWin = $IsWindows -or ($env:OS -eq "Windows_NT")

# Locate the activate script
if ($IsWin) {
    $ActivateScript = Join-Path $Venv "Scripts\Activate.ps1"
} else {
    $ActivateScript = Join-Path $Venv "bin\activate"
}

if (-not (Test-Path $ActivateScript)) {
    Write-Host "Activate script not found at $ActivateScript" -ForegroundColor Red
    exit 1
}

# Source it (no Set-ExecutionPolicy override — uses the parent policy)
. $ActivateScript

if ($env:VIRTUAL_ENV) {
    if ($IsWin) {
        $env:AGENT_FOUNDRY_PY = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    } else {
        $env:AGENT_FOUNDRY_PY = Join-Path $env:VIRTUAL_ENV "bin\python"
    }
    Write-Host "Agent Foundry venv activated (Python: $env:AGENT_FOUNDRY_PY)" -ForegroundColor Green
}