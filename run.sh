#!/bin/bash

# LEVIATHAN Fishing Copilot - Startup Script
# This script starts both the backend (FastAPI) and frontend (React) servers

echo "🐟 Starting LEVIATHAN Fishing Copilot..."
echo "========================================"

# Check if .env exists in backend
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: backend/.env not found!"
    echo "Please create backend/.env with your GEMINI_API_KEY"
    echo ""
fi

# Initialize and activate conda environment
echo "🔧 Activating conda environment 'sushi'..."

# Try different conda initialization methods
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif [ -f "/opt/miniconda3/etc/profile.d/conda.sh" ]; then
    source "/opt/miniconda3/etc/profile.d/conda.sh"
elif [ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]; then
    source "/opt/anaconda3/etc/profile.d/conda.sh"
else
    echo "⚠️  Could not find conda.sh. Please run 'conda init bash' first."
    exit 1
fi

conda activate sushi

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate conda environment 'sushi'"
    echo "Please ensure the 'sushi' environment exists"
    exit 1
fi

# Start backend server
echo "📡 Starting backend server (FastAPI)..."
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to initialize
sleep 2

# Start frontend server
echo "🎨 Starting frontend server (React)..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ LEVIATHAN is running!"
echo "========================================"
echo "Backend API:  http://localhost:8000"
echo "Frontend App: http://localhost:3000"
echo "API Docs:     http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping LEVIATHAN..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All servers stopped"
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait
