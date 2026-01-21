@echo off
REM Memotion Services Startup Script for Windows
REM This script starts all necessary services for the Memotion application

echo Starting Memotion Services...

REM Set environment variables
set PYTHONPATH=%PYTHONPATH%;%CD%

REM Check if virtual environment exists
if not exist ".venv" (
    echo Virtual environment not found. Please run setup first.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if required packages are installed
echo Checking dependencies...
python -c "import fastapi, uvicorn, sqlalchemy, pydantic" 2>nul
if errorlevel 1 (
    echo Missing required packages. Please install dependencies.
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if database is accessible (optional)
echo Checking database connection...
REM Add database check here if needed

REM Start the main FastAPI server with pose detection
echo Starting FastAPI server with pose detection...
echo Server will be available at: http://localhost:8000
echo API docs: http://localhost:8000/docs
echo WebSocket endpoint: ws://localhost:8000/api/pose/stream/{session_id}
echo.
echo Press Ctrl+C to stop the server
echo.

python -m app.main

REM Deactivate virtual environment on exit
call deactivate