#!/bin/bash

# Algorzen Data Quality Toolkit - Dashboard Startup Script
# This script starts both the API server and React dashboard

echo "🚀 Starting Algorzen Data Quality Toolkit Dashboard..."

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        echo "✅ Port $1 is available"
        return 0
    fi
}

# Check if ports are available
echo "🔍 Checking port availability..."
check_port 8000 || exit 1
check_port 3000 || exit 1

# Start API server in background
echo "🌐 Starting API server on port 8000..."
cd "$(dirname "$0")"
algorzen-dqt api-server --host 127.0.0.1 --port 8000 &
API_PID=$!

# Wait for API server to start
echo "⏳ Waiting for API server to start..."
sleep 5

# Check if API server is running
if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "✅ API server is running"
else
    echo "❌ API server failed to start"
    kill $API_PID 2>/dev/null
    exit 1
fi

# Start React dashboard
echo "🎨 Starting React dashboard on port 3000..."
cd frontend/algorzen-dashboard
npm start &
REACT_PID=$!

echo ""
echo "🎉 Dashboard startup complete!"
echo "📍 API Server: http://127.0.0.1:8000"
echo "📍 React Dashboard: http://localhost:3000"
echo "📊 API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for user to stop
trap "echo '🛑 Stopping services...'; kill $API_PID $REACT_PID 2>/dev/null; exit" INT
wait
