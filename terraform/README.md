# Terraform Infrastructure Documentation

This directory contains Terraform configuration for deploying the Airflow Health Dashboard to AWS.

## Architecture Overview

The infrastructure includes:

- **VPC**: Multi-AZ VPC with public and private subnets
- **ECS Fargate**: Containerized services (backend, frontend, scheduler)
- **Application Load Balancer**: Path-based routing with optional HTTPS
- **ElastiCache Redis**: Distributed caching layer
- **ECR**: Container image registry
- **Secrets Manager**: Secure credential storage
- **Auto Scaling**: CPU and memory-based scaling
- **CloudWatch**: Centralized logging and monitoring

## Prerequisites

1. **AWS CLI** installed and configured
2. **Terraform** >= 1.0 installed
3. **Docker** installed for building images
4. **AWS IAM** permissions for:
   - VPC, Subnet, Internet Gateway, NAT Gateway
   - ECS, ECR, Application Load Balancer
   - ElastiCache, Secrets Manager
   - IAM roles and policies
   - CloudWatch logs

## Quick Start

### 1. Configure Variables

Copy the example variables file:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
# Required
airflow_url = "https://your-airflow-instance.com"
airflow_username = "admin"
airflow_password = "your-password"
azure_openai_endpoint = "https://your-openai.openai.azure.com/"
azure_openai_key = "your-key"
azure_openai_deployment = "gpt-4"

# Optional - for Slack notifications
slack_webhook_url = "https://hooks.slack.com/services/..."
dashboard_url = "https://dashboard.example.com"
```

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

### 3. Plan Infrastructure

```bash
terraform plan
```

Review the planned changes carefully.

### 4. Apply Infrastructure

```bash
terraform apply
```

Type `yes` when prompted.

### 5. Deploy Application

Use the deployment script:

```bash
cd ..
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

Or manually:

```bash
# Get ECR URLs
BACKEND_ECR=$(terraform output -raw ecr_backend_repository_url)
FRONTEND_ECR=$(terraform output -raw ecr_frontend_repository_url)
SCHEDULER_ECR=$(terraform output -raw ecr_scheduler_repository_url)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $BACKEND_ECR

# Build and push images
docker build -t $BACKEND_ECR:latest -f ../backend/Dockerfile ../backend/
docker push $BACKEND_ECR:latest

docker build -t $FRONTEND_ECR:latest -f ../frontend/Dockerfile ../frontend/
docker push $FRONTEND_ECR:latest

docker build -t $SCHEDULER_ECR:latest -f ../scheduler/Dockerfile ../scheduler/
docker push $SCHEDULER_ECR:latest

# Update ECS services
CLUSTER=$(terraform output -raw ecs_cluster_name)
aws ecs update-service --cluster $CLUSTER --service $(terraform output -raw backend_service_name) --force-new-deployment
aws ecs update-service --cluster $CLUSTER --service $(terraform output -raw frontend_service_name) --force-new-deployment
```

## Terraform Files

- **main.tf**: Provider configuration and Terraform settings
- **variables.tf**: Input variable definitions
- **vpc.tf**: VPC, subnets, NAT gateways, route tables
- **security_groups.tf**: Security groups for ALB, ECS, Redis
- **ecr.tf**: ECR repositories with lifecycle policies
- **elasticache.tf**: Redis cluster configuration
- **secrets.tf**: Secrets Manager for credentials
- **ecs.tf**: ECS cluster, task definitions, services
- **alb.tf**: Application Load Balancer and target groups
- **autoscaling.tf**: Auto scaling policies
- **outputs.tf**: Output values (URLs, endpoints)

## Key Resources

### VPC Configuration

- CIDR: 10.0.0.0/16
- 2 Availability Zones
- Public subnets (10.0.0.0/24, 10.0.1.0/24)
- Private subnets (10.0.10.0/24, 10.0.11.0/24)
- NAT Gateways in each AZ

### ECS Services

**Backend:**
- CPU: 512 (0.5 vCPU)
- Memory: 1024 MB
- Port: 8000
- Auto scaling: 1-4 tasks

**Frontend:**
- CPU: 256 (0.25 vCPU)
- Memory: 512 MB
- Port: 80
- Auto scaling: 1-3 tasks

**Scheduler:**
- CPU: 256 (0.25 vCPU)
- Memory: 512 MB
- No load balancer (background service)
- Desired count: 1

### Load Balancer Rules

- `/` → Frontend
- `/api/*` → Backend
- `/health` → Backend
- `/docs` → Backend API documentation

### Auto Scaling Policies

- **CPU Target**: 70% utilization
- **Memory Target**: 80% utilization
- **Scale Out Cooldown**: 60 seconds
- **Scale In Cooldown**: 300 seconds

## Outputs

After applying, you'll get:

