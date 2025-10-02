#!/bin/bash
# Quick start script for Sonar Assist

echo "=================================================="
echo "🎣 SONAR ASSIST - Real-Time Fishing Copilot"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Must be run from backend/sonar_assist directory"
    echo "   Run: cd backend/sonar_assist && ./run_sonar_assist.sh"
    exit 1
fi

# Check for .env file
if [ ! -f "../.env" ]; then
    echo "⚠️  Warning: .env file not found in backend/"
    echo "   Voice and AI features may be disabled"
    echo ""
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi

# Check dependencies
echo "📦 Checking dependencies..."
python3 -c "import cv2, mss, yaml, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip3 install -r ../requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

echo "✓ Dependencies OK"
echo ""

# Check ffmpeg (optional)
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  Warning: ffmpeg not found - voice output may not work"
    echo "   Install: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
    echo ""
fi

# Run the application
echo "🚀 Starting Sonar Assist..."
echo ""
python3 app.py
