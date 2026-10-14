# Multi-stage production container for IFIT Terminal (Streamlit + FastAPI WebSockets)
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501 \
    BACKEND_PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "fastapi==0.110.0" "uvicorn[standard]" "websockets>=12.0" "pydantic>=2.0"

# Copy application source code
COPY . .

# Expose Streamlit and FastAPI WebSocket ports
EXPOSE 8501 8000

# Start both FastAPI backend daemon and Streamlit frontend
CMD uvicorn backend.server:app --host 0.0.0.0 --port 8000 & \
    streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
