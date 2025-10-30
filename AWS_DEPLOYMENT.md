# AWS Deployment Guide - Airflow Health Dashboard

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [AWS Services Used](#aws-services-used)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Infrastructure as Code](#infrastructure-as-code)
6. [Monitoring & Logging](#monitoring--logging)
7. [Cost Estimation](#cost-estimation)
8. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

### AWS Production Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Cloud (Region: us-east-1)                │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Route 53 (DNS)                              │  │
│  │              dashboard.yourcompany.com                         │  │
│  └────────────────────────┬──────────────────────────────────────┘  │
│                           │                                          │
│  ┌────────────────────────▼──────────────────────────────────────┐  │
│  │         Application Load Balancer (ALB)                       │  │
│  │  - HTTPS/SSL Termination (ACM Certificate)                    │  │
│  │  - Health Checks                                              │  │
│  │  - Path-based Routing                                         │  │
│  └─────┬──────────────────────────────────────┬─────────────────┘  │
│        │                                       │                     │
│  ┌─────▼──────────────────┐         ┌────────▼────────────────┐    │
│  │  Target Group:         │         │  Target Group:          │    │
│  │  Frontend (Port 80)    │         │  Backend (Port 8000)    │    │
│  └─────┬──────────────────┘         └────────┬────────────────┘    │
│        │                                      │                      │
│  ┌─────▼──────────────────────────────────────▼─────────────────┐  │
│  │              ECS Cluster (Fargate)                            │  │
│  │                                                                │  │
│  │  ┌──────────────────┐         ┌──────────────────────────┐   │  │
│  │  │ Frontend Service │         │   Backend Service        │   │  │
│  │  │ - 2 Tasks        │         │   - 2 Tasks              │   │  │
│  │  │ - Auto-scaling   │         │   - Auto-scaling         │   │  │
│  │  │ - Nginx + React  │         │   - FastAPI + Python     │   │  │
│  │  └──────────────────┘         └─────────┬────────────────┘   │  │
│  │                                          │                     │  │
│  │                              ┌───────────▼──────────────────┐ │  │
│  │                              │ Scheduler Service (Cron)     │ │  │
│  │                              │ - EventBridge Triggered      │ │  │
│  │                              │ - 10 AM & 7 PM Reports       │ │  │
│  │                              │ - Slack Notifications        │ │  │
│  │                              └──────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │             ElastiCache Redis (In-Memory Cache)              │  │
│  │  - Multi-AZ Replication                                      │  │
│  │  - Automatic Failover                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │        Secrets Manager (Credentials Storage)                 │  │
│  │  - Airflow Credentials                                       │  │
│  │  - Azure OpenAI API Keys                                     │  │
│  │  - Slack Webhook URL                                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │             CloudWatch (Monitoring & Logging)                │  │
│  │  - Application Logs                                          │  │
│  │  - Metrics & Alarms                                          │  │
│  │  - Dashboard Visualization                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │         EventBridge (Scheduled Events)                       │  │
│  │  - 10:00 AM UTC Daily Report                                │  │
│  │  - 07:00 PM UTC Daily Report                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              ECR (Container Registry)                        │  │
│  │  - Frontend Docker Images                                    │  │
│  │  - Backend Docker Images                                     │  │
│  │  - Scheduler Docker Images                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                               │
                               │ HTTPS API Calls
                               ▼
                    ┌──────────────────────┐
                    │  External Services   │
                    │  - Airflow Instance  │
                    │  - Azure OpenAI      │
                    │  - Slack API         │
                    └──────────────────────┘
```

---

## 📋 Prerequisites

### Required AWS Accounts & Permissions
- AWS Account with administrative access
- IAM user with permissions for:
  - ECS (Fargate)
  - ECR (Container Registry)
  - ALB (Load Balancer)
  - Route 53 (DNS)
  - Secrets Manager
  - CloudWatch
  - ElastiCache
  - EventBridge
  - ACM (Certificate Manager)

### Required Tools
```bash
# Install AWS CLI
brew install awscli  # macOS
# OR
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Docker
brew install docker  # macOS

# Install Terraform (for IaC)
brew install terraform

# Verify installations
aws --version        # Should be 2.x
docker --version     # Should be 20.x+
terraform --version  # Should be 1.x
```

### Configure AWS CLI
```bash
aws configure
# AWS Access Key ID: <your-access-key>
# AWS Secret Access Key: <your-secret-key>
# Default region: us-east-1
# Default output format: json
```

### Domain & SSL
- Registered domain (e.g., yourcompany.com)
- Access to DNS management (Route 53 or external DNS provider)

---

## 🔧 AWS Services Used

| Service | Purpose | Monthly Cost (Est.) |
|---------|---------|---------------------|
| **ECS Fargate** | Container orchestration | $50-100 |
| **Application Load Balancer** | Traffic distribution | $20-30 |
| **ElastiCache Redis** | Distributed caching | $15-40 |
| **ECR** | Docker image storage | $5-10 |
| **Route 53** | DNS management | $0.50 |
| **ACM** | SSL certificates | Free |
| **Secrets Manager** | Secure credential storage | $1-5 |
| **CloudWatch** | Logging & monitoring | $10-20 |
| **EventBridge** | Scheduled triggers | $1 |
| **Data Transfer** | Outbound traffic | $10-30 |
| **TOTAL** | **Estimated Monthly** | **$112-236** |

*Costs are estimates and may vary based on usage patterns*

---

## 🚀 Step-by-Step Deployment

### Phase 1: Container Registry Setup (15 minutes)

#### Step 1.1: Create ECR Repositories
```bash
# Navigate to project directory
cd /Users/harikrishnan.r/Downloads/airflow-health-dashboard

# Set variables
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
APP_NAME="airflow-health-dashboard"

# Create ECR repositories
aws ecr create-repository \
    --repository-name ${APP_NAME}-frontend \
    --region ${AWS_REGION}

aws ecr create-repository \
    --repository-name ${APP_NAME}-backend \
    --region ${AWS_REGION}

aws ecr create-repository \
    --repository-name ${APP_NAME}-scheduler \
    --region ${AWS_REGION}

echo "ECR Repositories created successfully!"
```

#### Step 1.2: Login to ECR
```bash
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
```

#### Step 1.3: Build and Push Frontend
```bash
# Build frontend image
cd frontend
docker build -t ${APP_NAME}-frontend:latest .

# Tag for ECR
docker tag ${APP_NAME}-frontend:latest \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}-frontend:latest

# Push to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}-frontend:latest

cd ..
```

#### Step 1.4: Build and Push Backend
```bash
# Build backend image
cd backend
docker build -t ${APP_NAME}-backend:latest .

# Tag for ECR
docker tag ${APP_NAME}-backend:latest \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}-backend:latest

# Push to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}-backend:latest

cd ..
```

---

### Phase 2: Secrets Management (10 minutes)

#### Step 2.1: Store Credentials in Secrets Manager
```bash
# Create Airflow credentials secret
aws secretsmanager create-secret \
    --name ${APP_NAME}/airflow-credentials \
    --description "Airflow API credentials" \
    --secret-string '{
        "AIRFLOW_BASE_URL": "https://airflow.sgbank.st",
        "AIRFLOW_USERNAME": "your_username",
        "AIRFLOW_PASSWORD": "your_password"
    }' \
    --region ${AWS_REGION}

