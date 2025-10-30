#!/bin/bash

# Airflow Health Dashboard - AWS Deployment Script
# This script automates the deployment of the dashboard to AWS

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-prod}"
PROJECT_NAME="airflow-health-dashboard"

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured. Please run 'aws configure'."
        exit 1
    fi
    
    print_info "All prerequisites met!"
}

# Function to initialize Terraform
init_terraform() {
    print_info "Initializing Terraform..."
    cd "$PROJECT_ROOT/terraform"
    terraform init
    print_info "Terraform initialized!"
}

# Function to create infrastructure
create_infrastructure() {
    print_info "Creating AWS infrastructure..."
    cd "$PROJECT_ROOT/terraform"
    
    # Check if terraform.tfvars exists
    if [ ! -f "terraform.tfvars" ]; then
        print_error "terraform.tfvars not found. Please create it with required variables."
        print_info "See terraform/terraform.tfvars.example for reference."
        exit 1
    fi
    
    terraform plan -out=tfplan
    
    read -p "Do you want to apply this plan? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        terraform apply tfplan
        print_info "Infrastructure created successfully!"
    else
        print_warn "Infrastructure creation cancelled."
        exit 0
    fi
}

# Function to get ECR repository URLs
get_ecr_urls() {
    cd "$PROJECT_ROOT/terraform"
    BACKEND_ECR_URL=$(terraform output -raw ecr_backend_repository_url)
    FRONTEND_ECR_URL=$(terraform output -raw ecr_frontend_repository_url)
    SCHEDULER_ECR_URL=$(terraform output -raw ecr_scheduler_repository_url)
    
    print_info "ECR URLs:"
    print_info "  Backend: $BACKEND_ECR_URL"
    print_info "  Frontend: $FRONTEND_ECR_URL"
    print_info "  Scheduler: $SCHEDULER_ECR_URL"
}

# Function to login to ECR
ecr_login() {
    print_info "Logging in to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "${BACKEND_ECR_URL%%/*}"
    print_info "ECR login successful!"
}

# Function to build and push Docker images
build_and_push_images() {
    print_info "Building and pushing Docker images..."
    
    # Build and push backend
    print_info "Building backend image..."
    cd "$PROJECT_ROOT"
    docker build -t "$BACKEND_ECR_URL:latest" -f backend/Dockerfile backend/
    docker push "$BACKEND_ECR_URL:latest"
    print_info "Backend image pushed!"
    
    # Build and push frontend
    print_info "Building frontend image..."
    docker build -t "$FRONTEND_ECR_URL:latest" -f frontend/Dockerfile frontend/
    docker push "$FRONTEND_ECR_URL:latest"
    print_info "Frontend image pushed!"
    
    # Build and push scheduler
    print_info "Building scheduler image..."
    docker build -t "$SCHEDULER_ECR_URL:latest" -f scheduler/Dockerfile scheduler/
    docker push "$SCHEDULER_ECR_URL:latest"
    print_info "Scheduler image pushed!"
    
    print_info "All images built and pushed successfully!"
}

# Function to update ECS services
update_services() {
    print_info "Updating ECS services..."
    cd "$PROJECT_ROOT/terraform"
    
    CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
    BACKEND_SERVICE=$(terraform output -raw backend_service_name)
    FRONTEND_SERVICE=$(terraform output -raw frontend_service_name)
    
    # Force new deployment
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$BACKEND_SERVICE" \
        --force-new-deployment \
        --region "$AWS_REGION" > /dev/null
    
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$FRONTEND_SERVICE" \
        --force-new-deployment \
        --region "$AWS_REGION" > /dev/null
    
    # Update scheduler if it exists
    SCHEDULER_SERVICE=$(terraform output -raw scheduler_service_name 2>/dev/null || echo "")
    if [ -n "$SCHEDULER_SERVICE" ] && [ "$SCHEDULER_SERVICE" != "Not created (Slack not configured)" ]; then
        aws ecs update-service \
            --cluster "$CLUSTER_NAME" \
            --service "$SCHEDULER_SERVICE" \
            --force-new-deployment \
            --region "$AWS_REGION" > /dev/null
        print_info "Scheduler service updated!"
    fi
    
    print_info "ECS services updated!"
}

# Function to wait for deployment
wait_for_deployment() {
    print_info "Waiting for deployment to complete..."
    cd "$PROJECT_ROOT/terraform"
    
    CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
    BACKEND_SERVICE=$(terraform output -raw backend_service_name)
    FRONTEND_SERVICE=$(terraform output -raw frontend_service_name)
    
    print_info "Waiting for backend service..."
    aws ecs wait services-stable \
        --cluster "$CLUSTER_NAME" \
        --services "$BACKEND_SERVICE" \
        --region "$AWS_REGION"
    
    print_info "Waiting for frontend service..."
    aws ecs wait services-stable \
        --cluster "$CLUSTER_NAME" \
        --services "$FRONTEND_SERVICE" \
        --region "$AWS_REGION"
    
    print_info "Deployment completed successfully!"
}

# Function to display dashboard URL
show_dashboard_url() {
    cd "$PROJECT_ROOT/terraform"
    DASHBOARD_URL=$(terraform output -raw dashboard_url)
    
    print_info "========================================="
    print_info "Deployment Complete!"
    print_info "========================================="
    print_info "Dashboard URL: $DASHBOARD_URL"
    print_info "API Docs: ${DASHBOARD_URL}/docs"
    print_info "========================================="
}

# Main deployment flow
main() {
    print_info "Starting AWS deployment for $PROJECT_NAME..."
    
    check_prerequisites
    init_terraform
    create_infrastructure
    get_ecr_urls
    ecr_login
    build_and_push_images
    update_services
    wait_for_deployment
    show_dashboard_url
    
    print_info "Deployment completed successfully! 🎉"
}

# Run main function
main "$@"
