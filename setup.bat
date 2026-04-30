@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
cd /d "%~dp0"

:: ================================================================
::  My Bookshelves -- One-Command Setup (Windows)
:: ================================================================
::  Usage: cmd /c setup.bat   OR   double-click setup.bat
:: ================================================================

echo.
echo ================================================================
echo   My Bookshelves -- Setup
echo ================================================================
echo.

:: -- Step 1: Check Python --
echo [1/5] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo    [ERROR] Python not found! Please install Python 3.8+
    echo            https://www.python.org/downloads/
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do (
    echo    [OK] Python %%v detected
)

:: -- Step 2: Create virtual environment + install dependencies --
echo.
echo [2/5] Creating virtual environment and installing Python dependencies...
if not exist "venv\Scripts\python.exe" (
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo    [ERROR] Failed to create virtual environment
        exit /b 1
    )
)
set "PYTHON_CMD=venv\Scripts\python.exe"
"%PYTHON_CMD%" -m pip install --upgrade pip >nul 2>&1
"%PYTHON_CMD%" -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo    [ERROR] Failed to install dependencies
    exit /b 1
)
echo    [OK] All dependencies installed

:: -- Step 3: Create project directories --
echo.
echo [3/5] Creating project directories...
if not exist "Books\" mkdir Books
if not exist "Inbox\" mkdir Inbox
if not exist "site\assets\covers\" mkdir site\assets\covers
echo    [OK] Books/  Inbox/  site/assets/covers/

:: -- Step 4: Verify installation --
echo.
echo [4/5] Verifying setup...
"%PYTHON_CMD%" -c "import fitz; print('    [OK] PyMuPDF', fitz.version[0])"
if %ERRORLEVEL% neq 0 echo    [FAIL] PyMuPDF not working
"%PYTHON_CMD%" -c "from PIL import Image; print('    [OK] Pillow', Image.__version__)"
if %ERRORLEVEL% neq 0 echo    [FAIL] Pillow not working
"%PYTHON_CMD%" -c "import docx; print('    [OK] python-docx')"
if %ERRORLEVEL% neq 0 echo    [FAIL] python-docx not working

:: -- Step 5: Optional reset + doctor --
echo.
echo [5/5] Running repo doctor...
if /I "%~1"=="--reset-sample-data" (
    echo    [WARN] Resetting sample data because --reset-sample-data was provided
    "%PYTHON_CMD%" scripts\reset_library.py --force
) else (
    echo    [OK] Skipping reset. Existing library data is preserved.
)
"%PYTHON_CMD%" scripts\cli.py doctor --base-dir .

:: -- Done --
echo.
echo ================================================================
echo   Setup complete!
echo ================================================================
echo.
echo   View locally:
echo     python -m http.server 8080
echo     Open http://localhost:8080/site/
echo.
echo   Add books:
echo     1. Drop files into Inbox/
echo     2. venv\Scripts\python.exe scripts\cli.py generate --base-dir .
echo.
echo ================================================================
echo.

endlocal
