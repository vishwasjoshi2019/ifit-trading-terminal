#!/bin/bash
set -e

# Render and cloud container providers inject $PORT dynamically
PORT=${PORT:-8000}

echo "=== Starting IFIT Terminal Unified Engine on Port $PORT ==="

# Optional Streamlit Quant Lab in background
STREAMLIT_PORT=${STREAMLIT_PORT:-8501}
if [ -f "app.py" ]; then
    echo "Starting Quant Research Lab on port $STREAMLIT_PORT in background..."
    streamlit run app.py --server.port "$STREAMLIT_PORT" --server.address 0.0.0.0 --server.headless true &
fi

# Run FastAPI streaming server (serving WebSockets, REST APIs, and compiled React Terminal)
exec uvicorn backend.server:app --host 0.0.0.0 --port "$PORT"
