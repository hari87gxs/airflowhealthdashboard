# Azure OpenAI Setup Guide

This guide will help you configure Azure OpenAI for the AI-powered failure analysis feature.

## Prerequisites

- An Azure subscription
- Access to Azure OpenAI Service (requires approval)

## Step 1: Create Azure OpenAI Resource

1. **Apply for Azure OpenAI Access** (if you haven't already):
   - Go to https://aka.ms/oai/access
   - Fill out the application form
   - Wait for approval (usually 1-2 business days)

2. **Create Azure OpenAI Resource**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Click "Create a resource"
   - Search for "Azure OpenAI"
   - Click "Create"
   - Fill in:
     - Subscription: Your Azure subscription
     - Resource group: Create new or use existing
     - Region: Choose a region (e.g., East US, West Europe)
     - Name: Choose a unique name (e.g., `airflow-health-openai`)
     - Pricing tier: Standard S0
   - Click "Review + create" → "Create"

## Step 2: Deploy a Model

1. **Navigate to Azure OpenAI Studio**:
   - Go to your Azure OpenAI resource in Azure Portal
   - Click "Go to Azure OpenAI Studio" or visit https://oai.azure.com/
   
2. **Create a Deployment**:
   - Click "Deployments" in the left menu
   - Click "+ Create new deployment"
   - Select model: **GPT-4o** (recommended) or GPT-4
   - Choose deployment name (e.g., `gpt-4o-deployment`)
   - Click "Create"
   - Wait for deployment to complete

## Step 3: Get Configuration Values

### Get API Key:
1. Go to Azure Portal → Your OpenAI Resource
2. Click "Keys and Endpoint" in the left menu
3. Copy **KEY 1** or **KEY 2**

### Get Endpoint:
- Same page, copy the **Endpoint** URL
- Example: `https://your-resource-name.openai.azure.com/`

### Get Deployment Name:
- The name you chose in Step 2 (e.g., `gpt-4o-deployment`)

## Step 4: Update .env File

Edit `/Users/harikrishnan.r/Downloads/airflow-health-dashboard/.env` with your values:

```properties
# LLM Configuration
LLM_ENABLED=true
LLM_PROVIDER=azure_openai
LLM_API_KEY=your_actual_api_key_from_azure
LLM_MODEL=gpt-4o

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-deployment
```

**Example with real values:**
```properties
LLM_ENABLED=true
LLM_PROVIDER=azure_openai
LLM_API_KEY=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
LLM_MODEL=gpt-4o

AZURE_OPENAI_ENDPOINT=https://airflow-health-openai.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-deployment
```

## Step 5: Copy .env to Backend

```bash
cp .env backend/.env
```

## Step 6: Restart Backend Server

```bash
# If running manually
cd backend
source ../.venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Or if using the start script
./start.sh
```

## Step 7: Test the Feature

1. Open the dashboard at http://localhost:3000
2. If there are failed DAGs, you should see an "AI-Powered Failure Analysis" section at the bottom
3. The analysis includes:
   - Executive summary of failures
   - Categories of failures
   - Recommended action items
   - Consolidated logs with Airflow links

## Troubleshooting

### Error: "AZURE_OPENAI_ENDPOINT not configured"
- Make sure you've updated the `.env` file with your actual endpoint
- Ensure you copied `.env` to `backend/.env`

### Error: "Resource not found"
- Check that `AZURE_OPENAI_DEPLOYMENT_NAME` matches your actual deployment name
- Verify the deployment is in "Succeeded" state in Azure OpenAI Studio

### Error: "401 Unauthorized"
- Double-check your API key
- Make sure you copied the complete key without extra spaces

### Error: "Rate limit exceeded"
- Azure OpenAI has rate limits based on your quota
- Default quota is usually sufficient for this use case
- You can request quota increase in Azure Portal

## Model Recommendations

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| **GPT-4o** (Recommended) | Fast | Medium | Best balance of speed, cost, and quality |
| GPT-4 Turbo | Medium | Higher | More detailed analysis |
| GPT-3.5 Turbo | Fastest | Lowest | Budget-conscious, simple failures |

## Cost Estimate

For typical usage (analyzing failures a few times per day):
- GPT-4o: ~$0.50-2.00/month
- GPT-4 Turbo: ~$1.00-4.00/month
- GPT-3.5 Turbo: ~$0.10-0.50/month

Actual costs depend on:
- Number of failed DAGs
- Frequency of analysis
- Length of logs

## Security Best Practices

1. **Never commit .env to git** - it contains sensitive API keys
2. **Use Azure Key Vault** in production to store API keys
3. **Enable Azure AD authentication** for enhanced security
4. **Set up cost alerts** in Azure to monitor spending
5. **Rotate API keys regularly** (every 90 days recommended)

## Next Steps

After setup:
1. Monitor the analysis quality
2. Adjust the LLM prompts in `backend/app/llm_service.py` if needed
3. Consider caching analysis results longer if DAG failures are stable
4. Set up Azure Monitor to track API usage and costs

## Support

- Azure OpenAI Documentation: https://learn.microsoft.com/azure/ai-services/openai/
- Azure OpenAI Studio: https://oai.azure.com/
- Pricing: https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/
