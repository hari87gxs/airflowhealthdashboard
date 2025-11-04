# MWAA Authentication Implementation Summary

## Overview
Added support for AWS Managed Workflows for Apache Airflow (MWAA) authentication to the Airflow Health Dashboard. The system now supports three authentication methods: API tokens, basic auth (username/password), and MWAA web token authentication.

## Files Modified

### 1. `/backend/app/config.py`
**Changes:**
- Added `aws_region` field for AWS region configuration
- Added `mwaa_environment_name` field for MWAA environment name
- Updated `validate_auth` validator to accept MWAA configuration as a valid authentication method

**New Configuration Options:**
```python
aws_region: Optional[str] = Field(None, description="AWS region for MWAA")
mwaa_environment_name: Optional[str] = Field(None, description="MWAA environment name")
```

### 2. `/backend/app/airflow_client.py`
**Changes:**
- Added imports: `boto3`, `requests`, `Tuple` type
- Added MWAA session management fields to `AirflowAPIClient` class
- Implemented `_get_mwaa_session_info()` method to obtain MWAA web tokens
- Implemented `_init_mwaa_session()` method to initialize MWAA authentication
- Implemented `_refresh_mwaa_session_if_needed()` method for session refresh
- Updated `__init__()` to support three authentication methods with priority handling
- Updated `_make_request()` to use MWAA session cookies when applicable
- Updated `get_all_dag_runs_for_dags()` to handle MWAA authentication for concurrent requests
- Added automatic session refresh on 401 responses

**Key Features:**
- Automatic MWAA token acquisition and session cookie management
- Session auto-refresh on expiration
- Support for concurrent API requests with MWAA authentication
- Fallback authentication priority: API Token → Basic Auth → MWAA

### 3. `/backend/requirements.txt`
**Changes:**
- Added `boto3==1.35.0` for AWS SDK integration
- Uses existing `httpx==0.25.2` for MWAA login requests (synchronous httpx.Client)

### 4. `/.env`
**Changes:**
- Added documentation comments for MWAA configuration
- Added example configuration for AWS_REGION and MWAA_ENVIRONMENT_NAME

## New Files Created

### 1. `/MWAA_AUTHENTICATION.md`
Comprehensive documentation covering:
- MWAA authentication flow and architecture
- Configuration guide with examples
- AWS IAM permissions required
- Local and production deployment scenarios
- Troubleshooting guide
- Security best practices

## Authentication Flow

### MWAA Authentication Process:
1. System checks configuration on startup
2. If AWS_REGION and MWAA_ENVIRONMENT_NAME are set (and no username/password):
   - Initializes boto3 MWAA client
   - Calls `create_web_login_token()` API
   - Receives web server hostname and token
   - Makes POST request to MWAA login endpoint
   - Stores session cookie for subsequent requests
3. All API requests use the session cookie
4. On 401 response, automatically refreshes session and retries

## Configuration Examples

### MWAA Configuration:
```bash
AIRFLOW_BASE_URL=https://abc123.c9.us-east-1.airflow.amazonaws.com
AWS_REGION=us-east-1
MWAA_ENVIRONMENT_NAME=my-airflow-env
# Leave username/password empty
```

### Basic Auth Configuration (existing):
```bash
AIRFLOW_BASE_URL=https://airflow.example.com
AIRFLOW_USERNAME=admin
AIRFLOW_PASSWORD=secret
```

### API Token Configuration (existing):
```bash
AIRFLOW_BASE_URL=https://airflow.example.com
AIRFLOW_API_TOKEN=your_token_here
```

## AWS IAM Requirements

Required IAM permissions for MWAA authentication:
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
      "Resource": "arn:aws:airflow:*:*:environment/*"
    }
  ]
}
```

## Testing

To test the implementation:

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Configure MWAA in .env file
echo "AWS_REGION=us-east-1" >> .env
echo "MWAA_ENVIRONMENT_NAME=your-env" >> .env
# Remove or comment out AIRFLOW_USERNAME and AIRFLOW_PASSWORD

# 3. Set AWS credentials (if not using IAM role)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# 4. Start the backend
python -m uvicorn app.main:app --reload

# 5. Check logs for successful authentication
# Expected: "Successfully authenticated with MWAA environment: your-env"
```

## Error Handling

The implementation includes robust error handling:
- Validates configuration on startup
- Raises clear errors if authentication is misconfigured
- Logs detailed error messages for MWAA connection issues
- Automatically retries on session expiration
- Gracefully handles network errors and timeouts

## Security Considerations

1. **No Credentials in Code**: All configuration via environment variables
2. **IAM Role Support**: Works with EC2/ECS IAM roles (no keys needed)
3. **Session Security**: Session cookies are internal-only, not logged
4. **Least Privilege**: Only requires minimal MWAA permissions
5. **Automatic Rotation**: Sessions automatically refresh when expired

## Backward Compatibility

✅ Fully backward compatible with existing deployments:
- Existing username/password configurations continue to work
- Existing API token configurations continue to work
- MWAA authentication is opt-in via new environment variables
- No breaking changes to API or behavior

## Next Steps

To use MWAA authentication in production:

1. Update `.env` file with MWAA configuration
2. Ensure AWS credentials are available (IAM role or credentials file)
3. Verify IAM permissions for MWAA access
4. Deploy updated code
5. Monitor logs for successful MWAA authentication
6. Test dashboard functionality with MWAA backend

## References

- AWS MWAA Documentation: https://docs.aws.amazon.com/mwaa/
- boto3 MWAA Client: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mwaa.html
- Airflow REST API: https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html
