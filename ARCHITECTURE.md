# Airflow Health Dashboard - Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Backend Architecture](#backend-architecture)
5. [Frontend Architecture](#frontend-architecture)
6. [Data Flow](#data-flow)
7. [API Design](#api-design)
8. [Caching Strategy](#caching-strategy)
9. [Security Considerations](#security-considerations)
10. [Deployment Architecture](#deployment-architecture)
11. [Code Organization](#code-organization)

---

## Overview

The Airflow Health Dashboard is a **read-only monitoring application** designed to provide high-level visibility into the health of 250+ Apache Airflow DAGs organized by business domains. The system aggregates DAG execution status by domain tags, enabling non-technical stakeholders to quickly identify system health issues without diving into the Airflow UI.

### Design Principles

- **Read-Only Access**: No ability to trigger or modify DAGs (security by design)
- **Performance Optimized**: Intelligent caching to minimize load on Airflow API
- **Domain-Focused**: Business-oriented view rather than technical DAG details
- **Progressive Disclosure**: Dashboard → Domain → DAG → Run hierarchy
- **API-First**: No direct database access to Airflow metastore

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         End Users                                │
│                  (Business Stakeholders)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend Layer                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  React Application (Vite)                                 │  │
│  │  - Dashboard Component (Domain List)                      │  │
│  │  - DomainDetail Component (DAG List)                      │  │
│  │  - Time Range Filtering                                   │  │
│  │  - Auto-refresh Mechanism                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                 Port 3000 (Development) / 80 (Docker)           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ REST API (JSON)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend Layer                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application                                      │  │
│  │  ┌────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │   Routes   │→ │   Service   │→ │ Airflow Client  │   │  │
│  │  │  (API)     │  │  (Business  │  │   (API Calls)   │   │  │
│  │  │            │  │   Logic)    │  │                 │   │  │
│  │  └────────────┘  └──────┬──────┘  └────────┬────────┘   │  │
│  │                          │                  │             │  │
│  │                          ▼                  │             │  │
│  │                  ┌──────────────┐           │             │  │
│  │                  │Cache Service │           │             │  │
│  │                  │(Redis/Memory)│           │             │  │
│  │                  └──────────────┘           │             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                     Port 8000                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ REST API (Basic Auth / Token)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Apache Airflow                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Airflow REST API (v1)                                    │  │
│  │  - GET /dags (List all DAGs)                              │  │
│  │  - GET /dags/{dag_id}/dagRuns (Get DAG runs)              │  │
│  │  - GET /health (Health check)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                     Port 8080                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Browser → React App → API Client (axios) → FastAPI Backend
                                                      ↓
                                          ┌───────────┴──────────┐
                                          ▼                      ▼
                                   Cache Service          Airflow Client
                                   (Check Cache)        (Make API Calls)
                                          ↓                      ↓
                                   Cache Hit?            Airflow REST API
                                    ↓     ↓                      ↓
                                  Yes    No ←───────────────────┘
                                   ↓      ↓
                              Return  Process &
                              Cached   Cache
                              Data     Result
                                   ↓      ↓
                                   └──────┴→ Return to Frontend
```

---

## Technology Stack

### Backend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | FastAPI | Latest | High-performance async web framework |
| **Language** | Python | 3.9+ | Backend programming language |
| **HTTP Client** | httpx | Latest | Async HTTP client for Airflow API calls |
| **Validation** | Pydantic | Latest | Data validation and settings management |
| **Logging** | Loguru | Latest | Structured logging with colors |
| **Caching** | Redis (optional) | 7.x | Distributed caching layer |
| **Server** | Uvicorn | Latest | ASGI server for FastAPI |

### Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | React | 18.x | UI component library |
| **Build Tool** | Vite | Latest | Fast development and build tool |
| **Styling** | Tailwind CSS | 3.x | Utility-first CSS framework |
| **Routing** | React Router | 6.x | Client-side routing |
| **HTTP Client** | Axios | Latest | HTTP client for API calls |
| **Date Formatting** | date-fns | Latest | Date manipulation and formatting |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Containerization** | Docker | Application packaging |
| **Orchestration** | Docker Compose | Multi-container deployment |
| **Cache Store** | Redis | Optional distributed caching |
| **Web Server** | Nginx | Frontend static file serving |

---

## Backend Architecture

### Layer Architecture

The backend follows a **layered architecture** pattern with clear separation of concerns:

```
┌──────────────────────────────────────────┐
│         Presentation Layer                │
│  - FastAPI Routes (routes.py)            │
│  - Request/Response Models                │
│  - HTTP Status Codes                      │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│         Business Logic Layer              │
│  - HealthService (service.py)            │
│  - Domain Aggregation Logic              │
│  - Health Score Calculation              │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│         Data Access Layer                 │
│  - AirflowAPIClient (airflow_client.py)  │
│  - CacheService (cache.py)               │
│  - API Request/Response Handling         │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│         External Services                 │
│  - Airflow REST API                      │
│  - Redis (optional)                      │
└──────────────────────────────────────────┘
```

### Core Components

#### 1. **Main Application (`main.py`)**

**Purpose**: Application entry point and configuration

**Responsibilities**:
- Initialize FastAPI application
- Configure CORS middleware
- Register API routes
- Set up logging
- Define startup/shutdown events

**Key Code**:
```python
app = FastAPI(
    title="Airflow Health Dashboard API",
    description="Read-only monitoring dashboard",
    version=__version__
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"]
)

# Include routes with API prefix
app.include_router(router, prefix=settings.api_prefix)
```

#### 2. **Configuration Management (`config.py`)**

**Purpose**: Centralized configuration using environment variables

**Features**:
- Type-safe settings using Pydantic
- Environment variable validation
- Default values for optional settings
- Authentication validation (ensures either token or username/password)

**Configuration Categories**:
- **Airflow Configuration**: URL, credentials, API token
- **Cache Configuration**: TTL, refresh intervals
- **Backend Configuration**: Host, port, CORS origins
- **Logging Configuration**: Log level

**Key Validation**:
```python
@validator("airflow_api_token", "airflow_username", "airflow_password")
def validate_auth(cls, v, values):
    # Ensures either API token or username/password is provided
    has_token = values.get("airflow_api_token") is not None
    has_basic = values.get("airflow_username") and values.get("airflow_password")
    
    if not has_token and not has_basic:
        raise ValueError("Authentication required")
    return v
```

#### 3. **Data Models (`models.py`)**

**Purpose**: Define data structures and validation rules

**Models Hierarchy**:

```
DashboardResponse
  ├── time_range: TimeRange
  ├── domains: List[DomainHealthSummary]
  │     ├── domain_tag: str
  │     ├── total_dags: int
  │     ├── total_runs: int
  │     ├── failed_count: int
  │     ├── success_count: int
  │     ├── running_count: int
  │     ├── queued_count: int
  │     ├── has_failures: bool
  │     └── health_score: float (0-100)
  ├── total_domains: int
  └── total_dags: int

DomainDetailResponse
  ├── domain_tag: str
  ├── time_range: TimeRange
  ├── summary: DomainHealthSummary
  └── dags: List[DagHealthSummary]
        ├── dag_id: str
        ├── description: str
        ├── is_paused: bool
        ├── tags: List[str]
        ├── total_runs: int
        ├── failed_count: int
        ├── success_count: int
        ├── last_run_state: DagRunState
        └── airflow_dag_url: str

DagRunSummary
  ├── dag_run_id: str
  ├── execution_date: datetime
  ├── state: DagRunState
  └── airflow_url: str
```

**Enums**:
- `DagRunState`: SUCCESS, FAILED, RUNNING, QUEUED
- `TimeRange`: HOURS_24 (24h), DAYS_7 (7d), DAYS_30 (30d)

#### 4. **Airflow API Client (`airflow_client.py`)**

**Purpose**: Handle all communication with Airflow REST API

**Authentication Support**:
- Basic Authentication (username/password)
- Token Authentication (Bearer token)

**Key Methods**:

| Method | Purpose | Caching |
|--------|---------|---------|
| `test_connection()` | Verify Airflow connectivity | No |
| `get_all_dags()` | Fetch all DAGs with pagination | Yes (via service) |
| `get_dag_runs()` | Get runs for a specific DAG | Yes (via service) |
| `get_all_dag_runs_for_dags()` | Concurrent fetching for multiple DAGs | Yes (via service) |

**Concurrency Optimization**:
```python
async def get_all_dag_runs_for_dags(self, dag_ids, time_range):
    # Use asyncio.gather for concurrent API calls
    async with httpx.AsyncClient(timeout=self.timeout) as client:
        tasks = [self._fetch_dag_run(dag_id) for dag_id in dag_ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
```

**Error Handling**:
- HTTP errors logged with status code and response text
- Request errors (network issues) logged and raised
- Individual DAG failures don't break batch requests

#### 5. **Health Service (`service.py`)**

**Purpose**: Business logic for health calculations and aggregation

**Core Responsibilities**:
1. **Dashboard Data Generation**: Aggregate all domains
2. **Domain Detail Generation**: DAG-level breakdown
3. **Health Score Calculation**: Success rate computation
4. **Data Grouping**: Group DAGs by tags
5. **Sorting Logic**: Prioritize failures

**Health Score Calculation**:
```python
if total_runs > 0:
    health_score = (total_success / total_runs) * 100
else:
    health_score = 100.0  # No runs = healthy
```

**Sorting Strategy**:
- **Dashboard**: Domains with failures first, then alphabetically
- **Domain Detail**: DAGs with failures first, then alphabetically

**Key Methods**:

| Method | Input | Output | Cache Key |
|--------|-------|--------|-----------|
| `get_dashboard_data()` | TimeRange | DashboardResponse | `dashboard:{time_range}` |
| `get_domain_detail()` | domain_tag, TimeRange | DomainDetailResponse | `domain:{tag}:{time_range}` |
| `get_dag_runs()` | dag_id, TimeRange | List[DagRunSummary] | Not cached |

**Data Aggregation Flow**:
```python
# 1. Fetch all DAGs from Airflow
dags = await airflow_client.get_all_dags()

# 2. Group by tags
dags_by_tag = self._group_dags_by_tags(dags)

# 3. For each tag, fetch runs and calculate metrics
for tag, tag_dags in dags_by_tag.items():
    dag_ids = [dag["dag_id"] for dag in tag_dags]
    all_runs = await airflow_client.get_all_dag_runs_for_dags(dag_ids)
    
    # Count states
    for runs in all_runs.values():
        for run in runs:
            if run['state'] == 'failed': failed_count += 1
            elif run['state'] == 'success': success_count += 1
            # ... etc
    
    # Calculate health score
    health_score = (success_count / total_runs) * 100
```

#### 6. **Cache Service (`cache.py`)**

**Purpose**: Performance optimization through caching

**Features**:
- Dual-mode caching: Redis (distributed) or In-memory (simple)
- Automatic TTL management
- Fallback to in-memory if Redis unavailable
- Cache cleanup for memory mode

**Cache Operations**:

| Operation | Method | Parameters |
|-----------|--------|-----------|
| Get | `get(key)` | key: str |
| Set | `set(key, value, ttl)` | key: str, value: Any, ttl: Optional[int] |
| Delete | `delete(key)` | key: str |
| Clear All | `clear_all()` | None |

**In-Memory Cache Cleanup**:
```python
def _cleanup_memory_cache(self):
    # Remove expired entries when cache > 1000 items
    current_time = datetime.utcnow()
    expired_keys = [
        key for key, timestamp in self.cache_timestamps.items()
        if current_time - timestamp >= timedelta(seconds=ttl)
    ]
    for key in expired_keys:
        del self.memory_cache[key]
```

**Cache Status Reporting**:
- Redis: `redis_healthy` or `redis_error`
- In-memory: `in_memory_{count}_entries`

#### 7. **API Routes (`api/routes.py`)**

**Purpose**: HTTP endpoint definitions

**Endpoints**:

| Endpoint | Method | Purpose | Response Model |
|----------|--------|---------|----------------|
| `/health` | GET | Health check | HealthCheckResponse |
| `/domains` | GET | All domain summaries | DashboardResponse |
| `/domains/{tag}` | GET | Domain detail | DomainDetailResponse |
| `/domains/{tag}/dags/{dag_id}/runs` | GET | DAG runs | List[DagRunSummary] |
| `/cache/clear` | POST | Clear cache | Status message |

**Query Parameters**:
- `time_range`: 24h, 7d, 30d (default: 24h)
- `limit`: Maximum runs to return (1-100, default: 50)

**Error Handling**:
```python
try:
    return await health_service.get_dashboard_data(time_range)
except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))
except Exception as e:
    logger.error(f"Error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
```

---

## Frontend Architecture

### Component Architecture

```
App.jsx (Root)
  ├── Header (Navigation + Health Status)
  ├── Router
  │   ├── Dashboard.jsx (Route: /)
  │   │   ├── Time Range Selector
  │   │   ├── Auto-refresh Toggle
  │   │   ├── Summary Stats Cards
  │   │   └── Domain List
  │   │       └── DomainCard (clickable)
  │   │
  │   └── DomainDetail.jsx (Route: /domain/:tag)
  │       ├── Back Button
  │       ├── Domain Summary
  │       └── DAG List
  │           └── DAGCard (expandable)
  │               └── DAG Runs List
  └── Footer
```

### Frontend UI Mockups

#### Dashboard View (Main Page)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Airflow Health Dashboard                    🟢 Connected    Open Airflow UI →   │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  Time Range: [Last 24 Hours ▼]  ☑ Auto-refresh   [Refresh]                     │
│  Last updated: 2 minutes ago                                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────────┬──────────────────┐
│ Total        │ Total        │ Domains with     │ Healthy          │
│ Domains      │ DAGs         │ Failures         │ Domains          │
│              │              │                  │                  │
│    10        │    250       │      3           │      7           │
└──────────────┴──────────────┴──────────────────┴──────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ Business Domains                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ 🔴 Finance                                           [5 Failed]            ➤ ┃ │
│ ┃ DAGs: 45  Runs: 230  Success: 180  Failed: 5  Health: 78.3%                ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                                                  │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ 🔴 Marketing                                        [3 Failed]            ➤ ┃ │
│ ┃ DAGs: 32  Runs: 156  Success: 142  Failed: 3  Health: 91.0%                ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                                                  │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ 🔴 Data-Science                                     [2 Failed]            ➤ ┃ │
│ ┃ DAGs: 28  Runs: 98   Success: 89   Failed: 2  Health: 90.8%                ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                                                  │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🔵 Engineering                                    [2 Running]            ➤ │ │
│ │ DAGs: 38  Runs: 189  Success: 185  Failed: 0  Health: 97.9%               │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🟢 Sales                                              [Healthy]          ➤ │ │
│ │ DAGs: 22  Runs: 110  Success: 110  Failed: 0  Health: 100.0%              │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🟢 Analytics                                          [Healthy]          ➤ │ │
│ │ DAGs: 35  Runs: 175  Success: 175  Failed: 0  Health: 100.0%              │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🟢 Operations                                         [Healthy]          ➤ │ │
│ │ DAGs: 18  Runs: 90   Success: 90   Failed: 0  Health: 100.0%              │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ v1.0.0 · Read-only monitoring dashboard · Data refreshed every 2 minutes        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Visual Design Elements**:
- 🔴 **Red Border/Background**: Domains with failures (prioritized at top)
- 🔵 **Blue Border/Background**: Domains with running DAGs
- 🟢 **Green Border/Background**: Healthy domains (100% success)
- **Bold Red Count**: Failed count badge
- **Right Arrow** (➤): Indicates clickable/drilldown

---

#### Domain Detail View (After Clicking a Domain)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Airflow Health Dashboard                    🟢 Connected    Open Airflow UI →   │
└─────────────────────────────────────────────────────────────────────────────────┘

← Back to Dashboard                                  Time Range: [Last 24 Hours ▼]

┌─────────────────────────────────────────────────────────────────────────────────┐
│ Finance                                                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  DAGs     Total Runs     Success     Failed     Health Score                    │
│   45         230           180         5          78.3%                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ DAGs in Finance                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ invoice_processing_pipeline                 View in Airflow →            ▼ ┃ │
│ ┃ Daily invoice processing and reconciliation                                 ┃ │
│ ┃                                                                              ┃ │
│ ┃ Total Runs: 24  Success: 20  Failed: 3  Running: 1  Last Run: 10 mins ago  ┃ │
│ ┃─────────────────────────────────────────────────────────────────────────────┃ │
│ ┃ Recent Runs                                                                  ┃ │
│ ┃ ┌───────────────────────────────────────────────────────────────────────┐   ┃ │
│ ┃ │ [running] Oct 29, 2025 10:30:00                     View →            │   ┃ │
│ ┃ └───────────────────────────────────────────────────────────────────────┘   ┃ │
│ ┃ ┌───────────────────────────────────────────────────────────────────────┐   ┃ │
│ ┃ │ [failed]  Oct 29, 2025 09:30:00  Duration: 1245s    View →            │   ┃ │
│ ┃ └───────────────────────────────────────────────────────────────────────┘   ┃ │
│ ┃ ┌───────────────────────────────────────────────────────────────────────┐   ┃ │
│ ┃ │ [success] Oct 29, 2025 08:30:00  Duration: 567s     View →            │   ┃ │
│ ┃ └───────────────────────────────────────────────────────────────────────┘   ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                                                  │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ payment_gateway_sync                        View in Airflow →            ▶ ┃ │
│ ┃ Sync payment data from external gateway                                     ┃ │
│ ┃                                                                              ┃ │
│ ┃ Total Runs: 24  Success: 22  Failed: 2  Running: 0  Last Run: 1 hour ago   ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                                                  │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ financial_reporting_daily                   View in Airflow →            ▶ │ │
│ │ Generate daily financial reports for stakeholders                           │ │
│ │                                                                              │ │
│ │ Total Runs: 24  Success: 24  Failed: 0  Running: 0  Last Run: 2 hours ago  │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ revenue_recognition_etl  [Paused]           View in Airflow →            ▶ │ │
│ │ ETL pipeline for revenue recognition data                                   │ │
│ │                                                                              │ │
│ │ Total Runs: 0   Success: 0   Failed: 0  Running: 0  Last Run: never        │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ v1.0.0 · Read-only monitoring dashboard · Data refreshed every 2 minutes        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Visual Design Elements**:
- **Expandable DAGs**: ▼ (expanded) / ▶ (collapsed)
- **State Badges**:
  - `[running]` - Blue background
  - `[failed]` - Red background
  - `[success]` - Green background
  - `[queued]` - Yellow background
- **DAG Status**: 
  - Red border = Has failures
  - Blue border = Has running jobs
  - Green border = All success
- **[Paused]** badge for paused DAGs

---

#### Mobile Responsive View (Dashboard)

```
┌───────────────────────────┐
│ Airflow Health Dashboard  │
│ 🟢 Connected              │
│ [≡ Menu]                  │
└───────────────────────────┘

┌───────────────────────────┐
│ Time: [Last 24 Hours ▼]  │
│ ☑ Auto-refresh [Refresh] │
└───────────────────────────┘

┌───────────────────────────┐
│ Total Domains             │
│        10                 │
└───────────────────────────┘
┌───────────────────────────┐
│ Total DAGs                │
│        250                │
└───────────────────────────┘
┌───────────────────────────┐
│ Domains with Failures     │
│         3                 │
└───────────────────────────┘
┌───────────────────────────┐
│ Healthy Domains           │
│         7                 │
└───────────────────────────┘

┌───────────────────────────┐
│ Business Domains          │
├───────────────────────────┤
│ ┏━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Finance [5 Failed] ➤┃ │
│ ┃ DAGs: 45            ┃ │
│ ┃ Health: 78.3%       ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━┛ │
│                           │
│ ┏━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Marketing           ┃ │
│ ┃ [3 Failed]        ➤ ┃ │
│ ┃ DAGs: 32            ┃ │
│ ┃ Health: 91.0%       ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━┛ │
│                           │
│ ┌─────────────────────┐   │
│ │ Sales [Healthy]   ➤ │   │
│ │ DAGs: 22            │   │
│ │ Health: 100.0%      │   │
│ └─────────────────────┘   │
└───────────────────────────┘
```

---

### UI Component Breakdown

#### Color Palette

| Component | Color | Hex | Usage |
|-----------|-------|-----|-------|
| **Failures** | Red | #DC2626 | Background, text, borders for failed states |
| **Running** | Blue | #2563EB | Background, text, borders for running states |
| **Success** | Green | #16A34A | Background, text, borders for successful states |
| **Queued** | Yellow | #CA8A04 | Background, text, borders for queued states |
| **Paused** | Gray | #6B7280 | Background, text for paused DAGs |
| **Background** | Light Gray | #F9FAFB | Page background |
| **Cards** | White | #FFFFFF | Card backgrounds |
| **Text Primary** | Dark Gray | #111827 | Main text |
| **Text Secondary** | Medium Gray | #6B7280 | Supporting text |
| **Borders** | Light Gray | #E5E7EB | Default borders |

#### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| **Page Title** | System Default | 24px | Bold (700) |
| **Section Headers** | System Default | 18px | Semibold (600) |
| **Domain Names** | System Default | 18px | Semibold (600) |
| **DAG Names** | System Default | 16px | Semibold (600) |
| **Body Text** | System Default | 14px | Medium (500) |
| **Helper Text** | System Default | 12px | Normal (400) |
| **Metrics** | System Default | 32px | Bold (700) |

#### Spacing

- **Card Padding**: 24px (1.5rem)
- **Section Spacing**: 24px (1.5rem)
- **Element Spacing**: 16px (1rem)
- **Compact Spacing**: 8px (0.5rem)
- **Grid Gaps**: 16px (1rem)

#### Interactive States

| State | Visual Feedback |
|-------|----------------|
| **Hover** | Background lightens, cursor changes to pointer |
| **Active** | Slight scale down (0.98), shadow increases |
| **Focus** | Blue outline ring (2px) |
| **Disabled** | Opacity 50%, cursor not-allowed |
| **Loading** | Spinner animation, reduced opacity |

---

### User Interaction Flows

#### Flow 1: View Domain Health

```
User Action                    UI Response                    Backend Action
───────────────────────────────────────────────────────────────────────────────
1. Open dashboard          → Show loading spinner          → GET /api/v1/health
                            
2. Health check succeeds   → Render dashboard             → GET /api/v1/domains
                            
3. Data loaded             → Display domain cards         → (Data cached)
                             Sort: failures first
                             
4. Auto-refresh timer      → Subtle refresh indicator     → GET /api/v1/domains
   (every 2 minutes)         Update counts                  (Cache hit/miss)
```

#### Flow 2: Drill Down to DAG Details

```
User Action                    UI Response                    Backend Action
───────────────────────────────────────────────────────────────────────────────
1. Click "Finance" card    → Navigate to /domain/Finance  → GET /api/v1/domains/Finance
                            
2. Page loads              → Show loading spinner          → (Fetch domain data)
                            
3. Data loaded             → Display Finance summary      → (Data cached)
                             List all DAGs
                             Sort: failures first
                             
4. Click DAG card          → Expand card                   → GET /api/v1/domains/Finance/
                             Show loading                     dags/{dag_id}/runs
                             
5. Runs loaded             → Display run history          → (NOT cached - real-time)
                             Color-coded by state
                             
6. Click "View →"          → Open Airflow UI              → (External link)
   on run                    in new tab
```

#### Flow 3: Change Time Range

```
User Action                    UI Response                    Backend Action
───────────────────────────────────────────────────────────────────────────────
1. Select "Last 7 Days"    → Show loading overlay         → GET /api/v1/domains
   from dropdown                                              ?time_range=7d
                            
2. Data loaded             → Update all metrics           → (New cache key)
                             Recalculate health scores
                             Re-sort domains
                             
3. Domain counts change    → Animate number transitions   → (Visual only)
                             Update percentages
```

---

### Accessibility Features

| Feature | Implementation |
|---------|---------------|
| **Keyboard Navigation** | Tab through cards, Enter to expand |
| **Screen Reader Support** | ARIA labels on all interactive elements |
| **Color Contrast** | WCAG AA compliant (4.5:1 minimum) |
| **Focus Indicators** | Visible blue outline on focus |
| **Error Messages** | Descriptive text for screen readers |
| **Loading States** | Announced to screen readers |

---

### Responsive Breakpoints

| Breakpoint | Width | Layout Changes |
|------------|-------|---------------|
| **Mobile** | < 640px | Single column, stacked stats |
| **Tablet** | 640px - 1024px | 2 columns for stats, full-width cards |
| **Desktop** | > 1024px | 4 columns for stats, optimized spacing |
| **Large Desktop** | > 1280px | Max width 1280px, centered content |

### State Management

**Dashboard Component State**:
```javascript
const [timeRange, setTimeRange] = useState('24h');
const [dashboardData, setDashboardData] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);
const [autoRefresh, setAutoRefresh] = useState(true);
```

**DomainDetail Component State**:
```javascript
const [timeRange, setTimeRange] = useState('24h');
const [domainData, setDomainData] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);
const [expandedDag, setExpandedDag] = useState(null);
const [dagRuns, setDagRuns] = useState({});
```

### Key Features

#### 1. **Auto-refresh Mechanism**

```javascript
useEffect(() => {
    fetchDashboard();
    
    if (autoRefresh) {
        const interval = setInterval(fetchDashboard, 120000); // 2 minutes
        return () => clearInterval(interval);
    }
}, [timeRange, autoRefresh]);
```

#### 2. **Progressive Data Loading**

- **Level 1**: Dashboard loads all domain summaries
- **Level 2**: Click domain → Load DAG list
- **Level 3**: Expand DAG → Load run history

#### 3. **Visual Health Indicators**

**Color Coding**:
```javascript
const getHealthColor = (domain) => {
    if (domain.has_failures) return 'bg-red-50 border-red-200';
    if (domain.running_count > 0) return 'bg-blue-50 border-blue-200';
    return 'bg-green-50 border-green-200';
};
```

**State Badges**:
- Failed: Red badge with count
- Running: Blue badge with count
- Healthy: Green badge

#### 4. **API Client (`api.js`)**

**Features**:
- Axios instance with base URL configuration
- Request/response interceptors for logging
- Error handling and propagation
- Environment variable support

**API Methods**:
```javascript
export const api = {
    getHealth(),
    getDomains(timeRange),
    getDomainDetail(domainTag, timeRange),
    getDagRuns(domainTag, dagId, timeRange, limit),
    clearCache()
};
```

---

## Data Flow

### Dashboard Load Flow

```
1. User visits / → App.jsx renders
2. App.jsx: checkHealth() → GET /api/v1/health
3. Health check passes → Render Dashboard.jsx
4. Dashboard.jsx: fetchDashboard() → GET /api/v1/domains?time_range=24h

   Backend Flow:
   5. routes.py: get_domains() receives request
   6. Check cache: cache_service.get("dashboard:24h")
   7a. Cache HIT → Return cached data
   7b. Cache MISS:
       - airflow_client.get_all_dags()
       - Group DAGs by tags
       - For each domain:
         * Fetch DAG runs concurrently
         * Calculate health metrics
       - cache_service.set("dashboard:24h", result)
       - Return result
   
8. Dashboard.jsx: Receive data → setDashboardData()
9. Render domain cards with health indicators
```

### Domain Drill-Down Flow

```
1. User clicks domain card → navigate('/domain/:tag')
2. DomainDetail.jsx: fetchDomainDetail()
   → GET /api/v1/domains/{tag}?time_range=24h

   Backend Flow:
   3. routes.py: get_domain_detail() receives request
   4. Check cache: cache_service.get("domain:{tag}:24h")
   5a. Cache HIT → Return cached data
   5b. Cache MISS:
       - airflow_client.get_all_dags()
       - Filter DAGs by tag
       - For each DAG:
         * Fetch runs
         * Calculate metrics
       - Build DomainDetailResponse
       - Cache result
       - Return result

6. DomainDetail.jsx: Receive data → setDomainData()
7. Render DAG list with health metrics
```

### DAG Run Expansion Flow

```
1. User clicks DAG card → toggleDagExpansion(dagId)
2. Check if already loaded: dagRuns[dagId]?
3. If not loaded:
   fetchDagRuns(dagId)
   → GET /api/v1/domains/{tag}/dags/{dag_id}/runs?time_range=24h&limit=20

   Backend Flow:
   4. routes.py: get_dag_runs() receives request
   5. airflow_client.get_dag_runs(dag_id, time_range)
   6. Transform to DagRunSummary objects
   7. Return runs (NOT cached - real-time data)

8. DomainDetail.jsx: setDagRuns({...prev, [dagId]: runs})
9. Render run list with state badges
```

---

## API Design

### RESTful Principles

- **Resource-Oriented**: `/domains`, `/domains/{tag}`, `/dags/{id}`
- **Standard HTTP Methods**: GET for reads, POST for actions
- **Query Parameters**: For filtering (time_range, limit)
- **HTTP Status Codes**: 200 (OK), 404 (Not Found), 500 (Server Error)

### Response Format

All responses follow a consistent JSON structure:

**Success Response**:
```json
{
  "time_range": "24h",
  "domains": [...],
  "total_domains": 10,
  "total_dags": 250,
  "last_updated": "2025-10-29T10:30:00Z"
}
```

**Error Response**:
```json
{
  "detail": "Failed to fetch domain data: Connection timeout"
}
```

### API Versioning

- Version in URL: `/api/v1/`
- Allows future versions without breaking existing clients

### CORS Configuration

```python
CORSMiddleware(
    allow_origins=["http://localhost:3000"],  # Frontend origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Read-only + cache clear
    allow_headers=["*"]
)
```

---

## Caching Strategy

### Cache Levels

| Level | What is Cached | TTL | Cache Key Pattern |
|-------|---------------|-----|-------------------|
| Dashboard | All domain summaries | 120s | `dashboard:{time_range}` |
| Domain Detail | DAG list for domain | 120s | `domain:{tag}:{time_range}` |
| DAG Runs | NOT cached | N/A | Real-time data |

### Cache Key Design

**Pattern**: `{resource}:{identifier}:{time_range}`

**Examples**:
- `dashboard:24h` - Dashboard for last 24 hours
- `domain:Finance:7d` - Finance domain for last 7 days
- `domain:Marketing:30d` - Marketing domain for last 30 days

### Cache Invalidation

**Manual**:
- POST `/cache/clear` - Clears all cache entries

**Automatic**:
- TTL expiration (120 seconds default)
- In-memory cleanup when > 1000 entries

### Why This Strategy?

1. **Dashboard is cached**: Expensive operation (fetches all DAGs + runs)
2. **Domain detail is cached**: Moderate expense (one domain's DAGs + runs)
3. **DAG runs NOT cached**: User expects real-time run status

---

## Security Considerations

### Read-Only by Design

- **No Trigger Endpoints**: Cannot start DAGs
- **No Modification Endpoints**: Cannot pause/unpause DAGs
- **No Configuration Changes**: Cannot modify DAG settings
- **No Database Access**: Only uses Airflow REST API

### Authentication Flow

```
Frontend → Backend: No auth (trusted network)
Backend → Airflow: Basic Auth or Token Auth
```

**Airflow Authentication Options**:

1. **Basic Authentication**:
   ```env
   AIRFLOW_USERNAME=admin
   AIRFLOW_PASSWORD=secret
   ```

2. **Token Authentication**:
   ```env
   AIRFLOW_API_TOKEN=your_jwt_token
   ```

### Credential Management

- **Environment Variables**: Credentials stored in `.env`
- **Docker Secrets**: Can use Docker secrets in production
- **No Hardcoding**: Never committed to version control

### CORS Protection

- Whitelist frontend origins
- Prevent unauthorized cross-origin access
- Can add authentication middleware for production

### Future Enhancements

- SSO integration (OAuth, SAML)
- API key authentication for backend
- Rate limiting
- Request logging and audit trails

---

## Deployment Architecture

### Docker Compose Deployment

```
┌─────────────────────────────────────────┐
│         Docker Host                      │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  frontend (Port 3000:80)           │ │
│  │  - Nginx serving React build       │ │
│  │  - Env: VITE_API_URL               │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│  ┌────────────▼───────────────────────┐ │
│  │  backend (Port 8000:8000)          │ │
│  │  - FastAPI + Uvicorn               │ │
│  │  - Env: AIRFLOW_* credentials      │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│  ┌────────────▼───────────────────────┐ │
│  │  redis (Port 6379:6379)            │ │
│  │  - Cache storage                   │ │
│  │  - Volume: redis-data              │ │
│  └────────────────────────────────────┘ │
│                                          │
│  Network: airflow-health-net (bridge)   │
└─────────────────────────────────────────┘
                  │
                  │ HTTP API Calls
                  ▼
┌─────────────────────────────────────────┐
│     External Airflow Instance            │
│     (Port 8080)                          │
└─────────────────────────────────────────┘
```

### Container Details

#### Frontend Container
- **Base Image**: node:18 (build), nginx:alpine (runtime)
- **Build Process**: `npm run build` → Static files
- **Web Server**: Nginx
- **Configuration**: nginx.conf for SPA routing

#### Backend Container
- **Base Image**: python:3.9-slim
- **Dependencies**: requirements.txt
- **Server**: Uvicorn ASGI server
- **Workers**: Single worker (can scale)

#### Redis Container
- **Base Image**: redis:7-alpine
- **Persistence**: Append-only file (AOF)
- **Volume**: Named volume for data persistence
- **Health Check**: `redis-cli ping`

### Networking

- **Bridge Network**: All containers on `airflow-health-net`
- **Host Network Access**: Backend can reach Airflow via `host.docker.internal`
- **Port Mapping**: Exposes 3000 (frontend), 8000 (backend)

### Environment Variables

**Backend**:
```env
AIRFLOW_BASE_URL=http://host.docker.internal:8080
AIRFLOW_USERNAME=admin
AIRFLOW_PASSWORD=password
CACHE_TTL_SECONDS=120
REDIS_URL=redis://redis:6379/0
```

**Frontend**:
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_AIRFLOW_URL=http://localhost:8080
```

### Scaling Considerations

**Horizontal Scaling**:
- Multiple backend instances behind load balancer
- Redis for shared cache across instances
- Frontend can be scaled via CDN

**Vertical Scaling**:
- Increase uvicorn workers
- Allocate more memory to Redis
- Optimize React bundle size

---

## Code Organization

### Backend Structure

```
backend/
├── app/
│   ├── __init__.py              # Package initialization, version
│   ├── main.py                  # FastAPI app, CORS, startup events
│   ├── config.py                # Settings management (Pydantic)
│   ├── models.py                # Data models, enums, validation
│   ├── airflow_client.py        # Airflow API client
│   ├── cache.py                 # Cache service (Redis/Memory)
│   ├── service.py               # Business logic, health calculations
│   └── api/
│       ├── __init__.py
│       └── routes.py            # API endpoints
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   ├── test_airflow_client.py  # Client tests
│   └── test_service.py          # Service tests
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container definition
```

### Frontend Structure

```
frontend/
├── src/
│   ├── main.jsx                 # React entry point
│   ├── App.jsx                  # Root component, routing
│   ├── api.js                   # API client (axios)
│   ├── index.css                # Global styles (Tailwind)
│   └── components/
│       ├── Dashboard.jsx        # Main dashboard view
│       └── DomainDetail.jsx     # Domain drill-down view
├── public/                      # Static assets
├── index.html                   # HTML template
├── package.json                 # Node dependencies
├── vite.config.js              # Vite configuration
├── tailwind.config.js          # Tailwind configuration
├── nginx.conf                   # Nginx configuration for production
└── Dockerfile                   # Container definition
```

### Design Patterns Used

#### Backend Patterns

1. **Dependency Injection**: FastAPI's dependency system
2. **Repository Pattern**: AirflowAPIClient abstracts data access
3. **Service Layer**: HealthService contains business logic
4. **Singleton Pattern**: Global instances (client, cache, service)
5. **Factory Pattern**: Pydantic model validation
6. **Strategy Pattern**: Dual cache implementation (Redis/Memory)

#### Frontend Patterns

1. **Component Composition**: Reusable React components
2. **Container/Presentational**: Separation of logic and UI
3. **Custom Hooks**: Could add for shared logic
4. **Higher-Order Components**: Router wrapping
5. **State Management**: Local state with useState/useEffect

---

## Performance Optimizations

### Backend Optimizations

1. **Async/Await**: All I/O operations are async
2. **Concurrent API Calls**: `asyncio.gather()` for batch requests
3. **Caching**: Reduces Airflow API calls by 95%+
4. **Pagination**: Fetches DAGs in batches of 100
5. **Connection Pooling**: httpx reuses HTTP connections

### Frontend Optimizations

1. **Code Splitting**: React Router lazy loading (can add)
2. **Auto-refresh**: Configurable, can be disabled
3. **Progressive Loading**: Three-level hierarchy
4. **Debouncing**: Could add for time range changes
5. **Vite Build**: Fast builds, tree shaking

### Database Optimizations (Future)

- Materialized views for domain summaries
- Background job for cache warming
- WebSocket for real-time updates

---

## Monitoring and Observability

### Logging

**Backend Logging**:
```python
logger.info("GET /domains - time_range: 24h")
logger.error(f"Error fetching domains: {str(e)}")
logger.debug("Returning cached dashboard data")
```

**Frontend Logging**:
```javascript
console.log(`API Request: GET /domains`);
console.error('API Error:', error.response?.data);
```

### Health Checks

- **Endpoint**: GET `/api/v1/health`
- **Checks**: Backend status, Airflow connection, Cache status
- **Response**:
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "airflow_connection": "connected",
    "cache_status": "redis_healthy",
    "timestamp": "2025-10-29T10:30:00Z"
  }
  ```

### Metrics to Monitor

- **Response Times**: API endpoint latency
- **Cache Hit Rate**: Percentage of cached responses
- **Airflow API Calls**: Rate and latency
- **Error Rates**: 4xx and 5xx responses
- **Active Connections**: Concurrent users

---

## Future Architecture Enhancements

### Planned Improvements

1. **WebSocket Support**: Real-time DAG run updates
2. **GraphQL API**: More flexible data fetching
3. **Background Jobs**: Cache pre-warming
4. **Database Layer**: Store historical metrics
5. **Authentication**: SSO integration
6. **Rate Limiting**: Prevent abuse
7. **API Gateway**: Centralized routing and security
8. **Kubernetes**: Container orchestration
9. **Observability**: Prometheus + Grafana
10. **A/B Testing**: Feature flags

### Scalability Roadmap

**Phase 1 (Current)**: Single-instance deployment
**Phase 2**: Multi-instance with load balancer
**Phase 3**: Microservices architecture
**Phase 4**: Serverless functions (AWS Lambda)

---

## Conclusion

The Airflow Health Dashboard is built on a **modern, scalable architecture** that prioritizes:

- ✅ **Performance**: Intelligent caching and async operations
- ✅ **Security**: Read-only access and credential management
- ✅ **Maintainability**: Clean separation of concerns
- ✅ **Usability**: Progressive disclosure and visual indicators
- ✅ **Reliability**: Error handling and health checks

The architecture supports the core mission of providing **at-a-glance visibility** into Airflow DAG health for non-technical stakeholders while maintaining **minimal impact** on the Airflow infrastructure itself.

---

**Document Version**: 1.0.0  
**Last Updated**: October 29, 2025  
**Maintained By**: Data Platform Team
