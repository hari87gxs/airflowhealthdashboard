# 🚀 Quick Start Guide - AWS Deployment with Slack

Get your Airflow Health Dashboard deployed to AWS with Slack notifications in minutes!

## Prerequisites (5 minutes)

Install required tools:

```bash
# Check if installed
aws --version        # AWS CLI
docker --version     # Docker
terraform --version  # Terraform >= 1.0

# Configure AWS credentials
aws configure
```

## Step 1: Configure Slack (5 minutes)

1. **Create Incoming Webhook**
   - Go to: https://api.slack.com/messaging/webhooks
   - Click "Create New App" → "From scratch"
   - Name: "Airflow Health Dashboard"
   - Select your workspace
   - Add "Incoming Webhooks" feature
   - Activate and create webhook
   - **Copy the Webhook URL** (starts with `https://hooks.slack.com/services/...`)

2. **Choose a Slack channel**
   - Recommended: Create `#airflow-health` channel
   - Or use existing channel like `#data-engineering`

## Step 2: Configure Terraform (10 minutes)

```bash
cd airflow-health-dashboard/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
# AWS Configuration
aws_region = "us-east-1"
environment = "prod"

# Airflow
airflow_url = "https://your-airflow-instance.com"
airflow_username = "admin"
airflow_password = "your-secure-password"

# Azure OpenAI
azure_openai_endpoint = "https://your-instance.openai.azure.com/"
azure_openai_key = "your-api-key-here"
azure_openai_deployment = "gpt-4"

# Slack (IMPORTANT!)
slack_webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
dashboard_url = ""  # Leave empty for now, will be set after deployment

# Report Schedule (UTC - adjust for your timezone)
morning_report_hour = 10    # 10 AM UTC
evening_report_hour = 19    # 7 PM UTC
```

**Timezone Conversion:**
- PST (UTC-8): Add 8 hours (10 AM PST = 18:00 UTC)
- EST (UTC-5): Add 5 hours (10 AM EST = 15:00 UTC)
- CET (UTC+1): Subtract 1 hour (10 AM CET = 09:00 UTC)

## Step 3: Deploy to AWS (15 minutes)

**Option A: Automated Script (Recommended)**

```bash
cd airflow-health-dashboard
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

The script will:
1. ✅ Check prerequisites
2. ✅ Initialize Terraform
3. ✅ Create AWS infrastructure
4. ✅ Build Docker images
5. ✅ Push to ECR
6. ✅ Deploy services
7. ✅ Display dashboard URL

**Option B: Manual Steps**

```bash
# 1. Initialize Terraform
cd terraform
terraform init

# 2. Plan infrastructure
terraform plan -out=tfplan

# 3. Apply (type 'yes' when prompted)
terraform apply tfplan

# 4. Get ECR URLs
export BACKEND_ECR=$(terraform output -raw ecr_backend_repository_url)
export FRONTEND_ECR=$(terraform output -raw ecr_frontend_repository_url)
export SCHEDULER_ECR=$(terraform output -raw ecr_scheduler_repository_url)

# 5. Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${BACKEND_ECR%%/*}

# 6. Build and push images
cd ..
docker build -t $BACKEND_ECR:latest -f backend/Dockerfile backend/
docker push $BACKEND_ECR:latest

docker build -t $FRONTEND_ECR:latest -f frontend/Dockerfile frontend/
docker push $FRONTEND_ECR:latest

docker build -t $SCHEDULER_ECR:latest -f scheduler/Dockerfile scheduler/
docker push $SCHEDULER_ECR:latest

# 7. Update ECS services
CLUSTER=$(cd terraform && terraform output -raw ecs_cluster_name)
aws ecs update-service --cluster $CLUSTER \
  --service $(cd terraform && terraform output -raw backend_service_name) \
  --force-new-deployment

aws ecs update-service --cluster $CLUSTER \
  --service $(cd terraform && terraform output -raw frontend_service_name) \
  --force-new-deployment

# 8. Get dashboard URL
cd terraform
terraform output dashboard_url
```

## Step 4: Verify Deployment (5 minutes)

```bash
# Get your dashboard URL
cd terraform
export DASHBOARD_URL=$(terraform output -raw dashboard_url)
echo $DASHBOARD_URL

# Test backend health
curl $DASHBOARD_URL/health
# Expected: {"status":"healthy"}

# Test API
curl $DASHBOARD_URL/api/v1/domains | jq '.'
# Expected: JSON with domain data

# Test Slack
curl -X POST $DASHBOARD_URL/api/slack/test
# Expected: {"success": true, "message": "Test message sent to Slack"}
# Check your Slack channel for test message!

# Send manual report
curl -X POST $DASHBOARD_URL/api/reports/send
# Check Slack for full health report!
```

## Step 5: Update Dashboard URL (2 minutes)

Now that you have the ALB URL, update Terraform to use it in Slack messages:

```bash
# Edit terraform/terraform.tfvars
dashboard_url = "http://your-alb-dns-name.us-east-1.elb.amazonaws.com"

