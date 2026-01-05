#!/bin/bash

# Motion Weave - One-Tap Production Deploy Script
# Usage: ./deploy.sh

set -e # Exit on error

echo "=================================================="
echo "   MOTION WEAVE - PRODUCTION DEPLOYMENT"
echo "=================================================="

# 1. Check Pre-requisites
echo "[1/4] Checking System..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Engine first."
    exit 1
fi

if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️  WARNING: nvidia-smi not found. Ensure NVIDIA drivers are installed if running on GPU."
fi

# 2. Setup Environment
echo "[2/4] Setting up Environment..."
mkdir -p models_cache
mkdir -p backend/outputs
mkdir -p backend/uploads

# 3. Build & Launch
echo "[3/4] Building Containers (This may take a few minutes)..."
docker-compose down # Cleanup old runs
docker-compose up --build -d

# 4. Validation
echo "[4/4] Validating Health..."
echo "Waiting for API to initialize..."
sleep 10
CONTAINER_ID=$(docker ps -qf "name=motion_weave_api")

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ API Container failed to start. Check logs with: docker-compose logs api"
    exit 1
fi

# Run the internal health check script inside the container
docker exec $CONTAINER_ID python scripts/health_check.py

echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "   UI Studio: http://localhost:3000"
echo "   API Docs:  http://localhost:8000/docs"
echo "=================================================="
