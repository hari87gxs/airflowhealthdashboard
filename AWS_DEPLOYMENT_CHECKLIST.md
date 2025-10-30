# AWS Deployment Checklist

Use this checklist to ensure a successful AWS deployment of the Airflow Health Dashboard.

## Pre-Deployment

### Prerequisites
- [ ] AWS CLI installed and configured (`aws --version`)
- [ ] Docker installed and running (`docker --version`)
- [ ] Terraform >= 1.0 installed (`terraform --version`)
- [ ] AWS credentials configured (`aws sts get-caller-identity`)
- [ ] Sufficient IAM permissions for VPC, ECS, ECR, ALB, ElastiCache, Secrets Manager
- [ ] Airflow instance accessible and credentials ready
- [ ] Azure OpenAI API key obtained
- [ ] Slack webhook URL created (optional, for notifications)

### Configuration Files
- [ ] Created `terraform/terraform.tfvars` from example
- [ ] Set all required Terraform variables:
  - [ ] `airflow_url`
  - [ ] `airflow_username` & `airflow_password`
  - [ ] `azure_openai_endpoint`, `azure_openai_key`, `azure_openai_deployment`
  - [ ] `slack_webhook_url` (optional)
  - [ ] `morning_report_hour` & `evening_report_hour` (if using Slack)
  - [ ] `aws_region` and `availability_zones`

### Cost Review
- [ ] Reviewed estimated monthly costs (~$135-145/month)
- [ ] Confirmed budget approval
- [ ] Understood cost breakdown:
  - ECS Fargate: ~$29/month (3 services)
  - NAT Gateways: ~$65/month (2 AZs)
  - Application Load Balancer: ~$25/month
  - ElastiCache Redis: ~$12/month
  - Other: ~$4/month

## Infrastructure Deployment

### Step 1: Initialize Terraform
- [ ] Navigate to `terraform/` directory
- [ ] Run `terraform init`
- [ ] Verify initialization successful
- [ ] (Optional) Configure S3 backend for state storage

### Step 2: Plan Infrastructure
- [ ] Run `terraform plan`
- [ ] Review all resources to be created:
  - [ ] VPC with public/private subnets
  - [ ] NAT Gateways and Internet Gateway
  - [ ] Security Groups
  - [ ] ECR Repositories (3)
  - [ ] ECS Cluster
  - [ ] Task Definitions (3)
  - [ ] ECS Services (2-3, depending on Slack config)
  - [ ] Application Load Balancer
  - [ ] Target Groups (2)
  - [ ] ElastiCache Redis Cluster
  - [ ] Secrets Manager Secrets (2-3)
  - [ ] Auto Scaling Policies
- [ ] Confirm no errors in plan output
- [ ] Save plan: `terraform plan -out=tfplan`

### Step 3: Apply Infrastructure
- [ ] Run `terraform apply tfplan`
- [ ] Confirm with `yes`
- [ ] Wait for completion (typically 10-15 minutes)
- [ ] Verify all resources created successfully
- [ ] Note any errors and troubleshoot

### Step 4: Capture Outputs
- [ ] Get ALB DNS name: `terraform output alb_dns_name`
- [ ] Get ECR URLs: `terraform output ecr_*_repository_url`
- [ ] Get Redis endpoint: `terraform output redis_endpoint`
- [ ] Save outputs for reference

## Application Deployment

### Step 5: Authenticate to ECR
- [ ] Run ECR login command:
  ```bash
  aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
  ```
- [ ] Verify login successful

### Step 6: Build Docker Images
- [ ] Build backend image:
  ```bash
  docker build -t <backend-ecr-url>:latest -f backend/Dockerfile backend/
  ```
- [ ] Build frontend image:
  ```bash
  docker build -t <frontend-ecr-url>:latest -f frontend/Dockerfile frontend/
  ```
- [ ] Build scheduler image (if Slack enabled):
  ```bash
  docker build -t <scheduler-ecr-url>:latest -f scheduler/Dockerfile scheduler/
  ```
- [ ] Verify all builds successful

