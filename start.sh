#!/bin/bash

echo "📦 Checking dependencies..."
npm install

echo "🚀 Starting GCP PCA Mock App server in the background..."
nohup node server.js > server.log 2>&1 &
echo $! > server.pid

echo "✅ Server is running!"
echo "🌐 Open your browser to: http://localhost:4000"
echo "📝 Logs are being saved to server.log"
echo "🛑 Use ./stop.sh to shut it down."