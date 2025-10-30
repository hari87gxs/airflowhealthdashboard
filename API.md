# API Documentation - Airflow Health Dashboard

## Production System Overview

This API serves the Airflow Health Dashboard, currently monitoring **294 DAGs** across **8 business domains** with real-time health analytics and AI-powered failure analysis.

## Base URL

```
http://localhost:8000
```

## Authentication

The dashboard uses environment-based authentication for Airflow integration:
- **Development**: Basic auth with username/password
- **Production**: Azure OpenAI integration for AI analysis
- **Airflow Connection**: Configured via environment variables (AIRFLOW_BASE_URL, credentials)

## 🚀 Core Endpoints

### System Health

Check the overall system status, cache performance, and AI service connectivity.

**Endpoint:** `GET /health`

**Current Response (Live System):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "airflow_connection": "connected",
  "cache_status": "294_dags_cached",
  "ai_service": "azure_openai_active",
  "background_tasks": "running",
  "response_time_ms": 45,
  "last_refresh": "2025-01-18T10:25:00Z",
  "domains_count": 8,
  "total_dags": 294
}
```

**Status Indicators:**
- `healthy`: All systems operational (~94% success rate)
- `degraded`: Some issues but functional
- `error`: Critical issues requiring attention

---

### Domain Overview

Get real-time health summary for all business domains with current metrics.

**Endpoint:** `GET /api/v1/domains`

**Query Parameters:**
- `time_range` (optional): `24h` | `7d` | `30d` (default: `24h`)

**Live Response (Current System):**
```json
{
  "time_range": "24h",
  "domains": [
    {
      "domain_tag": "Finance",
      "total_dags": 45,
      "total_runs": 312,
      "failed_count": 12,
      "success_count": 295,
      "running_count": 5,
      "queued_count": 0,
      "has_failures": true,
      "health_score": 96.2,
      "last_updated": "2025-01-18T10:25:00Z",
      "failure_categories": ["Infrastructure", "Data Quality"],
      "avg_duration_minutes": 12.5
    },
    {
      "domain_tag": "Ecosystem",
      "total_dags": 38,
      "total_runs": 284,
      "failed_count": 23,
      "success_count": 256,
      "running_count": 3,
      "queued_count": 2,
      "has_failures": true,
      "health_score": 92.1,
      "last_updated": "2025-01-18T10:25:00Z",
      "failure_categories": ["External Dependencies", "Logic"],
      "avg_duration_minutes": 8.3
    },
    {
      "domain_tag": "Marketing",
      "total_dags": 42,
      "total_runs": 298,
      "failed_count": 15,
      "success_count": 278,
      "running_count": 4,
      "queued_count": 1,
      "has_failures": true,
      "health_score": 94.9,
      "last_updated": "2025-01-18T10:25:00Z",
      "failure_categories": ["Data Quality"],
      "avg_duration_minutes": 15.2
    }
  ],
  "total_domains": 8,
  "total_dags": 294,
  "overall_health_score": 94.1,
  "cache_hit_ratio": 0.95,
  "last_updated": "2025-01-18T10:25:00Z"
}
```

---

### Domain Detail with AI Analysis

Get comprehensive domain information including DAG-level details and AI-powered insights.

**Endpoint:** `GET /api/v1/domains/{domain_tag}`

**Path Parameters:**
- `domain_tag`: Business domain name (Finance, Ecosystem, Marketing, etc.)

**Query Parameters:**
- `time_range` (optional): `24h` | `7d` | `30d` (default: `24h`)
- `include_analysis` (optional): `true` | `false` (default: `false`)

**Enhanced Response (With AI Analysis):**
```json
{
  "domain_tag": "Finance",
  "time_range": "24h",
  "summary": {
    "domain_tag": "Finance",
    "total_dags": 45,
    "total_runs": 312,
    "failed_count": 12,
    "success_count": 295,
    "running_count": 5,
    "queued_count": 0,
    "has_failures": true,
    "health_score": 96.2,
    "last_updated": "2025-01-18T10:25:00Z"
  },
  "ai_analysis": {
    "failure_categories": {
      "Infrastructure": {
        "count": 7,
        "percentage": 58.3,
        "common_causes": ["Network timeouts", "Resource constraints"],
        "recommendations": ["Increase timeout settings", "Scale infrastructure"]
      },
      "Data Quality": {
        "count": 5,
        "percentage": 41.7,
        "common_causes": ["Missing source data", "Schema changes"],
        "recommendations": ["Implement data validation", "Add schema monitoring"]
      }
    },
    "patterns": [
      {
        "pattern": "Morning peak failures",
        "description": "Higher failure rate between 8-10 AM",
        "impact": "medium",
        "recommendation": "Stagger DAG schedules"
      }
    ],
    "summary": "Finance domain shows strong performance with isolated infrastructure issues during peak hours."
  },
  "dags": [
    {
      "dag_id": "finance_daily_settlement",
      "dag_display_name": "Finance Daily Settlement",
      "description": "Process daily financial settlements and reconciliation",
      "is_paused": false,
      "tags": ["Finance", "Daily", "Critical"],
      "total_runs": 15,
      "failed_count": 2,
      "success_count": 12,
      "running_count": 1,
      "queued_count": 0,
      "last_run_state": "running",
      "last_run_date": "2025-01-18T09:00:00Z",
      "airflow_dag_url": "https://airflow.sgbank.st/dags/finance_daily_settlement/grid",
      "avg_duration_minutes": 18.5,
      "failure_pattern": "infrastructure",
      "criticality": "high"
    }
  ],
  "performance_metrics": {
    "avg_response_time_ms": 284,
    "cache_efficiency": 0.98,
    "data_freshness_seconds": 125
  },
  "last_updated": "2025-01-18T10:25:00Z"
}
```

---

### AI-Powered Failure Analysis

Get intelligent analysis of failures across domains or specific DAGs.

**Endpoint:** `POST /api/v1/analysis/failures`

**Request Body:**
```json
{
  "domain_tag": "Finance",
  "time_range": "24h",
  "analysis_depth": "detailed",
  "include_recommendations": true
}
```

**AI Analysis Response:**
```json
{
  "analysis_id": "fa_20250118_102500_finance",
  "domain": "Finance",
  "time_range": "24h",
  "generated_at": "2025-01-18T10:25:00Z",
  "summary": {
    "total_failures": 12,
    "critical_issues": 3,
    "patterns_identified": 2,
    "actionable_recommendations": 5
  },
  "categorized_failures": {
    "Infrastructure": {
      "count": 7,
      "severity": "medium",
      "affected_dags": ["finance_daily_settlement", "finance_reporting"],
      "root_causes": [
        "Database connection timeouts during peak hours",
        "Insufficient memory allocation for large data processing"
      ],
      "immediate_actions": [
        "Increase database connection timeout to 30 seconds",
        "Scale worker memory from 4GB to 8GB"
      ],
      "preventive_measures": [
        "Implement connection pooling",
        "Add memory monitoring alerts"
      ]
    },
    "Data Quality": {
      "count": 5,
      "severity": "high",
      "affected_dags": ["finance_data_validation", "finance_reconciliation"],
      "root_causes": [
        "Upstream source system schema changes",
        "Missing mandatory fields in source data"
      ],
      "immediate_actions": [
        "Add schema validation step before processing",
        "Implement data quality checks with circuit breaker"
      ],
      "preventive_measures": [
        "Establish data contracts with upstream systems",
        "Deploy automated schema monitoring"
      ]
    }
  },
  "patterns": [
    {
      "pattern": "Time-based failures",
      "description": "67% of failures occur between 8-10 AM during market opening",
      "confidence": 0.85,
      "recommendation": "Implement staggered scheduling to distribute load",
      "expected_improvement": "40% reduction in morning failures"
    }
  ],
  "priority_actions": [
    {
      "action": "Increase database timeout settings",
      "impact": "high",
      "effort": "low",
      "timeline": "immediate"
    },
    {
      "action": "Implement data quality gates",
      "impact": "high",
      "effort": "medium",
      "timeline": "1-2 weeks"
    }
  ]
}
```

---

### DAG Run History

Get detailed execution history for specific DAGs with performance metrics.

**Endpoint:** `GET /api/v1/domains/{domain_tag}/dags/{dag_id}/runs`

**Path Parameters:**
- `domain_tag`: Business domain (Finance, Ecosystem, etc.)
- `dag_id`: Specific DAG identifier

**Query Parameters:**
- `time_range` (optional): `24h` | `7d` | `30d` (default: `24h`)
- `limit` (optional): Max runs to return (1-100, default: 25)
- `include_metrics` (optional): Include performance data (default: `true`)

**Production Response:**
```json
{
  "dag_id": "finance_daily_settlement",
  "domain": "Finance",
  "time_range": "24h",
  "total_runs": 15,
  "performance_summary": {
    "avg_duration_minutes": 18.5,
    "success_rate": 80.0,
    "fastest_run_minutes": 12.3,
    "slowest_run_minutes": 28.7
  },
  "runs": [
    {
      "dag_run_id": "scheduled__2025-01-18T09:00:00+00:00",
      "execution_date": "2025-01-18T09:00:00Z",
      "start_date": "2025-01-18T09:00:05Z",
      "end_date": "2025-01-18T09:18:30Z",
      "state": "success",
      "duration_minutes": 18.4,
      "airflow_url": "https://airflow.sgbank.st/dags/finance_daily_settlement/grid?dag_run_id=scheduled__2025-01-18T09:00:00+00:00",
      "task_failures": 0,
      "data_interval_start": "2025-01-17T09:00:00Z",
      "data_interval_end": "2025-01-18T09:00:00Z"
    },
    {
      "dag_run_id": "scheduled__2025-01-17T09:00:00+00:00",
      "execution_date": "2025-01-17T09:00:00Z",
      "start_date": "2025-01-17T09:00:12Z",
      "end_date": null,
      "state": "failed",
      "duration_minutes": null,
      "failure_reason": "Infrastructure timeout",
      "airflow_url": "https://airflow.sgbank.st/dags/finance_daily_settlement/grid?dag_run_id=scheduled__2025-01-17T09:00:00+00:00",
      "task_failures": 1,
      "failed_task": "settlement_processing"
    }
  ],
  "last_updated": "2025-01-18T10:25:00Z"
}
```

### Cache Management

Advanced cache operations for performance optimization.

**Endpoint:** `POST /api/v1/cache/refresh`

**Request Body:**
```json
{
  "force": true,
  "domains": ["Finance", "Marketing"],
  "background": false
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Cache refreshed for 2 domains",
  "refresh_time_ms": 1250,
  "cache_stats": {
    "total_entries": 294,
    "hit_ratio": 0.95,
    "last_refresh": "2025-01-18T10:25:00Z",
    "next_scheduled_refresh": "2025-01-18T10:30:00Z"
  }
}
```

**Clear Cache Endpoint:** `DELETE /api/v1/cache`
```json
{
  "status": "success",
  "message": "All cache cleared",
  "entries_cleared": 294
}
```

## 📊 Enhanced Data Models

### DomainSummary (Current Production Model)

```typescript
interface DomainSummary {
  domain_tag: string;
  total_dags: number;
  total_runs: number;
  failed_count: number;
  success_count: number;
  running_count: number;
  queued_count: number;
  has_failures: boolean;
  health_score: number;  // 0-100 percentage
  avg_duration_minutes: number;
  failure_categories: string[];
  last_updated: string;  // ISO datetime
}
```

### DAGDetail (Enhanced Production Model)

```typescript
interface DAGDetail {
  dag_id: string;
  dag_display_name: string;
  description: string;
  is_paused: boolean;
  tags: string[];
  total_runs: number;
  failed_count: number;
  success_count: number;
  running_count: number;
  queued_count: number;
  last_run_state: "success" | "failed" | "running" | "queued";
  last_run_date: string;
  airflow_dag_url: string;
  avg_duration_minutes: number;
  failure_pattern?: string;
  criticality: "low" | "medium" | "high";
}
```

### AIAnalysis (Azure OpenAI Integration)

```typescript
interface AIAnalysis {
  analysis_id: string;
  domain: string;
  time_range: string;
  generated_at: string;
  summary: {
    total_failures: number;
    critical_issues: number;
    patterns_identified: number;
    actionable_recommendations: number;
  };
  categorized_failures: {
    [category: string]: {
      count: number;
      severity: "low" | "medium" | "high";
      affected_dags: string[];
      root_causes: string[];
      immediate_actions: string[];
      preventive_measures: string[];
    };
  };
  patterns: Array<{
    pattern: string;
    description: string;
    confidence: number;
    recommendation: string;
    expected_improvement: string;
  }>;
  priority_actions: Array<{
    action: string;
    impact: "low" | "medium" | "high";
    effort: "low" | "medium" | "high";
    timeline: string;
  }>;
}
```

## 🔧 Performance & Caching

### Current System Performance
- **API Response Time**: <500ms (95th percentile)
- **Cache Hit Ratio**: 95%+ 
- **Background Refresh**: Every 5 minutes
- **Data Freshness**: 2-minute cache TTL
- **Concurrent Connections**: Up to 50 simultaneous requests

### Cache Strategy
```json
{
  "cache_levels": {
    "domains_list": "120_seconds",
    "domain_detail": "60_seconds", 
    "dag_runs": "300_seconds",
    "ai_analysis": "1800_seconds"
  },
  "refresh_strategy": "background_async",
  "invalidation": "time_based_with_manual_override"
}
```

## 🚨 Error Handling

### Production Error Responses

**Standard Error Format:**
```json
{
  "error": {
    "code": "AIRFLOW_CONNECTION_ERROR",
    "message": "Unable to connect to Airflow instance",
    "details": {
      "airflow_url": "https://airflow.sgbank.st",
      "connection_timeout": "30s",
      "retry_count": 3
    },
    "timestamp": "2025-01-18T10:25:00Z",
    "request_id": "req_20250118_102500_001"
  }
}
```

**HTTP Status Codes:**
- `200 OK`: Successful operation
- `202 Accepted`: Background task initiated
- `404 Not Found`: Domain/DAG not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: System error
- `502 Bad Gateway`: Airflow connection issue
- `503 Service Unavailable`: Maintenance mode

## 🔌 Client Integration Examples

### Python Production Client

```python
import asyncio
import aiohttp
from typing import Dict, List, Optional

class AirflowHealthClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    async def get_domains(self, time_range: str = "24h") -> Dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/domains",
                params={"time_range": time_range}
            ) as response:
                return await response.json()
    
    async def get_domain_with_analysis(self, domain: str) -> Dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/domains/{domain}",
                params={"include_analysis": "true"}
            ) as response:
                return await response.json()
    
    async def analyze_failures(self, domain: str) -> Dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/analysis/failures",
                json={
                    "domain_tag": domain,
                    "time_range": "24h",
                    "analysis_depth": "detailed"
                }
            ) as response:
                return await response.json()

# Usage example
client = AirflowHealthClient()
domains = await client.get_domains("7d")
finance_analysis = await client.analyze_failures("Finance")
```

### React/TypeScript Frontend Integration

```typescript
interface DashboardAPI {
  getDomains: (timeRange?: string) => Promise<DomainsResponse>;
  getDomainDetail: (domain: string, includeAnalysis?: boolean) => Promise<DomainDetailResponse>;
  analyzeFailures: (domain: string) => Promise<AIAnalysisResponse>;
  refreshCache: (domains?: string[]) => Promise<CacheResponse>;
}

class AirflowHealthAPI implements DashboardAPI {
  private baseURL = 'http://localhost:8000';
  
  async getDomains(timeRange = '24h'): Promise<DomainsResponse> {
    const response = await fetch(`${this.baseURL}/api/v1/domains?time_range=${timeRange}`);
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return response.json();
  }
  