### Step 7: Push Images to ECR
- [ ] Push backend: `docker push <backend-ecr-url>:latest`
- [ ] Push frontend: `docker push <frontend-ecr-url>:latest`
- [ ] Push scheduler: `docker push <scheduler-ecr-url>:latest` (if applicable)
- [ ] Verify images in ECR console

### Step 8: Deploy ECS Services
- [ ] Update backend service:
  ```bash
  aws ecs update-service --cluster <cluster-name> \
    --service <backend-service> --force-new-deployment
  ```
- [ ] Update frontend service:
  ```bash
  aws ecs update-service --cluster <cluster-name> \
    --service <frontend-service> --force-new-deployment
  ```
- [ ] Update scheduler service (if applicable):
  ```bash
  aws ecs update-service --cluster <cluster-name> \
    --service <scheduler-service> --force-new-deployment
  ```

### Step 9: Wait for Deployment
- [ ] Monitor backend service:
  ```bash
  aws ecs wait services-stable --cluster <cluster-name> --services <backend-service>
  ```
- [ ] Monitor frontend service:
  ```bash
  aws ecs wait services-stable --cluster <cluster-name> --services <frontend-service>
  ```
- [ ] Check CloudWatch logs for any errors
- [ ] Verify tasks are running (not crashing)

## Verification & Testing

### Step 10: Test Backend Health
- [ ] Get ALB DNS name
- [ ] Test health endpoint:
  ```bash
  curl http://<alb-dns>/health
  ```
- [ ] Verify response: `{"status": "healthy"}`

### Step 11: Test API Endpoints
- [ ] Test domains endpoint:
  ```bash
  curl http://<alb-dns>/api/v1/domains
  ```
- [ ] Test failure analysis:
  ```bash
  curl http://<alb-dns>/api/v1/analysis/failures
  ```
- [ ] Verify JSON responses with data
- [ ] Check for any error messages

### Step 12: Test Frontend
- [ ] Open browser to `http://<alb-dns>`
- [ ] Verify dashboard loads
- [ ] Check domain health cards display
- [ ] Click on a domain to view details
- [ ] Verify failure analysis tab works
- [ ] Check console for JavaScript errors

### Step 13: Test Slack Integration (if enabled)
- [ ] Test webhook:
  ```bash
  curl -X POST http://<alb-dns>/api/slack/test
  ```
- [ ] Verify test message appears in Slack channel
- [ ] Check message formatting (emojis, blocks)
- [ ] Trigger manual report:
  ```bash
  curl -X POST http://<alb-dns>/api/reports/send
  ```
- [ ] Verify full health report in Slack
- [ ] Check report schedule:
  ```bash
  curl http://<alb-dns>/api/reports/schedule
  ```

### Step 14: Monitor Logs
- [ ] Check backend logs:
  ```bash
  aws logs tail /ecs/airflow-health-dashboard --follow --filter-pattern "backend"
  ```
- [ ] Check scheduler logs (if applicable):
  ```bash
  aws logs tail /ecs/airflow-health-dashboard --follow --filter-pattern "scheduler"
  ```
- [ ] Verify no critical errors
- [ ] Check for connection issues

### Step 15: Test Auto Scaling (optional)
- [ ] Generate load on backend
- [ ] Monitor CloudWatch metrics
- [ ] Verify auto scaling triggers
- [ ] Check scaling activity:
  ```bash
  aws application-autoscaling describe-scaling-activities \
    --service-namespace ecs \
    --resource-id service/<cluster>/<service>
  ```

## Post-Deployment Configuration

### Step 16: Configure Custom Domain (optional)
- [ ] Request ACM certificate for domain
- [ ] Validate certificate (DNS or email)
- [ ] Update `terraform.tfvars` with:
  - `domain_name = "dashboard.example.com"`
  - `certificate_arn = "arn:aws:acm:..."`
- [ ] Apply Terraform changes
- [ ] Create Route 53 A record pointing to ALB
- [ ] Test HTTPS access: `https://dashboard.example.com`
- [ ] Verify HTTP redirects to HTTPS