```bash
# Get dashboard URL
terraform output dashboard_url

# Get API URL
terraform output api_url

# Get ECR URLs
terraform output ecr_backend_repository_url
terraform output ecr_frontend_repository_url
terraform output ecr_scheduler_repository_url

# Get Redis endpoint
terraform output redis_endpoint
```

## Cost Estimation

Approximate monthly costs (us-east-1):

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| ECS Fargate (Backend) | 0.5 vCPU, 1GB RAM, 1 task | ~$15 |
| ECS Fargate (Frontend) | 0.25 vCPU, 0.5GB RAM, 1 task | ~$7 |
| ECS Fargate (Scheduler) | 0.25 vCPU, 0.5GB RAM, 1 task | ~$7 |
| NAT Gateway (2 AZs) | Data processing + hourly | ~$65 |
| Application Load Balancer | Hourly + LCU charges | ~$25 |
| ElastiCache (t3.micro) | Single node | ~$12 |
| ECR | Image storage (< 10GB) | ~$1 |
| CloudWatch Logs | 7 days retention | ~$3 |
| **Total** | | **~$135/month** |

*Costs may vary based on usage and region*

## Security Best Practices

1. **Secrets Management**: All credentials stored in AWS Secrets Manager
2. **Network Isolation**: Private subnets for ECS tasks and Redis
3. **Security Groups**: Least-privilege access rules
4. **HTTPS**: Optional SSL/TLS with ACM certificate
5. **Image Scanning**: ECR scan on push enabled
6. **IAM Roles**: Task-specific IAM roles with minimal permissions

## Updating the Infrastructure

### Update Terraform Configuration

```bash
# Make changes to .tf files
terraform plan
terraform apply
```

### Update Application Code

```bash
# Run deployment script
./scripts/deploy.sh
```

### Update Individual Service

```bash
# Backend only
docker build -t $BACKEND_ECR:latest -f backend/Dockerfile backend/
docker push $BACKEND_ECR:latest
aws ecs update-service --cluster $CLUSTER --service backend --force-new-deployment
```

## Monitoring

### CloudWatch Logs

```bash
# View backend logs
aws logs tail /ecs/airflow-health-dashboard --follow --filter-pattern "backend"

# View scheduler logs
aws logs tail /ecs/airflow-health-dashboard --follow --filter-pattern "scheduler"
```

### ECS Service Status

```bash
# Check service status
aws ecs describe-services --cluster $CLUSTER --services backend frontend
```

### Auto Scaling Activity

```bash
# View scaling activities
aws application-autoscaling describe-scaling-activities \
  --service-namespace ecs \
  --resource-id service/$CLUSTER/backend
```

## Troubleshooting

### Service Won't Start

1. Check CloudWatch logs for errors
2. Verify Secrets Manager values
3. Check security group rules
4. Verify Redis connectivity

```bash
# Get task failures
aws ecs describe-tasks --cluster $CLUSTER --tasks $(aws ecs list-tasks --cluster $CLUSTER --service-name backend --query 'taskArns[0]' --output text)
```

### Health Check Failures

```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn $TARGET_GROUP_ARN
```

### Can't Connect to Redis

1. Verify security group allows port 6379
2. Check subnet configuration
3. Verify Redis cluster is running

```bash
# Check Redis status
aws elasticache describe-cache-clusters --cache-cluster-id airflow-health-dashboard-redis --show-cache-node-info
```

## Cleanup

To destroy all infrastructure:

```bash
# Delete all resources
terraform destroy

# Manually delete ECR images first if needed
aws ecr batch-delete-image \
  --repository-name airflow-health-dashboard-backend \
  --image-ids imageTag=latest
```

**Warning**: This will delete all data and cannot be undone!

## Advanced Configuration

### Custom Domain with HTTPS

1. Create ACM certificate:
```bash
aws acm request-certificate \
  --domain-name dashboard.example.com \
  --validation-method DNS
```

2. Add to terraform.tfvars:
```hcl
domain_name = "dashboard.example.com"
certificate_arn = "arn:aws:acm:..."
```

3. Apply changes:
```bash
terraform apply
```

4. Create Route 53 record:
```bash
# Get ALB DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)
ALB_ZONE=$(terraform output -raw alb_zone_id)

# Create A record (alias)
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "dashboard.example.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "'$ALB_ZONE'",
          "DNSName": "'$ALB_DNS'",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'
```

### Multi-Region Deployment

For disaster recovery or global deployment:

1. Create separate workspaces:
```bash
terraform workspace new us-west-2
terraform workspace select us-west-2
```

2. Use region-specific tfvars:
```bash
terraform apply -var-file=us-west-2.tfvars
```

## Support

For issues or questions:
- Check AWS CloudWatch logs
- Review ECS task events
- Consult AWS documentation
- Open GitHub issue
