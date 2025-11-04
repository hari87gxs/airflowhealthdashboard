# AWS MWAA Authentication Guide

This document explains how to configure the Airflow Health Dashboard to work with AWS Managed Workflows for Apache Airflow (MWAA).

## Overview

The dashboard supports three authentication methods for connecting to Airflow:

1. **API Token** - Best for self-hosted Airflow with API tokens enabled
2. **Basic Authentication** - Username and password for self-hosted Airflow
3. **AWS MWAA** - Automatic token-based authentication for AWS MWAA environments

## MWAA Authentication Flow

When using AWS MWAA, the system:

1. Connects to AWS MWAA using boto3
2. Requests a web login token from the MWAA API
3. Exchanges the token for a session cookie
4. Uses the session cookie for subsequent API calls
5. Automatically refreshes the session if it expires (401 response)

## Configuration

### Prerequisites

1. AWS credentials configured on the host machine (via AWS CLI, environment variables, or IAM role)
2. IAM permissions to access the MWAA environment:
   - `airflow:CreateWebLoginToken`
   - `airflow:GetEnvironment`

### Environment Variables

To use MWAA authentication, set these environment variables in your `.env` file:

```bash
# Airflow Configuration
AIRFLOW_BASE_URL=https://your-mwaa-environment-id.region.airflow.amazonaws.com

# AWS MWAA Configuration
AWS_REGION=us-east-1
MWAA_ENVIRONMENT_NAME=your-mwaa-environment-name

# Important: Leave username and password empty for MWAA
# AIRFLOW_USERNAME=
# AIRFLOW_PASSWORD=
# AIRFLOW_API_TOKEN=
```

### Authentication Priority

The system will use authentication in this order:

1. If `AIRFLOW_API_TOKEN` is set → Use API token
2. Else if `AIRFLOW_USERNAME` and `AIRFLOW_PASSWORD` are set → Use basic auth
3. Else if `AWS_REGION` and `MWAA_ENVIRONMENT_NAME` are set → Use MWAA auth
4. Else → Raise configuration error

### AWS Credentials Setup

The boto3 client will automatically use AWS credentials from:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS credentials file (`~/.aws/credentials`)
3. IAM role (when running on EC2, ECS, or other AWS services)

## Example Configuration

### For Local Development

```bash
# .env file
AIRFLOW_BASE_URL=https://abc123def-xyz.c9.us-east-1.airflow.amazonaws.com
AWS_REGION=us-east-1
MWAA_ENVIRONMENT_NAME=my-airflow-env

# Set AWS credentials (one of these methods):
# Method 1: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

# Method 2: AWS CLI profile
export AWS_PROFILE=your-profile-name
```

### For Production (ECS/EC2)

When running on AWS infrastructure, use IAM roles:

```bash
# .env file
AIRFLOW_BASE_URL=https://abc123def-xyz.c9.us-east-1.airflow.amazonaws.com
AWS_REGION=us-east-1
MWAA_ENVIRONMENT_NAME=my-airflow-env

# No AWS credentials needed - the IAM role will provide them
```

Attach an IAM role with this policy to your ECS task or EC2 instance:

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
      "Resource": "arn:aws:airflow:us-east-1:123456789012:environment/my-airflow-env"
    }
  ]
}
```

## Testing MWAA Connection

After configuration, you can test the connection:

```bash
# Start the backend
cd backend
python -m uvicorn app.main:app --reload

# Check logs for successful authentication:
# "Successfully authenticated with MWAA environment: my-airflow-env"

# Test the health endpoint
curl http://localhost:8000/api/v1/health
```

## Troubleshooting

### Error: "Failed to get MWAA session info"

**Possible causes:**
- Incorrect AWS credentials
- Missing IAM permissions
- Incorrect MWAA environment name or region
- MWAA environment is not running

**Solution:**
1. Verify AWS credentials: `aws sts get-caller-identity`
2. Check IAM permissions
3. Verify environment name: `aws mwaa list-environments --region us-east-1`

### Error: "MWAA session expired"

The system automatically refreshes expired sessions. If you see this repeatedly:
- Check network connectivity to MWAA
- Verify MWAA environment is healthy
- Check CloudWatch logs for MWAA issues

### Error: "Authentication configuration missing"

Ensure at least one authentication method is configured:
- API token, OR
- Username + password, OR
- AWS region + MWAA environment name

## Dependencies

The MWAA authentication requires these Python packages (already included in requirements.txt):

```
boto3==1.35.0
httpx==0.25.2
```

Note: We use `httpx` for all HTTP requests (both async and sync), ensuring consistency across the application.

## Architecture Notes

- MWAA sessions are obtained during client initialization
- Sessions are automatically refreshed on 401 responses
- All concurrent DAG run requests use the same session cookie
- The base URL is overridden to use the MWAA hostname when using MWAA auth

## Security Considerations

1. **IAM Roles**: Use IAM roles instead of access keys when possible
2. **Least Privilege**: Only grant necessary MWAA permissions
3. **Environment Variables**: Never commit AWS credentials to version control
4. **Session Cookies**: Handled internally and not exposed in logs