### Step 17: Set Up Monitoring
- [ ] Enable CloudWatch Container Insights (already enabled)
- [ ] Create CloudWatch dashboard for key metrics:
  - ECS CPU & Memory utilization
  - ALB request count & latency
  - Target health status
  - Redis connection count
- [ ] Set up CloudWatch alarms:
  - ECS task failures
  - ALB 5xx errors
  - High CPU/Memory usage
  - Redis connection failures
- [ ] Configure SNS topic for alarm notifications

### Step 18: Configure Backup & DR
- [ ] Enable S3 backend for Terraform state (if not done)
- [ ] Document recovery procedures
- [ ] Test disaster recovery process
- [ ] Set up cross-region replication (optional)

### Step 19: Security Hardening
- [ ] Review security group rules
- [ ] Enable VPC Flow Logs
- [ ] Enable ALB access logs
- [ ] Enable AWS Config for compliance
- [ ] Review IAM roles and permissions
- [ ] Enable AWS GuardDuty (optional)
- [ ] Rotate Secrets Manager secrets regularly

### Step 20: Documentation
- [ ] Document ALB DNS name or custom domain
- [ ] Update team wiki with access instructions
- [ ] Share Slack channel integration details
- [ ] Document scheduled report times
- [ ] Create runbook for common issues
- [ ] Update on-call procedures

## Ongoing Maintenance

### Daily
- [ ] Monitor Slack reports (10 AM & 7 PM UTC)
- [ ] Check CloudWatch alarms
- [ ] Review critical errors in logs

### Weekly
- [ ] Review ECS task restarts
- [ ] Check auto scaling activity
- [ ] Review cost and usage reports
- [ ] Verify backup processes

### Monthly
- [ ] Update Docker images with security patches
- [ ] Review and optimize resource allocation
- [ ] Check for Terraform provider updates
- [ ] Audit IAM permissions
- [ ] Review CloudWatch logs retention
- [ ] Test disaster recovery procedures

### Quarterly
- [ ] Review architecture for improvements
- [ ] Evaluate cost optimization opportunities
- [ ] Update dependencies (Python, Node.js)
- [ ] Conduct security audit
- [ ] Review and update documentation

## Rollback Procedures

### If Terraform Apply Fails
- [ ] Review error messages
- [ ] Run `terraform destroy` if partial resources created
- [ ] Fix configuration issues
- [ ] Retry `terraform plan` and `terraform apply`

### If Deployment Fails
- [ ] Check ECS task logs
- [ ] Verify Secrets Manager values
- [ ] Roll back to previous Docker images:
  ```bash
  docker pull <ecr-url>:previous-tag
  docker tag <ecr-url>:previous-tag <ecr-url>:latest
  docker push <ecr-url>:latest
  aws ecs update-service --cluster <cluster> --service <service> --force-new-deployment
  ```

### If Service Unhealthy
- [ ] Check target group health
- [ ] Review CloudWatch logs
- [ ] Verify backend can reach Airflow API
- [ ] Check Redis connectivity
- [ ] Restart ECS service if needed

## Cleanup (for testing/dev environments)

### Remove All Resources
- [ ] Run `terraform destroy`
- [ ] Manually delete ECR images (if needed)
- [ ] Verify all resources deleted in AWS Console
- [ ] Check for lingering costs

## Support Resources

- **AWS Support**: https://console.aws.amazon.com/support
- **Terraform Docs**: https://registry.terraform.io/providers/hashicorp/aws
- **Project Documentation**: [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)
- **Slack Integration**: [SLACK_INTEGRATION.md](SLACK_INTEGRATION.md)
- **GitHub Issues**: https://github.com/hari87gxs/airflowhealthdashboard/issues

## Emergency Contacts

- AWS Account Owner: _____________________
- DevOps Lead: _____________________
- On-Call Engineer: _____________________
- Slack Channel: #airflow-health-dashboard

---

**Deployment Date**: _____________  
**Deployed By**: _____________  
**ALB URL**: _____________  
**Custom Domain**: _____________  
**Environment**: [ ] Dev [ ] Staging [ ] Production
