# Quick Start: Configuring MWAA Authentication

This guide will help you quickly configure the Airflow Health Dashboard to work with AWS MWAA.

## Prerequisites

1. An AWS MWAA environment up and running
2. AWS credentials with appropriate IAM permissions
3. The MWAA environment name and AWS region

## Step 1: Configure Environment Variables

Edit your `.env` file and add the following:

```bash
# Airflow Configuration
AIRFLOW_BASE_URL=https://your-mwaa-id.c9.us-east-1.airflow.amazonaws.com

# AWS MWAA Configuration
AWS_REGION=us-east-1
MWAA_ENVIRONMENT_NAME=your-mwaa-environment-name

# IMPORTANT: Comment out or remove username/password
# AIRFLOW_USERNAME=
# AIRFLOW_PASSWORD=
# AIRFLOW_API_TOKEN=
```

**How to find your MWAA URL:**
```bash
aws mwaa get-environment --name your-mwaa-environment-name --region us-east-1 \
  --query "Environment.WebserverUrl" --output text
```

## Step 2: Set Up AWS Credentials

Choose one of these methods:

### Option A: Use AWS CLI Profile (Recommended for local development)
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and Region
```

### Option B: Use Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### Option C: Use IAM Role (Recommended for production)
When running on AWS (EC2, ECS, Lambda), attach an IAM role with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "airflow:CreateWebLoginToken",
        "airflow:GetEnvironment"
      ],
      "Resource": "arn:aws:airflow:us-east-1:123456789012:environment/your-mwaa-environment-name"
    }
  ]
}
```

## Step 3: Install Dependencies

```bash
cd backend
pip install boto3==1.35.0
# Or install all dependencies (includes httpx which is already in requirements)
pip install -r requirements.txt
```

## Step 4: Test the Configuration

Start the backend:
```bash
cd backend
python -m uvicorn app.main:app --reload
```

Check the logs - you should see:
```
INFO: Successfully authenticated with MWAA environment: your-mwaa-environment-name
```

Test the health endpoint:
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "airflow_connection": true,
  "timestamp": "2025-11-04T12:00:00Z"
}
```

## Step 5: Start the Full Application

```bash
# From project root
docker-compose up -d
```

Access the dashboard at: `http://localhost:3000`

## Troubleshooting

### Error: "Failed to get MWAA session info"

**Check AWS credentials:**
```bash
aws sts get-caller-identity
```

**List your MWAA environments:**
```bash
aws mwaa list-environments --region us-east-1
```

**Get environment details:**
```bash
aws mwaa get-environment --name your-env-name --region us-east-1
```

### Error: "Access Denied"

Verify IAM permissions:
```bash
aws mwaa create-web-login-token --name your-env-name --region us-east-1
```

If this fails, you need the `airflow:CreateWebLoginToken` permission.

### Error: "Authentication configuration missing"

Make sure your `.env` file has either:
- `AWS_REGION` AND `MWAA_ENVIRONMENT_NAME`, OR
- `AIRFLOW_USERNAME` AND `AIRFLOW_PASSWORD`, OR
- `AIRFLOW_API_TOKEN`

### Session Keeps Expiring

This is normal - the system automatically refreshes MWAA sessions. Check logs for:
```
WARNING: MWAA session expired, attempting to refresh...
INFO: Successfully authenticated with MWAA environment: your-env-name
```

## Complete Example `.env` File

```bash
# Airflow Configuration
AIRFLOW_BASE_URL=https://abc123def-xyz.c9.us-east-1.airflow.amazonaws.com

# AWS MWAA Configuration
AWS_REGION=us-east-1
MWAA_ENVIRONMENT_NAME=my-production-airflow

# Cache Configuration
CACHE_TTL_SECONDS=3600
REFRESH_INTERVAL_SECONDS=3600

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "https://dashboard.yourcompany.com"]

# Logging
LOG_LEVEL=INFO

# LLM Configuration (optional)
LLM_ENABLED=true
LLM_PROVIDER=azure_openai
LLM_API_KEY=your-key-here
LLM_MODEL=gpt-4o

# Azure OpenAI Configuration (if using Azure)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

## Next Steps

- ✅ Configure Slack notifications (see `SLACK_INTEGRATION.md`)
- ✅ Set up scheduled reports (see `QUICKSTART_AWS_SLACK.md`)
- ✅ Deploy to production (see `AWS_DEPLOYMENT.md`)
- ✅ Configure monitoring and alerts

## Support

For detailed documentation, see:
- `MWAA_AUTHENTICATION.md` - Complete MWAA auth documentation
- `MWAA_IMPLEMENTATION_SUMMARY.md` - Technical implementation details
- `README.md` - General project documentation

For issues related to AWS MWAA itself, consult:
- [AWS MWAA Documentation](https://docs.aws.amazon.com/mwaa/)
- [Airflow REST API Documentation](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html)
