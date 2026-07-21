#!/usr/bin/env pwsh
# install.ps1 — PowerShell wrapper that delegates to install.js (Node).
# Mirrors ECC's architecture: one Node entry, this PS wrapper just dispatches.

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$InstallJs = Join-Path $ScriptDir "install.js"

# Find Node — try PATH, then standard install paths, then common aliases
$Node = $null
if (Get-Command node -ErrorAction SilentlyContinue) { $Node = "node" }
elseif (Get-Command node18 -ErrorAction SilentlyContinue) { $Node = "node18" }
elseif (Get-Command nodejs -ErrorAction SilentlyContinue) { $Node = "nodejs" }
elseif (Test-Path "/c/Program Files/nodejs/node.exe") { $Node = "/c/Program Files/nodejs/node.exe" }
elseif (Test-Path "/usr/local/bin/node") { $Node = "/usr/local/bin/node" }

if (-not $Node) {
    Write-Host "Node.js >=18 is required. Install from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Forward all args
& $Node $InstallJs $args