@echo off
echo ============================================================
echo   ANSH AI JOBHUNTER -- Starting System Services
echo ============================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Please run setup.bat first!
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Starting FastAPI Backend (Port 8000)...
start "Ansh AI JobHunter - Backend" /B uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

echo Waiting for backend API to initialize...
timeout /t 3 /nobreak >nul

echo Starting Streamlit Dashboard (Port 8501)...
echo.
echo ============================================================
echo   ANSH AI JOBHUNTER is now running:
echo     - Dashboard: http://localhost:8501
echo     - API Docs:  http://localhost:8000/docs
echo ============================================================
echo.

streamlit run frontend/streamlit_app.py --server.port 8501

pause
