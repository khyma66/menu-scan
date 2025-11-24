#!/bin/bash

echo "🛑 Stopping servers..."

# Stop backend
if [ -f /tmp/backend.pid ]; then
    BACKEND_PID=$(cat /tmp/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID
        echo "✅ Backend stopped"
    fi
    rm /tmp/backend.pid
fi

# Stop frontend
if [ -f /tmp/frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID
        echo "✅ Frontend stopped"
    fi
    rm /tmp/frontend.pid
fi

# Also kill any remaining processes
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "next dev" 2>/dev/null

echo "✅ All servers stopped"

