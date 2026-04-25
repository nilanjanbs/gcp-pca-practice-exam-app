#!/bin/bash

if [ -f server.pid ]; then
    PID=$(cat server.pid)
    echo "🛑 Stopping server (PID: $PID)..."
    kill $PID
    rm server.pid
    echo "✅ Server stopped."
else
    echo "⚠️ server.pid not found. Searching for process on port 3000..."
    PID=$(lsof -t -i:3000)
    if [ -z "$PID" ]; then
        echo "✅ No server running on port 3000."
    else
        kill $PID
        echo "✅ Server on port 3000 stopped."
    fi
fi