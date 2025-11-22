#!/bin/bash

echo "========================================"
echo "Starting Live Analyser"
echo "========================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap CTRL+C
trap cleanup INT TERM

echo "[1/2] Starting Backend Server..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..
sleep 3

echo "[2/2] Starting Frontend Server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "Both servers are running!"
echo "Backend:  http://localhost:5001"
echo "Frontend: http://localhost:3000"
echo "========================================"
echo ""
echo "Press CTRL+C to stop all servers..."

# Wait for processes
wait
