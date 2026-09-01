#!/bin/bash
set -e

echo "🌆 Starting City Operations Center..."

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set!"
    echo "   Set it with: export OPENAI_API_KEY=sk-your-key-here"
    exit 1
fi

# Default mode
MODE=${1:-unified}
PORT=${2:-8080}
FRONTEND_PORT=${3:-3000}

echo "Mode: $MODE"
echo "API Port: $PORT"
echo "Frontend Port: $FRONTEND_PORT"

# Start frontend server in background
echo "🖥️  Starting frontend dashboard on port $FRONTEND_PORT..."
python -m http.server $FRONTEND_PORT --directory frontend &
FRONTEND_PID=$!

# Start Pathway backend
echo "🚀 Starting Pathway API server on port $PORT..."
python src/main.py --mode $MODE &
BACKEND_PID=$!

echo ""
echo "✅ City Operations Center is running!"
echo "   Dashboard: http://localhost:$FRONTEND_PORT/dashboard.html"
echo "   API:       http://localhost:$PORT"
echo "   Docs:      http://localhost:$PORT/_schema"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $FRONTEND_PID $BACKEND_PID; exit" INT
wait
