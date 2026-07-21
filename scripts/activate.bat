@echo off
REM activate.bat — Windows CMD venv activator for Agent Foundry.
REM
REM Use this from cmd.exe / Windows Terminal (CMD profile):
REM   scripts\activate.bat
REM
REM After activation, `python` is on PATH and points at .venv\Scripts\python.exe.

if not exist ".venv\Scripts\activate.bat" (
    echo No .venv found at %CD%\.venv
    echo Run: python -m venv .venv ^&^& .venv\Scripts\pip install -e .
    exit /b 1
)

call ".venv\Scripts\activate.bat"

if defined VIRTUAL_ENV (
    set "AGENT_FOUNDRY_PY=%VIRTUAL_ENV%\Scripts\python.exe"
    echo Agent Foundry venv activated (Python: %AGENT_FOUNDRY_PY%)
)