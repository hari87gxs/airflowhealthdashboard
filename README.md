# Airflow Domain-Specific Health Dashboard

A read-only web dashboard that provides high-level health monitoring for Airflow DAGs grouped by business domains/systems.

## Overview

This dashboard aggregates the health status of 250+ Airflow DAGs by their domain tags (e.g., Finance, Marketing, Data-Science), providing at-a-glance visibility into system health without diving into individual DAG details.

## Key Features

- **System-Level Health Aggregation**: View Failed, Success, and Running counts by business domain
- **Time-Based Filtering**: Filter data by Last 24 Hours, Last 7 Days, etc.
- **Drill-Down Capabilities**: Click on a domain to see individual DAG statuses
- **Read-Only**: No ability to modify or trigger DAGs (security by design)
- **Performance-Optimized**: Caching layer prevents excessive API calls to Airflow

## Architecture

```
┌─────────────────┐
│   Frontend      │
│   (React)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│   Backend       │─────▶│  Airflow REST    │
│   (FastAPI)     │      │  API             │
│   + Cache       │◀─────│                  │
└─────────────────┘      └──────────────────┘
```

## Project Structure

```
airflow-health-dashboard/
├── backend/              # FastAPI backend application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py      # FastAPI app entry point
│   │   ├── api/         # API endpoints
│   │   ├── services/    # Business logic
│   │   ├── models/      # Data models
│   │   └── utils/       # Utilities and helpers
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # React frontend application
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── services/    # API client
│   │   └── App.js
│   ├── package.json
│   └── Dockerfile
├── config/              # Configuration files
│   └── .env.example
├── docker-compose.yml   # Multi-container setup
└── README.md
```

## Requirements

### Backend
- Python 3.9+
- FastAPI
- httpx (for Airflow API calls)
- Redis (for caching)

### Frontend
- Node.js 18+
- React 18
- Tailwind CSS

## Quick Start

### 1. Clone and Configure

```bash
cd /Users/harikrishnan.r/Downloads/airflow-health-dashboard
cp config/.env.example .env
# Edit .env with your Airflow credentials
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

The dashboard will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 3. Manual Setup (Development)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## Configuration

Create a `.env` file in the root directory:

```env
# Airflow Configuration
AIRFLOW_BASE_URL=http://your-airflow-instance:8080
AIRFLOW_USERNAME=your_username
AIRFLOW_PASSWORD=your_password
# Or use API token
AIRFLOW_API_TOKEN=your_api_token

# Cache Configuration
CACHE_TTL_SECONDS=120
REFRESH_INTERVAL_SECONDS=300

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
```

## Security Notes

- **Read-Only Access**: The dashboard only makes GET requests to the Airflow API
- **Credential Management**: Store API credentials in environment variables or secrets manager
- **Network Access**: Deploy behind company firewall or SSO
- **No Direct DB Access**: Uses only Airflow REST API (no direct metastore queries)

## API Endpoints

### Backend API

- `GET /api/v1/health` - Health check
- `GET /api/v1/domains` - List all domain tags with aggregated health
- `GET /api/v1/domains/{tag}` - Get DAG details for a specific domain
- `GET /api/v1/domains/{tag}/dags/{dag_id}/runs` - Get runs for a specific DAG

### Query Parameters

- `time_range`: `24h`, `7d`, `30d` (default: `24h`)

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Style

```bash
# Backend
black app/
flake8 app/

# Frontend
npm run lint
```

## Success Metrics

- **MTTD**: Reduction in time to detect system-wide failures
- **Load Time**: Main dashboard loads in < 5 seconds
- **Stakeholder Adoption**: Non-technical users can identify issues within 30 seconds
- **System Stability**: No negative impact on Airflow performance over 30 days

## Roadmap

- [ ] Basic dashboard with domain aggregation (v1.0)
- [ ] Drill-down to DAG level (v1.0)
- [ ] Time range filtering (v1.0)
- [ ] Enhanced caching strategy (v1.1)
- [ ] SSO integration (v1.2)
- [ ] Custom domain grouping (v2.0)

## License

Internal use only - [Your Company Name]

## Support

For issues or questions, contact the Data Platform team.