  async getDomainDetail(domain: string, includeAnalysis = true): Promise<DomainDetailResponse> {
    const url = `${this.baseURL}/api/v1/domains/${encodeURIComponent(domain)}`;
    const params = new URLSearchParams({ include_analysis: includeAnalysis.toString() });
    
    const response = await fetch(`${url}?${params}`);
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return response.json();
  }
}

// React Hook usage
const useDomainHealth = (timeRange = '24h') => {
  const [domains, setDomains] = useState<DomainSummary[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const api = new AirflowHealthAPI();
    api.getDomains(timeRange)
      .then(data => setDomains(data.domains))
      .finally(() => setLoading(false));
  }, [timeRange]);
  
  return { domains, loading };
};
```

## 📈 Production Monitoring

### Health Check Monitoring
```bash
# Continuous health monitoring
while true; do
  curl -s http://localhost:8000/health | jq '.status'
  sleep 30
done

# Performance monitoring
curl -s http://localhost:8000/health | jq '{
  status: .status,
  response_time: .response_time_ms,
  cache_efficiency: .cache_status,
  total_dags: .total_dags
}'
```

### Interactive Documentation

**Swagger UI (Full API Testing):** http://localhost:8000/docs
- Live API testing interface
- Complete request/response schemas
- Authentication testing
- Performance metrics

**ReDoc (Comprehensive Documentation):** http://localhost:8000/redoc
- Detailed API reference
- Code examples in multiple languages
- Schema documentation
- Integration guides

---

*This API documentation reflects the current production system monitoring 294 DAGs across 8 business domains with AI-powered analysis and <500ms response times.*
