#!/bin/bash

# Menu OCR Services Startup Script
# This script starts all services using Docker Compose

set -e

echo "🚀 Starting Menu OCR Services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Start services
echo "🔄 Starting Redis and FastAPI services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check Redis health
echo "🔍 Checking Redis health..."
if docker exec menu-ocr-redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
    exit 1
fi

# Check API health
echo "🔍 Checking API health..."
if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ API is responding"
else
    echo "❌ API health check failed"
    echo "📋 Checking API logs:"
    docker logs menu-ocr-api | tail -20
    exit 1
fi

echo ""
echo "🎉 All services started successfully!"
echo ""
echo "📊 Service Status:"
echo "  • Redis:    redis://localhost:6379"
echo "  • API:      http://localhost:8000"
echo "  • Docs:     http://localhost:8000/docs"
echo ""
echo "🛑 To stop services: docker-compose down"
echo "📝 To view logs: docker-compose logs -f"