# Create Azure OpenAI credentials secret
aws secretsmanager create-secret \
    --name ${APP_NAME}/azure-openai-credentials \
    --description "Azure OpenAI API credentials" \
    --secret-string '{
        "AZURE_OPENAI_API_KEY": "your_api_key",
        "AZURE_OPENAI_ENDPOINT": "https://your-endpoint.openai.azure.com",
        "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4o"
    }' \
    --region ${AWS_REGION}

# Create Slack webhook secret
aws secretsmanager create-secret \
    --name ${APP_NAME}/slack-webhook \
    --description "Slack webhook URL for notifications" \
    --secret-string '{
        "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    }' \
    --region ${AWS_REGION}

echo "Secrets stored successfully!"
```

---

### Phase 3: Networking Setup (15 minutes)

#### Step 3.1: Create VPC (if not using default)
```bash
# Create VPC
aws ec2 create-vpc \
    --cidr-block 10.0.0.0/16 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value='${APP_NAME}'-vpc}]' \
    --region ${AWS_REGION}

# Save VPC ID
VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=tag:Name,Values=${APP_NAME}-vpc" \
    --query 'Vpcs[0].VpcId' \
    --output text)

echo "VPC ID: ${VPC_ID}"
```

#### Step 3.2: Create Subnets (Multi-AZ)
```bash
# Create public subnet 1 (us-east-1a)
aws ec2 create-subnet \
    --vpc-id ${VPC_ID} \
    --cidr-block 10.0.1.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value='${APP_NAME}'-public-1a}]'

