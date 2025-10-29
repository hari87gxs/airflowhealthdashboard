#!/bin/bash

# Quick Start Script for Airflow Health Dashboard
# This script helps you get started quickly with the dashboard

set -e

echo "=================================="
echo "Airflow Health Dashboard - Quick Start"
echo "=================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp config/.env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and configure your Airflow credentials:"
    echo "   - AIRFLOW_BASE_URL"
    echo "   - AIRFLOW_USERNAME and AIRFLOW_PASSWORD (or AIRFLOW_API_TOKEN)"
    echo ""
    read -p "Press Enter to open .env for editing (or Ctrl+C to exit)..."
    ${EDITOR:-nano} .env
fi

# Check if frontend .env exists
if [ ! -f frontend/.env ]; then
    echo "Creating frontend .env..."
    cp frontend/.env.example frontend/.env
    echo "✅ Created frontend/.env"
fi

echo ""
echo "Starting services with Docker Compose..."
echo ""

# Build and start services
docker-compose up --build -d

echo ""
echo "=================================="
echo "✅ Services are starting up!"
echo "=================================="
echo ""
echo "It may take a minute for all services to be ready."
echo ""
echo "Access points:"
echo "  • Frontend:  http://localhost:3000"
echo "  • Backend:   http://localhost:8000"
echo "  • API Docs:  http://localhost:8000/docs"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
echo "Checking service health..."
sleep 5

# Check backend health
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend is not responding yet. It may still be starting up."
    echo "   Check logs with: docker-compose logs backend"
fi

echo ""
echo "=================================="
echo "Setup complete! 🎉"
echo "=================================="
