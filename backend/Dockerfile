# Backend Dockerfile for Motion Weave AI Engine
# Base image with CUDA 12.1 support (Required for PyTorch 2.x + SVD)
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TORCH_HOME=/app/models \
    HF_HOME=/app/models/huggingface

WORKDIR /app

# Install System Dependencies
# ffmpeg: For video processing
# git: For cloning repos
# libgl1: Required by OpenCV
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    git \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python3 -> python
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Copy Requirements
COPY backend/requirements.txt /app/backend/requirements.txt
COPY ai_engine/requirements.txt /app/ai_engine/requirements.txt

# Install Python Dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/ai_engine/requirements.txt

# Copy Codebase
COPY . /app

# Create Model Directory (Volume Mount Target)
RUN mkdir -p /app/models

# Expose API Port
EXPOSE 8000

# Healthcheck Script
COPY scripts/health_check.py /app/scripts/health_check.py

# Start Command
# 1. Runs health check
# 2. Starts FastAPI
CMD ["sh", "-c", "python scripts/health_check.py && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
