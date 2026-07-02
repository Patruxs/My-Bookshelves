@echo off
setlocal
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    set "PYTHON_CMD=venv\Scripts\python.exe"
) else (
    set "PYTHON_CMD=python"
)

"%PYTHON_CMD%" scripts\cli.py %*
exit /b %ERRORLEVEL%