# Create public subnet 2 (us-east-1b)
aws ec2 create-subnet \
    --vpc-id ${VPC_ID} \
    --cidr-block 10.0.2.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value='${APP_NAME}'-public-1b}]'

# Create private subnet 1 (us-east-1a)
aws ec2 create-subnet \
    --vpc-id ${VPC_ID} \
    --cidr-block 10.0.11.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value='${APP_NAME}'-private-1a}]'

# Create private subnet 2 (us-east-1b)
aws ec2 create-subnet \
    --vpc-id ${VPC_ID} \
    --cidr-block 10.0.12.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value='${APP_NAME}'-private-1b}]'
```

#### Step 3.3: Configure Internet Gateway & NAT
```bash
# Create Internet Gateway
aws ec2 create-internet-gateway \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value='${APP_NAME}'-igw}]'

IGW_ID=$(aws ec2 describe-internet-gateways \
    --filters "Name=tag:Name,Values=${APP_NAME}-igw" \
    --query 'InternetGateways[0].InternetGatewayId' \
    --output text)

# Attach to VPC
aws ec2 attach-internet-gateway \
    --vpc-id ${VPC_ID} \
    --internet-gateway-id ${IGW_ID}

echo "Internet Gateway configured"
```

---

### Phase 4: ElastiCache Redis Setup (10 minutes)

```bash
# Create ElastiCache subnet group
aws elasticache create-cache-subnet-group \
    --cache-subnet-group-name ${APP_NAME}-redis-subnet \
    --cache-subnet-group-description "Subnet group for ${APP_NAME} Redis" \
    --subnet-ids subnet-xxx subnet-yyy

# Create Redis cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id ${APP_NAME}-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --engine-version 7.0 \
    --num-cache-nodes 1 \
    --cache-subnet-group-name ${APP_NAME}-redis-subnet \
    --preferred-availability-zone us-east-1a \
    --tags Key=Name,Value=${APP_NAME}-redis

echo "ElastiCache Redis cluster creating (takes 5-10 minutes)..."
```

---

### Phase 5: ECS Cluster & Services (30 minutes)

#### Step 5.1: Create ECS Cluster
```bash
aws ecs create-cluster \
    --cluster-name ${APP_NAME}-cluster \
    --capacity-providers FARGATE FARGATE_SPOT \
    --default-capacity-provider-strategy \
        capacityProvider=FARGATE,weight=1 \
        capacityProvider=FARGATE_SPOT,weight=1 \
    --region ${AWS_REGION}

echo "ECS Cluster created"
```

#### Step 5.2: Create Task Execution Role
```bash
# Create trust policy
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
    --role-name ${APP_NAME}-task-execution-role \
    --assume-role-policy-document file://trust-policy.json

# Attach AWS managed policy
aws iam attach-role-policy \
    --role-name ${APP_NAME}-task-execution-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create custom policy for Secrets Manager
