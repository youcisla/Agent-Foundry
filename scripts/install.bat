@echo off
REM install.bat — Windows CMD wrapper that delegates to install.js (Node).
REM Mirrors ECC's architecture: one Node entry, this CMD wrapper just dispatches.

setlocal

REM Find Node.js in PATH or standard locations
where node >nul 2>nul
if %errorlevel% equ 0 (
    set "NODE=node"
) else (
    if exist "%ProgramFiles%\nodejs\node.exe" set "NODE=%ProgramFiles%\nodejs\node.exe"
    if exist "%LOCALAPPDATA%\Programs\nodejs\node.exe" set "NODE=%LOCALAPPDATA%\Programs\nodejs\node.exe"
)

if not defined NODE (
    echo Node.js ^>=18 is required. Install from https://nodejs.org/
    exit /b 1
)

REM Resolve the install.js path relative to this script
set "SCRIPT_DIR=%~dp0"

REM Forward all args
"%NODE%" "%SCRIPT_DIR%install.js" %*

endlocal