#!/bin/bash

# Memotion Services Startup Script
# This script starts all necessary services for the Memotion application

echo "Starting Memotion Services..."

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/Scripts/activate  # For Windows Git Bash
# source .venv/bin/activate    # For Linux/Mac

# Check if required packages are installed
echo "Checking dependencies..."
python -c "import fastapi, uvicorn, sqlalchemy, pydantic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Missing required packages. Please install dependencies."
    echo "Run: pip install -r requirements.txt"
    exit 1
fi

# Check if database is accessible (optional)
echo "Checking database connection..."
# Add database check here if needed

# Start the main FastAPI server with pose detection
echo "Starting FastAPI server with pose detection..."
echo "Server will be available at: http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo "WebSocket endpoint: ws://localhost:8000/api/pose/stream/{session_id}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m app.main

# Deactivate virtual environment on exit
deactivate