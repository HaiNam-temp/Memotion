@echo off
REM Memotion Services Startup Script for Windows
REM This script starts all necessary services for the Memotion application

echo ============================================
echo    MEMOTION Backend Services Startup
echo ============================================
echo.

REM Set working directory
cd /d "%~dp0"

REM Set environment variables - Include mediapipe_be for relative imports
set PYTHONPATH=%CD%;%CD%\app\mediapipe\mediapipe_be;%PYTHONPATH%

REM Check if virtual environment exists
if not exist ".venv" (
    echo [ERROR] Virtual environment not found. Please run setup first.
    echo         Run: python -m venv .venv
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/4] Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if required packages are installed
echo [2/4] Checking dependencies...
python -c "import fastapi, uvicorn, sqlalchemy, pydantic, mediapipe" 2>nul
if errorlevel 1 (
    echo [ERROR] Missing required packages. Please install dependencies.
    echo         Run: pip install -r requirements.txt
    pause
    exit /b 1
)
echo       Dependencies OK

REM Check MediaPipe engine
echo [3/4] Checking MediaPipe engine...
python -c "from app.mediapipe.mediapipe_be.service.engine_service import MemotionEngine; print('       MediaPipe engine OK')" 2>nul
if errorlevel 1 (
    echo [WARNING] MediaPipe engine not available. Pose detection may be limited.
)

REM Start the main FastAPI server
echo [4/4] Starting FastAPI server...
echo.
echo ============================================
echo    Server Information:
echo ============================================
echo    Main API:      http://localhost:8000
echo    API Docs:      http://localhost:8000/docs
echo    Health Check:  http://localhost:8000/api/healthcheck
echo    Pose API:      http://localhost:8000/api/pose/health
echo    WebSocket:     ws://localhost:8000/api/pose/sessions/{id}/ws
echo ============================================
echo.
echo Press Ctrl+C to stop the server
echo.

python -m app.main

REM Deactivate virtual environment on exit
call deactivate