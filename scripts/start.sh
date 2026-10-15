#!/bin/bash
set -e

# Render, Railway, and cloud container providers inject $PORT dynamically
PORT=${PORT:-8501}
TERMINAL_MODE=${TERMINAL_MODE:-QUANT}

echo "=== Starting IFIT Production Engine (Mode: $TERMINAL_MODE) on Port $PORT ==="

if [ "$TERMINAL_MODE" = "STREAMING_REACT" ]; then
    echo "Starting React Bloomberg + FastAPI Streaming Engine on port $PORT..."
    if [ -f "app.py" ]; then
        streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true &
    fi
    exec uvicorn backend.server:app --host 0.0.0.0 --port "$PORT"
else
    echo "Starting Full 16-Workspace Quant Trading Terminal (Streamlit) on port $PORT..."
    # Run FastAPI streaming server on port 8000 in background
    uvicorn backend.server:app --host 0.0.0.0 --port 8000 &
    exec streamlit run app.py \
        --server.port "$PORT" \
        --server.address 0.0.0.0 \
        --server.headless true \
        --browser.gatherUsageStats false \
        --server.enableCORS false \
        --server.enableXsrfProtection false
fi
