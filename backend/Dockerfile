# Use official lightweight Python image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace

WORKDIR /workspace

# Install system dependencies (build-essential needed for compiling psycopg2 if binary fails)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements list
COPY backend/requirements.txt /workspace/backend/requirements.txt

# Install backend dependencies
RUN pip install --no-cache-dir -r /workspace/backend/requirements.txt

# Copy backend source code
COPY backend /workspace/backend

EXPOSE 8000

# Run FastAPI server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
