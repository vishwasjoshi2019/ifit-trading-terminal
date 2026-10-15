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
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose default HTTP/WebSocket port
EXPOSE 8000 8501 10000

RUN chmod +x scripts/start.sh

# Run unified entrypoint supporting dynamic $PORT from Render, Railway, or Fly
CMD ["/bin/bash", "scripts/start.sh"]