# Apply changes
cd terraform
terraform apply
```

Or set up custom domain (optional):

```bash
# Request ACM certificate
aws acm request-certificate \
  --domain-name dashboard.example.com \
  --validation-method DNS

# Update terraform.tfvars
domain_name = "dashboard.example.com"
certificate_arn = "arn:aws:acm:us-east-1:123456789:certificate/..."
dashboard_url = "https://dashboard.example.com"

# Apply
terraform apply

# Create Route 53 record pointing to ALB
```

## Step 6: Configure Scheduled Reports (Optional)

Your reports are already scheduled! They run at:
- **Morning**: Time specified in `morning_report_hour` (default 10:00 UTC)
- **Evening**: Time specified in `evening_report_hour` (default 19:00 UTC)

To change times:

```bash
# Edit terraform/terraform.tfvars
morning_report_hour = 14    # 2 PM UTC
evening_report_hour = 22    # 10 PM UTC

# Apply changes
cd terraform
terraform apply
```

## Troubleshooting

### "Slack message not appearing"

```bash
# Check Slack is enabled
curl $DASHBOARD_URL/api/reports/schedule | jq '.slack_enabled'

# Check webhook URL is set
cd terraform
terraform output | grep slack

# Test webhook directly
curl -X POST YOUR_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test from terminal"}'
```

### "Service won't start"

```bash
# Check logs
aws logs tail /ecs/airflow-health-dashboard --follow

# Check service status
CLUSTER=$(cd terraform && terraform output -raw ecs_cluster_name)
aws ecs describe-services --cluster $CLUSTER --services backend frontend

# Check task status
aws ecs list-tasks --cluster $CLUSTER --service-name backend
```

### "Frontend shows error"

```bash
# Check backend is healthy
curl $DASHBOARD_URL/health

# Check backend logs
aws logs tail /ecs/airflow-health-dashboard --follow --filter-pattern "backend"

# Check target health
TG_ARN=$(aws elbv2 describe-target-groups --query 'TargetGroups[?contains(TargetGroupName, `backend`)].TargetGroupArn' --output text)
aws elbv2 describe-target-health --target-group-arn $TG_ARN
```

## Cost Management

**Expected monthly cost: $135-145**

Breakdown:
- ECS Fargate: $29/month
- NAT Gateways: $65/month (biggest cost)
- ALB: $25/month
- Redis: $12/month
- Other: $4/month

**To reduce costs:**

1. **Use single NAT Gateway** (reduces reliability):
   ```hcl
   # In terraform/vpc.tf, change count from 2 to 1
   resource "aws_nat_gateway" "main" {
     count = 1  # Instead of length(var.availability_zones)
   ```
   Saves ~$32/month

2. **Use smaller Redis instance**:
   ```hcl
   redis_node_type = "cache.t4g.micro"  # ARM-based, cheaper
   ```
   Saves ~$4/month

3. **Disable scheduler** if not using Slack:
   ```hcl
   slack_webhook_url = ""  # Empty disables scheduler service
   ```
   Saves ~$7/month

## Monitoring

### CloudWatch Dashboard

```bash
# Create dashboard (in AWS Console)
# Widgets to add:
# 1. ECS CPU Utilization
# 2. ECS Memory Utilization
# 3. ALB Request Count
# 4. ALB Target Response Time
# 5. Redis CPU
```

### Set up Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name backend-high-cpu \
  --alarm-description "Backend CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

## Next Steps

1. **✅ Deployed**: Your dashboard is live!
2. **✅ Slack**: Reports scheduled for 10 AM & 7 PM UTC
3. **📊 Monitor**: Watch first reports arrive
4. **🔒 Secure**: Set up custom domain with HTTPS
5. **📈 Optimize**: Adjust resources based on usage
6. **📚 Document**: Share with your team

## Quick Reference

**Dashboard URL**: `http://<alb-dns-name>`  
**API Docs**: `http://<alb-dns-name>/docs`  
**Health Check**: `http://<alb-dns-name>/health`  
**Manual Report**: `curl -X POST http://<alb-dns-name>/api/reports/send`  
**Slack Test**: `curl -X POST http://<alb-dns-name>/api/slack/test`

## Support

- **Detailed Guide**: [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)
- **Slack Setup**: [SLACK_INTEGRATION.md](SLACK_INTEGRATION.md)
- **Checklist**: [AWS_DEPLOYMENT_CHECKLIST.md](AWS_DEPLOYMENT_CHECKLIST.md)
- **Full Summary**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

**Need help?** Check the troubleshooting sections in the documentation or open a GitHub issue.

**Enjoying the dashboard?** ⭐ Star the repo and share with others!
