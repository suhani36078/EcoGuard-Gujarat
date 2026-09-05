FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker cache layer)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .
# Copy agents and ml modules (imported by backend)
COPY agents/ /app/../agents/
COPY ml/ /app/../ml/

# Expose port
EXPOSE 8000

# Default: seed and start
CMD ["python", "start.py", "--seed"]