cat > secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${APP_NAME}/*"
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name ${APP_NAME}-task-execution-role \
    --policy-name SecretsManagerAccess \
    --policy-document file://secrets-policy.json

echo "Task execution role created"
```

#### Step 5.3: Create Task Definitions

**Backend Task Definition:**
```bash
cat > backend-task-definition.json <<EOF
{
  "family": "${APP_NAME}-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/${APP_NAME}-task-execution-role",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        },
        {
          "name": "CACHE_TTL",
          "value": "120"
        },
        {
          "name": "REFRESH_INTERVAL",
          "value": "300"
        }
      ],
      "secrets": [
        {
          "name": "AIRFLOW_BASE_URL",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${APP_NAME}/airflow-credentials:AIRFLOW_BASE_URL::"
        },
        {
          "name": "AIRFLOW_USERNAME",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${APP_NAME}/airflow-credentials:AIRFLOW_USERNAME::"
        },
        {
          "name": "AIRFLOW_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${APP_NAME}/airflow-credentials:AIRFLOW_PASSWORD::"
        },
        {
          "name": "AZURE_OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${APP_NAME}/azure-openai-credentials:AZURE_OPENAI_API_KEY::"
        },
        {
          "name": "AZURE_OPENAI_ENDPOINT",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${APP_NAME}/azure-openai-credentials:AZURE_OPENAI_ENDPOINT::"
        },
        {
          "name": "AZURE_OPENAI_DEPLOYMENT_NAME",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${APP_NAME}/azure-openai-credentials:AZURE_OPENAI_DEPLOYMENT_NAME::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/${APP_NAME}-backend",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

# Create CloudWatch log group
aws logs create-log-group \
    --log-group-name /ecs/${APP_NAME}-backend \
    --region ${AWS_REGION}

# Register task definition
aws ecs register-task-definition \
    --cli-input-json file://backend-task-definition.json \
    --region ${AWS_REGION}
```

**Frontend Task Definition:**
```bash
cat > frontend-task-definition.json <<EOF
{
  "family": "${APP_NAME}-frontend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/${APP_NAME}-task-execution-role",
  "containerDefinitions": [
    {
      "name": "frontend",
      "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}-frontend:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/${APP_NAME}-frontend",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

# Create CloudWatch log group
aws logs create-log-group \
    --log-group-name /ecs/${APP_NAME}-frontend \
    --region ${AWS_REGION}

# Register task definition
aws ecs register-task-definition \
    --cli-input-json file://frontend-task-definition.json \
    --region ${AWS_REGION}
```

---

### Phase 6: Application Load Balancer (20 minutes)

#### Step 6.1: Create Security Groups
```bash
# ALB Security Group
aws ec2 create-security-group \
    --group-name ${APP_NAME}-alb-sg \
    --description "Security group for ALB" \
    --vpc-id ${VPC_ID}

ALB_SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${APP_NAME}-alb-sg" \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

# Allow HTTP and HTTPS
aws ec2 authorize-security-group-ingress \
    --group-id ${ALB_SG_ID} \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id ${ALB_SG_ID} \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# ECS Tasks Security Group
aws ec2 create-security-group \
    --group-name ${APP_NAME}-ecs-sg \
    --description "Security group for ECS tasks" \
    --vpc-id ${VPC_ID}

ECS_SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${APP_NAME}-ecs-sg" \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

# Allow traffic from ALB
aws ec2 authorize-security-group-ingress \
    --group-id ${ECS_SG_ID} \
    --protocol tcp \
    --port 8000 \
    --source-group ${ALB_SG_ID}

aws ec2 authorize-security-group-ingress \
    --group-id ${ECS_SG_ID} \
    --protocol tcp \
    --port 80 \
    --source-group ${ALB_SG_ID}
```

#### Step 6.2: Create Application Load Balancer
```bash
# Get subnet IDs
SUBNET_1=$(aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=${APP_NAME}-public-1a" \
    --query 'Subnets[0].SubnetId' \
    --output text)

SUBNET_2=$(aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=${APP_NAME}-public-1b" \
    --query 'Subnets[0].SubnetId' \
    --output text)

# Create ALB
aws elbv2 create-load-balancer \
    --name ${APP_NAME}-alb \
    --subnets ${SUBNET_1} ${SUBNET_2} \
    --security-groups ${ALB_SG_ID} \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4

ALB_ARN=$(aws elbv2 describe-load-balancers \
    --names ${APP_NAME}-alb \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

ALB_DNS=$(aws elbv2 describe-load-balancers \
    --names ${APP_NAME}-alb \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

echo "ALB DNS: ${ALB_DNS}"
```

#### Step 6.3: Create Target Groups
```bash
# Backend target group
aws elbv2 create-target-group \
    --name ${APP_NAME}-backend-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id ${VPC_ID} \
    --target-type ip \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3

BACKEND_TG_ARN=$(aws elbv2 describe-target-groups \
    --names ${APP_NAME}-backend-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

# Frontend target group
aws elbv2 create-target-group \
    --name ${APP_NAME}-frontend-tg \
    --protocol HTTP \
    --port 80 \
    --vpc-id ${VPC_ID} \
    --target-type ip \
    --health-check-path / \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3

FRONTEND_TG_ARN=$(aws elbv2 describe-target-groups \
    --names ${APP_NAME}-frontend-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)
```

#### Step 6.4: Create ALB Listeners
```bash
# Create HTTP listener (redirects to HTTPS in production)
aws elbv2 create-listener \
    --load-balancer-arn ${ALB_ARN} \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=${FRONTEND_TG_ARN}

# Create listener rules for path-based routing
LISTENER_ARN=$(aws elbv2 describe-listeners \
    --load-balancer-arn ${ALB_ARN} \
    --query 'Listeners[0].ListenerArn' \
    --output text)

# Route /api/* to backend
aws elbv2 create-rule \
    --listener-arn ${LISTENER_ARN} \
    --priority 1 \
    --conditions Field=path-pattern,Values='/api/*' \
    --actions Type=forward,TargetGroupArn=${BACKEND_TG_ARN}

# Route /health to backend
aws elbv2 create-rule \
    --listener-arn ${LISTENER_ARN} \
    --priority 2 \
    --conditions Field=path-pattern,Values='/health' \
    --actions Type=forward,TargetGroupArn=${BACKEND_TG_ARN}

# Route /docs to backend
aws elbv2 create-rule \
    --listener-arn ${LISTENER_ARN} \
    --priority 3 \
    --conditions Field=path-pattern,Values='/docs*' \
    --actions Type=forward,TargetGroupArn=${BACKEND_TG_ARN}
```

---

### Phase 7: ECS Services Creation (15 minutes)

#### Step 7.1: Create Backend Service
```bash
aws ecs create-service \
    --cluster ${APP_NAME}-cluster \
    --service-name ${APP_NAME}-backend-service \
    --task-definition ${APP_NAME}-backend \
    --desired-count 2 \
    --launch-type FARGATE \
    --platform-version LATEST \
    --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_1},${SUBNET_2}],securityGroups=[${ECS_SG_ID}],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=${BACKEND_TG_ARN},containerName=backend,containerPort=8000" \
    --health-check-grace-period-seconds 60 \
    --region ${AWS_REGION}

echo "Backend service created with 2 tasks"
```

#### Step 7.2: Create Frontend Service
```bash
aws ecs create-service \
    --cluster ${APP_NAME}-cluster \
    --service-name ${APP_NAME}-frontend-service \
    --task-definition ${APP_NAME}-frontend \
    --desired-count 2 \
    --launch-type FARGATE \
    --platform-version LATEST \
    --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_1},${SUBNET_2}],securityGroups=[${ECS_SG_ID}],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=${FRONTEND_TG_ARN},containerName=frontend,containerPort=80" \
    --health-check-grace-period-seconds 60 \
    --region ${AWS_REGION}

echo "Frontend service created with 2 tasks"
```

---

### Phase 8: Auto Scaling Configuration (10 minutes)

```bash
# Register backend scalable target
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/${APP_NAME}-cluster/${APP_NAME}-backend-service \
    --min-capacity 2 \
    --max-capacity 10 \
    --region ${AWS_REGION}

# Create scaling policy for backend (CPU-based)
aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/${APP_NAME}-cluster/${APP_NAME}-backend-service \
    --policy-name ${APP_NAME}-backend-cpu-scaling \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration file://scaling-policy.json \
    --region ${AWS_REGION}

# Create scaling policy JSON
cat > scaling-policy.json <<EOF
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleInCooldown": 300,
  "ScaleOutCooldown": 60
}
EOF

echo "Auto-scaling configured for backend service"
```

---

### Phase 9: SSL/TLS Setup with ACM (15 minutes)

#### Step 9.1: Request SSL Certificate
```bash
# Request certificate
aws acm request-certificate \
    --domain-name dashboard.yourcompany.com \
    --validation-method DNS \
    --region ${AWS_REGION}

CERT_ARN=$(aws acm list-certificates \
    --query 'CertificateSummaryList[?DomainName==`dashboard.yourcompany.com`].CertificateArn' \
    --output text)

echo "Certificate ARN: ${CERT_ARN}"
echo "Validate the certificate via DNS in ACM console"
```

#### Step 9.2: Add HTTPS Listener (After certificate validation)
```bash
# Create HTTPS listener
aws elbv2 create-listener \
    --load-balancer-arn ${ALB_ARN} \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=${CERT_ARN} \
    --default-actions Type=forward,TargetGroupArn=${FRONTEND_TG_ARN}

# Update HTTP listener to redirect to HTTPS
aws elbv2 modify-listener \
    --listener-arn ${LISTENER_ARN} \
    --default-actions Type=redirect,RedirectConfig='{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}'
```

---

### Phase 10: Route 53 DNS Setup (10 minutes)

```bash
# Get hosted zone ID
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones \
    --query 'HostedZones[?Name==`yourcompany.com.`].Id' \
    --output text | cut -d'/' -f3)

# Create DNS record
cat > dns-record.json <<EOF
{
  "Changes": [
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "dashboard.yourcompany.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z35SXDOTRQ7X7K",
          "DNSName": "${ALB_DNS}",
          "EvaluateTargetHealth": true
        }
      }
    }
  ]
}
EOF

aws route53 change-resource-record-sets \
    --hosted-zone-id ${HOSTED_ZONE_ID} \
    --change-batch file://dns-record.json

echo "DNS record created for dashboard.yourcompany.com"
```

---

## ✅ Deployment Verification

### Check Service Health
```bash
# Check ECS services
aws ecs describe-services \
    --cluster ${APP_NAME}-cluster \
    --services ${APP_NAME}-backend-service ${APP_NAME}-frontend-service \
    --query 'services[*].[serviceName,desiredCount,runningCount,status]' \
    --output table

# Check target health
aws elbv2 describe-target-health \
    --target-group-arn ${BACKEND_TG_ARN}

aws elbv2 describe-target-health \
    --target-group-arn ${FRONTEND_TG_ARN}

# Test backend health
curl https://dashboard.yourcompany.com/health

# Test frontend
curl https://dashboard.yourcompany.com/
```

### View Logs
```bash
# Backend logs
aws logs tail /ecs/${APP_NAME}-backend --follow

# Frontend logs
aws logs tail /ecs/${APP_NAME}-frontend --follow
```

---

## 📊 Monitoring & Logging

### CloudWatch Dashboards
```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
    --dashboard-name ${APP_NAME}-dashboard \
    --dashboard-body file://cloudwatch-dashboard.json
```

### Set Up Alarms
```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
    --alarm-name ${APP_NAME}-backend-high-cpu \
    --alarm-description "Backend CPU > 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=ServiceName,Value=${APP_NAME}-backend-service Name=ClusterName,Value=${APP_NAME}-cluster

# Unhealthy target alarm
aws cloudwatch put-metric-alarm \
    --alarm-name ${APP_NAME}-unhealthy-targets \
    --alarm-description "Unhealthy targets detected" \
    --metric-name UnHealthyHostCount \
    --namespace AWS/ApplicationELB \
    --statistic Average \
    --period 60 \
    --evaluation-periods 2 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold
```

---

## 💰 Cost Estimation

### Monthly Cost Breakdown

```
ECS Fargate (Backend: 2 tasks * 0.5 vCPU, 1GB RAM):
  - $0.04048/hour * 2 tasks * 730 hours = ~$59

ECS Fargate (Frontend: 2 tasks * 0.25 vCPU, 0.5GB RAM):
  - $0.02024/hour * 2 tasks * 730 hours = ~$30

Application Load Balancer:
  - $0.0225/hour * 730 hours = ~$16.50
  - LCU charges = ~$5-10

ElastiCache Redis (t3.micro):
  - $0.017/hour * 730 hours = ~$12.50

ECR Storage (10GB):
  - $0.10/GB * 10GB = ~$1

Data Transfer Out (50GB):
  - $0.09/GB * 50GB = ~$4.50

CloudWatch Logs (10GB):
  - $0.50/GB * 10GB = ~$5

Secrets Manager (3 secrets):
  - $0.40/secret * 3 = ~$1.20

Route 53 Hosted Zone:
  - $0.50/month

TOTAL ESTIMATED: ~$135-145/month
```

### Cost Optimization Tips
1. Use Fargate Spot for non-critical workloads (save up to 70%)
2. Enable auto-scaling to scale down during low traffic
3. Use CloudWatch Logs retention policies
4. Enable S3 lifecycle policies for ECR images
5. Consider Reserved Capacity for predictable workloads

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: Tasks not starting
```bash
# Check task definitions
aws ecs describe-task-definition --task-definition ${APP_NAME}-backend

# Check service events
aws ecs describe-services \
    --cluster ${APP_NAME}-cluster \
    --services ${APP_NAME}-backend-service \
    --query 'services[0].events[0:5]'

# Check stopped tasks
aws ecs list-tasks \
    --cluster ${APP_NAME}-cluster \
    --desired-status STOPPED \
    --max-results 5

aws ecs describe-tasks \
    --cluster ${APP_NAME}-cluster \
    --tasks <task-id> \
    --query 'tasks[0].stoppedReason'
```

#### Issue: Unhealthy targets
```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids ${ECS_SG_ID}

# Test health endpoint from ALB subnet
# Ensure ECS tasks are in correct subnets
# Check health check path in target group
```

#### Issue: High costs
```bash
# Check task count
aws ecs describe-services \
    --cluster ${APP_NAME}-cluster \
    --services ${APP_NAME}-backend-service \
    --query 'services[0].desiredCount'

# Review CloudWatch costs
aws ce get-cost-and-usage \
    --time-period Start=2025-10-01,End=2025-10-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=SERVICE
```

---

## 🔄 CI/CD Integration (Optional)

### GitHub Actions Deployment
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS ECS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push backend
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        run: |
          docker build -t $ECR_REGISTRY/airflow-health-dashboard-backend:latest backend/
          docker push $ECR_REGISTRY/airflow-health-dashboard-backend:latest
      
      - name: Build and push frontend
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        run: |
          docker build -t $ECR_REGISTRY/airflow-health-dashboard-frontend:latest frontend/
          docker push $ECR_REGISTRY/airflow-health-dashboard-frontend:latest
      
      - name: Update ECS services
        run: |
          aws ecs update-service \
            --cluster airflow-health-dashboard-cluster \
            --service airflow-health-dashboard-backend-service \
            --force-new-deployment
          
          aws ecs update-service \
            --cluster airflow-health-dashboard-cluster \
            --service airflow-health-dashboard-frontend-service \
            --force-new-deployment
```

---

## 📚 Next Steps

After deployment:
1. ✅ Configure SSL certificate validation
2. ✅ Set up CloudWatch alarms and SNS notifications
3. ✅ Enable AWS WAF for security
4. ✅ Configure backup strategies
5. ✅ Set up Slack integration (see next section)
6. ✅ Configure scheduled reports with EventBridge

---

**Deployment Status**: Complete  
**Access URL**: https://dashboard.yourcompany.com  
**Estimated Setup Time**: 2-3 hours  
**Monthly Cost**: ~$135-145

For Slack integration and scheduled reports, see the next section!
