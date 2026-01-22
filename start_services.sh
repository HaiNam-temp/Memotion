#!/bin/bash

# Memotion Services Startup Script
# This script starts all necessary services for the Memotion application
# Works on both local development and Docker container

echo "=========================================="
echo "   MEMOTION Backend Startup Script"
echo "=========================================="

# Set environment variables for MediaPipe
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/app/mediapipe/mediapipe_be"
export POSE_DETECTION_ENABLED=true
export QT_QPA_PLATFORM=offscreen
export MPLBACKEND=Agg

echo "PYTHONPATH: $PYTHONPATH"

# Check if running in Docker (no venv needed)
if [ -f "/.dockerenv" ]; then
    echo "Running in Docker container..."
else
    # Check if virtual environment exists for local development
    if [ -d ".venv" ]; then
        echo "Activating virtual environment..."
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        elif [ -f ".venv/Scripts/activate" ]; then
            source .venv/Scripts/activate
        fi
    else
        echo "Warning: Virtual environment not found. Using system Python."
    fi
fi

# Check if required packages are installed
echo ""
echo "Checking core dependencies..."
python -c "import fastapi, uvicorn, sqlalchemy, pydantic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Missing core packages. Please install dependencies."
    echo "Run: pip install -r app/requirements.txt"
    exit 1
fi
echo "✓ Core dependencies OK"

# Check MediaPipe/OpenCV
echo "Checking MediaPipe/OpenCV..."
python -c "import cv2; import mediapipe; print('  OpenCV:', cv2.__version__); print('  MediaPipe:', mediapipe.__version__)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "WARNING: MediaPipe/OpenCV not available. Pose detection will be disabled."
else
    echo "✓ MediaPipe/OpenCV OK"
fi

# Check MediaPipe BE module
echo "Checking MediaPipe BE module..."
python -c "from app.mediapipe.mediapipe_be import MemotionEngine; print('  MemotionEngine:', 'OK')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "WARNING: MediaPipe BE module not available."
else
    echo "✓ MediaPipe BE module OK"
fi

# Create necessary directories
mkdir -p logs static/uploads/exercise models

echo ""
echo "=========================================="
echo "Starting FastAPI server..."
echo "=========================================="
echo "Server: http://0.0.0.0:${PORT:-8005}"
echo "API docs: http://localhost:${PORT:-8005}/docs"
echo "WebSocket: ws://localhost:${PORT:-8005}/api/pose/sessions/{id}/ws"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="

# Start the main FastAPI server
python -m app.main

# Cleanup on exit
if [ -d ".venv" ]; then
    deactivate 2>/dev/null || true
fi