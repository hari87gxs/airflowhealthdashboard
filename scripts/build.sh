#!/bin/bash

# Build Docker images locally for testing
# This script builds all Docker images without pushing to ECR

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Building backend image..."
docker build -t airflow-health-dashboard-backend:latest -f "$PROJECT_ROOT/backend/Dockerfile" "$PROJECT_ROOT/backend/"

echo "Building frontend image..."
docker build -t airflow-health-dashboard-frontend:latest -f "$PROJECT_ROOT/frontend/Dockerfile" "$PROJECT_ROOT/frontend/"

echo "Building scheduler image..."
docker build -t airflow-health-dashboard-scheduler:latest -f "$PROJECT_ROOT/scheduler/Dockerfile" "$PROJECT_ROOT/scheduler/"

echo "All images built successfully!"
echo ""
echo "To run locally with docker-compose:"
echo "  docker-compose up"
echo ""
echo "To test individual images:"
echo "  docker run -p 8000:8000 airflow-health-dashboard-backend:latest"
echo "  docker run -p 80:80 airflow-health-dashboard-frontend:latest"
