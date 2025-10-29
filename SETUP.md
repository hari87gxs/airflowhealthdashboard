# Development Setup Guide

## Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (optional)
- Access to an Airflow instance with REST API enabled

## Quick Start with Docker Compose

1. **Clone and Configure**
   ```bash
   cd /Users/harikrishnan.r/Downloads/airflow-health-dashboard
   
   # Copy environment template
   cp config/.env.example .env
   cp frontend/.env.example frontend/.env
   
   # Edit .env with your Airflow credentials
   nano .env
   ```

2. **Start Services**
   ```bash
   docker-compose up --build
   ```

3. **Access the Dashboard**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Manual Development Setup

### Backend Setup

1. **Create Virtual Environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp ../config/.env.example ../.env
   # Edit .env with your Airflow credentials
   ```

4. **Run Backend**
   ```bash
   # From the backend directory
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env if needed
   ```

3. **Run Frontend**
   ```bash
   npm run dev
   ```

## Testing the Setup

1. **Check Backend Health**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

2. **Test Airflow Connection**
   ```bash
   curl http://localhost:8000/api/v1/domains
   ```

3. **Access Frontend**
   Open http://localhost:3000 in your browser

## Configuration Details

### Required Environment Variables

**Backend (.env in root):**
- `AIRFLOW_BASE_URL` - Your Airflow webserver URL
- `AIRFLOW_USERNAME` / `AIRFLOW_PASSWORD` - Basic auth credentials
- OR `AIRFLOW_API_TOKEN` - API token (alternative to username/password)

**Frontend (frontend/.env):**
- `VITE_API_URL` - Backend API URL (default: http://localhost:8000/api/v1)
- `VITE_AIRFLOW_URL` - Airflow UI URL for deep links

### Optional Configuration

- `REDIS_URL` - For distributed caching (default: in-memory cache)
- `CACHE_TTL_SECONDS` - Cache lifetime (default: 120)
- `REFRESH_INTERVAL_SECONDS` - Background refresh (default: 300)
- `LOG_LEVEL` - Logging level (default: INFO)

## Troubleshooting

### Backend won't connect to Airflow

1. Check Airflow URL is accessible:
   ```bash
   curl http://your-airflow-url/api/v1/health
   ```

2. Verify credentials are correct

3. Check CORS settings if running Airflow with authentication

### Frontend can't reach backend

1. Verify backend is running: `curl http://localhost:8000/api/v1/health`
2. Check CORS_ORIGINS in backend .env includes frontend URL
3. Check browser console for CORS errors

### No domains showing up

1. Verify DAGs in Airflow have tags configured
2. Check API response: `curl http://localhost:8000/api/v1/domains`
3. Look at backend logs for errors

## Running Tests

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Code Formatting

### Backend
```bash
cd backend
black app/
flake8 app/
```

### Frontend
```bash
cd frontend
npm run lint
```

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment guidelines.

## Development Tips

1. **Enable Auto-Refresh**: The dashboard has an auto-refresh toggle in the UI
2. **Cache Management**: Use the "Refresh" button to force a cache clear
3. **API Documentation**: Visit http://localhost:8000/docs for interactive API docs
4. **Hot Reload**: Both backend and frontend support hot reloading during development
