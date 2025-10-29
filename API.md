# API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the dashboard itself doesn't require authentication (it's meant to be deployed behind SSO or internal network). However, it requires credentials to connect to the Airflow API, which are configured via environment variables.

## Endpoints

### Health Check

Check the status of the API and its dependencies.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "airflow_connection": "connected",
  "cache_status": "redis_healthy",
  "timestamp": "2025-10-29T10:30:00Z"
}
```

**Status Values:**
- `healthy`: All systems operational
- `degraded`: Some issues but functional
- `error`: Critical issues

---

### Get All Domains

Get health summary for all business domains.

**Endpoint:** `GET /domains`

**Query Parameters:**
- `time_range` (optional): `24h` | `7d` | `30d` (default: `24h`)

**Response:**
```json
{
  "time_range": "24h",
  "domains": [
    {
      "domain_tag": "Finance",
      "total_dags": 25,
      "total_runs": 150,
      "failed_count": 5,
      "success_count": 140,
      "running_count": 5,
      "queued_count": 0,
      "has_failures": true,
      "health_score": 93.33,
      "last_updated": "2025-10-29T10:30:00Z"
    }
  ],
  "total_domains": 10,
  "total_dags": 250,
  "last_updated": "2025-10-29T10:30:00Z"
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/domains?time_range=7d"
```

---

### Get Domain Detail

Get detailed information for a specific domain.

**Endpoint:** `GET /domains/{domain_tag}`

**Path Parameters:**
- `domain_tag`: The domain/tag name (URL encoded if contains special characters)

**Query Parameters:**
- `time_range` (optional): `24h` | `7d` | `30d` (default: `24h`)

**Response:**
```json
{
  "domain_tag": "Finance",
  "time_range": "24h",
  "summary": {
    "domain_tag": "Finance",
    "total_dags": 25,
    "total_runs": 150,
    "failed_count": 5,
    "success_count": 140,
    "running_count": 5,
    "queued_count": 0,
    "has_failures": true,
    "health_score": 93.33,
    "last_updated": "2025-10-29T10:30:00Z"
  },
  "dags": [
    {
      "dag_id": "finance_daily_report",
      "dag_display_name": "Finance Daily Report",
      "description": "Generate daily financial reports",
      "is_paused": false,
      "tags": ["Finance", "Daily"],
      "total_runs": 10,
      "failed_count": 1,
      "success_count": 8,
      "running_count": 1,
      "queued_count": 0,
      "last_run_state": "running",
      "last_run_date": "2025-10-29T09:00:00Z",
      "airflow_dag_url": "http://localhost:8080/dags/finance_daily_report/grid"
    }
  ],
  "last_updated": "2025-10-29T10:30:00Z"
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/domains/Finance?time_range=24h"
```

---

### Get DAG Runs

Get recent runs for a specific DAG.

**Endpoint:** `GET /domains/{domain_tag}/dags/{dag_id}/runs`

**Path Parameters:**
- `domain_tag`: The domain/tag name
- `dag_id`: The DAG identifier

**Query Parameters:**
- `time_range` (optional): `24h` | `7d` | `30d` (default: `24h`)
- `limit` (optional): Maximum number of runs to return (1-100, default: 50)

**Response:**
```json
[
  {
    "dag_id": "finance_daily_report",
    "dag_run_id": "scheduled__2025-10-29T09:00:00+00:00",
    "execution_date": "2025-10-29T09:00:00Z",
    "start_date": "2025-10-29T09:00:05Z",
    "end_date": "2025-10-29T09:15:30Z",
    "state": "success",
    "airflow_url": "http://localhost:8080/dags/finance_daily_report/grid?dag_run_id=scheduled__2025-10-29T09:00:00+00:00"
  }
]
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/domains/Finance/dags/finance_daily_report/runs?limit=20"
```

---

### Clear Cache

Force clear all cached data.

**Endpoint:** `POST /cache/clear`

**Response:**
```json
{
  "status": "success",
  "message": "Cache cleared"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/cache/clear"
```

**Note:** This endpoint should be protected in production environments.

---

## Data Models

### DagRunState

Possible values:
- `success`
- `failed`
- `running`
- `queued`

### TimeRange

Possible values:
- `24h` - Last 24 hours
- `7d` - Last 7 days
- `30d` - Last 30 days

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Request successful
- `404 Not Found`: Domain or DAG not found
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: Unable to connect to Airflow

---

## Rate Limiting

Currently no rate limiting is implemented. In production, consider:
- Per-IP rate limiting
- Per-user rate limiting (if authenticated)
- API key-based quotas

---

## Caching

The API implements caching to reduce load on the Airflow API:

- Default cache TTL: 120 seconds (configurable)
- Cache key format: `{endpoint}:{parameters}`
- Cache can be cleared via the `/cache/clear` endpoint
- Cache status visible in `/health` endpoint

---

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Browse all endpoints
- See request/response schemas
- Test API calls directly in the browser
- Download OpenAPI specification

---

## Example Usage

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get all domains
response = requests.get(f"{BASE_URL}/domains", params={"time_range": "24h"})
domains = response.json()

# Get domain detail
response = requests.get(f"{BASE_URL}/domains/Finance")
finance_detail = response.json()

# Get DAG runs
response = requests.get(
    f"{BASE_URL}/domains/Finance/dags/finance_daily_report/runs",
    params={"limit": 10}
)
runs = response.json()
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000/api/v1';

// Get all domains
const getDomains = async (timeRange = '24h') => {
  const response = await axios.get(`${BASE_URL}/domains`, {
    params: { time_range: timeRange }
  });
  return response.data;
};

// Get domain detail
const getDomainDetail = async (domainTag, timeRange = '24h') => {
  const response = await axios.get(`${BASE_URL}/domains/${domainTag}`, {
    params: { time_range: timeRange }
  });
  return response.data;
};
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Get all domains (last 7 days)
curl "http://localhost:8000/api/v1/domains?time_range=7d"

# Get Finance domain detail
curl "http://localhost:8000/api/v1/domains/Finance"

# Get recent runs for a DAG
curl "http://localhost:8000/api/v1/domains/Finance/dags/finance_daily_report/runs?limit=10"

# Clear cache
curl -X POST http://localhost:8000/api/v1/cache/clear
```
