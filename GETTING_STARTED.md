# 🚀 Getting Started - Airflow Health Dashboard

Welcome! This guide will help you get the Airflow Health Dashboard up and running in minutes.

## ⚡ Quick Start (5 Minutes)

### Step 1: Navigate to Project
```bash
cd /Users/harikrishnan.r/Downloads/airflow-health-dashboard
```

### Step 2: Configure Airflow Connection
```bash
# Copy the environment template
cp config/.env.example .env

# Edit with your Airflow details
nano .env
```

**Required settings in `.env`:**
```env
AIRFLOW_BASE_URL=http://your-airflow-url:8080
AIRFLOW_USERNAME=your_username
AIRFLOW_PASSWORD=your_password
```

### Step 3: Start the Dashboard
```bash
./start.sh
```

That's it! The dashboard will be available at:
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000/docs

## 🎯 What You'll See

### Main Dashboard
- List of all business domains (based on DAG tags)
- Health metrics for each domain:
  - Total DAGs
  - Success/Failed/Running counts
  - Health score percentage
- Color-coded status (red for failures, green for healthy)
- Sortable by health (failures first)

### Domain Detail View
Click any domain to see:
- All DAGs in that domain
- Recent run history for each DAG
- Direct links to Airflow UI
- Expandable run details

### Time Filtering
Switch between:
- Last 24 Hours (default)
- Last 7 Days
- Last 30 Days

## 📋 Prerequisites

### Required
- Docker & Docker Compose installed
- Access to Airflow instance (URL and credentials)
- Airflow REST API enabled

### System Requirements
- **RAM**: Minimum 2GB available
- **Disk**: 500MB for Docker images
- **Network**: Access to Airflow API endpoint

## 🔧 Configuration Options

### Basic Configuration (`.env`)

**Airflow Connection:**
```env
# Option 1: Basic Auth
AIRFLOW_BASE_URL=http://localhost:8080
AIRFLOW_USERNAME=admin
AIRFLOW_PASSWORD=admin

# Option 2: API Token (more secure)
AIRFLOW_BASE_URL=http://localhost:8080
AIRFLOW_API_TOKEN=your_api_token_here
```

**Caching:**
```env
# How long to cache data (in seconds)
CACHE_TTL_SECONDS=120

# How often to refresh in background (in seconds)
REFRESH_INTERVAL_SECONDS=300
```

**Optional Redis (for distributed caching):**
```env
REDIS_URL=redis://localhost:6379/0
```

### Frontend Configuration (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_AIRFLOW_URL=http://localhost:8080
```

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart a service
docker-compose restart backend

# Rebuild and restart
docker-compose up --build -d
```

## 🔍 Verification Steps

### 1. Check Backend Health
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "airflow_connection": "connected",
  "cache_status": "in_memory_0_entries",
  "timestamp": "2025-10-29T10:30:00Z"
}
```

### 2. Check Frontend
Open http://localhost:3000 in your browser. You should see:
- Header with "Airflow Health Dashboard"
- Connection status indicator (green = connected)
- List of business domains

### 3. Test Airflow Connection
```bash
curl http://localhost:8000/api/v1/domains
```

Should return a list of domains with health metrics.

## 🐛 Common Issues & Solutions

### Issue: "Cannot connect to Airflow"

**Solutions:**
1. Verify Airflow URL is accessible:
   ```bash
   curl http://your-airflow-url/api/v1/health
   ```
2. Check credentials are correct
3. Ensure Airflow REST API is enabled
4. Check network/firewall rules

### Issue: "No domains showing"

**Solutions:**
1. Verify DAGs in Airflow have tags configured
2. Check time range - try "Last 7 Days"
3. Look at backend logs:
   ```bash
   docker-compose logs backend
   ```

### Issue: "Port already in use"

**Solutions:**
1. Change ports in `docker-compose.yml`:
   ```yaml
   ports:
     - "3001:80"  # Frontend
     - "8001:8000"  # Backend
   ```
2. Or stop conflicting services

### Issue: "Slow performance"

**Solutions:**
1. Enable Redis for better caching:
   ```env
   REDIS_URL=redis://redis:6379/0
   ```
2. Increase cache TTL:
   ```env
   CACHE_TTL_SECONDS=300
   ```
3. Reduce number of DAG runs fetched

## 📚 Next Steps

### 1. Explore the Dashboard
- Click on different domains
- Try different time ranges
- Expand DAG details
- Click "View in Airflow" links

### 2. Customize Settings
- Adjust cache duration
- Modify refresh intervals
- Configure CORS for production

### 3. Production Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Kubernetes deployment
- SSL/TLS setup
- SSO integration
- Monitoring setup

### 4. Learn More
- [README.md](README.md) - Full project overview
- [API.md](API.md) - API documentation
- [ROADMAP.md](ROADMAP.md) - Future features

## 💡 Tips for Success

### Tag Your DAGs
Ensure DAGs in Airflow are properly tagged:
```python
# In your DAG file
dag = DAG(
    'my_dag',
    tags=['Finance', 'Daily'],  # Add domain tags
    ...
)
```

### Use Meaningful Tags
Choose tags that represent business domains:
- ✅ Good: "Finance", "Marketing", "DataScience"
- ❌ Avoid: "test", "misc", "temp"

### Set Appropriate Cache TTL
- **Development**: 60-120 seconds (fast updates)
- **Production**: 300-600 seconds (less API load)

### Monitor Airflow API Load
- Use the cache effectively
- Don't set refresh too aggressively
- Monitor Airflow webserver metrics

## 🎓 Understanding the Dashboard

### Health Score Calculation
```
Health Score = (Successful Runs / Total Runs) × 100%
```

### Color Coding
- 🔴 **Red**: Has failures (priority attention needed)
- 🔵 **Blue**: Has running jobs (in progress)
- 🟢 **Green**: All successful (healthy)

### Data Freshness
- Data is cached for performance
- Default: 2-minute cache
- Use "Refresh" button to force update
- Auto-refresh option available

## 🤝 Getting Help

1. **Documentation**: Check all `.md` files in project root
2. **Logs**: `docker-compose logs -f backend`
3. **API Docs**: http://localhost:8000/docs
4. **Health Check**: http://localhost:8000/api/v1/health

## ✅ Checklist

Before considering setup complete, verify:

- [ ] `.env` file configured with Airflow credentials
- [ ] Services started: `docker-compose ps` shows all running
- [ ] Backend health check passes
- [ ] Frontend loads at http://localhost:3000
- [ ] At least one domain appears in dashboard
- [ ] Can drill down into domain details
- [ ] Links to Airflow UI work correctly

---

**Congratulations!** 🎉 You now have a fully functional Airflow Health Dashboard!

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).

For questions or issues, check the troubleshooting section above or review the full documentation.
