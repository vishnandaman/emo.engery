# Dockerfile for Intelligent Content API
# This file defines how to build a Docker image for the application

# Use Python 3.11 slim image as base
# Slim images are smaller and faster
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Set environment variables
# Prevents Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# These are needed for MySQL client and building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first (for better Docker layer caching)
# If requirements don't change, Docker can reuse cached layers
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 8000 (default FastAPI/Uvicorn port)
EXPOSE 8000

# Command to run the application
# uvicorn is the ASGI server for FastAPI
# --host 0.0.0.0 makes it accessible from outside container
# --reload enables auto-reload in development (remove in production)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

