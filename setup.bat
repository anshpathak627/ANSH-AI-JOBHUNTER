@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   ANSH AI JOBHUNTER -- Windows 11 Automated Setup Script
echo ============================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in system PATH.
    echo Please install Python 3.11 or higher and run setup again.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [1/7] Python detected: %PYVER%

:: 2. Create venv
if not exist ".venv" (
    echo [2/7] Creating virtual environment (.venv)...
    python -m venv .venv
) else (
    echo [2/7] Virtual environment (.venv) already exists.
)

:: 3. Activate venv & upgrade pip
echo [3/7] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [4/7] Installing dependencies from requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt

:: 4. Create directories
echo [5/7] Creating data and log directories...
if not exist "data" mkdir data
if not exist "data\resumes" mkdir data\resumes
if not exist "data\tailored" mkdir data\tailored
if not exist "data\screenshots" mkdir data\screenshots
if not exist "logs" mkdir logs

:: 5. Copy .env
if not exist ".env" (
    echo [6/7] Creating .env from .env.example...
    copy .env.example .env >nul
) else (
    echo [6/7] .env configuration file already exists.
)

:: 6. Initialize database
echo [7/7] Initializing database and company registry...
python database\init_db.py

:: 7. Install Playwright Chromium
echo Installing Playwright Chromium browser binary...
playwright install chromium

echo.
echo ============================================================
echo   SETUP COMPLETED SUCCESSFULLY!
echo ============================================================
echo   To launch the application, run:
echo       run.bat
echo ============================================================
echo.
pause
