# 📚 Documentation Index

Complete guide to the Airflow Health Dashboard documentation.

## 🎯 Start Here

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | Quick setup guide | **First time setup** |
| [README.md](README.md) | Project overview | Understanding the project |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | What was created | After initial setup |

## 📖 Setup & Configuration

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [SETUP.md](SETUP.md) | Detailed setup instructions | Manual installation |
| [config/.env.example](config/.env.example) | Environment configuration | Configuring the app |
| [frontend/.env.example](frontend/.env.example) | Frontend configuration | Frontend setup |

## 🚀 Deployment

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment | Deploying to production |
| [docker-compose.yml](docker-compose.yml) | Container orchestration | Docker setup |

## 🔌 API Reference

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [API.md](API.md) | Complete API documentation | Building integrations |
| http://localhost:8000/docs | Interactive API docs | Testing API calls |

## 🗺️ Project Planning

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [ROADMAP.md](ROADMAP.md) | Future enhancements | Planning upgrades |
| [LICENSE](LICENSE) | Legal terms | Understanding licensing |

## 📂 Code Documentation

### Backend (Python)
- `backend/app/main.py` - FastAPI application entry point
- `backend/app/config.py` - Configuration management
- `backend/app/models.py` - Data models and schemas
- `backend/app/airflow_client.py` - Airflow REST API client
- `backend/app/cache.py` - Caching service
- `backend/app/service.py` - Business logic layer
- `backend/app/api/routes.py` - API endpoint definitions

### Frontend (React)
- `frontend/src/App.jsx` - Main application component
- `frontend/src/api.js` - API client service
- `frontend/src/components/Dashboard.jsx` - Main dashboard view
- `frontend/src/components/DomainDetail.jsx` - Domain drill-down view

### Tests
- `backend/tests/test_airflow_client.py` - Airflow client tests
- `backend/tests/test_service.py` - Service layer tests
- `backend/tests/conftest.py` - Test configuration

## 🎓 Learning Path

### For First-Time Users
1. Read [GETTING_STARTED.md](GETTING_STARTED.md)
2. Configure environment variables
3. Run `./start.sh`
4. Browse [README.md](README.md) for feature overview

### For Developers
1. Review [README.md](README.md) for architecture
2. Read [SETUP.md](SETUP.md) for development setup
3. Check [API.md](API.md) for endpoint details
4. Study code in `backend/app/` and `frontend/src/`

### For DevOps/Operations
1. Review [DEPLOYMENT.md](DEPLOYMENT.md)
2. Check [docker-compose.yml](docker-compose.yml)
3. Understand [SETUP.md](SETUP.md) for troubleshooting
4. Plan using [ROADMAP.md](ROADMAP.md)

### For Project Managers
1. Read [README.md](README.md) for overview
2. Check [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
3. Review [ROADMAP.md](ROADMAP.md) for future plans

## 🔍 Quick Reference

### Common Tasks

**Start the application:**
```bash
./start.sh
# or
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f backend
```

**Stop services:**
```bash
docker-compose down
```

**Run tests:**
```bash
cd backend && pytest
```

**Check health:**
```bash
curl http://localhost:8000/api/v1/health
```

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Backend environment variables |
| `frontend/.env` | Frontend environment variables |
| `docker-compose.yml` | Container configuration |
| `backend/requirements.txt` | Python dependencies |
| `frontend/package.json` | Node.js dependencies |

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | User interface |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |
| Health Check | http://localhost:8000/api/v1/health | Service status |

## 🐛 Troubleshooting Guide

| Issue | See |
|-------|-----|
| Setup problems | [GETTING_STARTED.md](GETTING_STARTED.md) - Common Issues |
| Configuration | [SETUP.md](SETUP.md) - Configuration Details |
| Deployment issues | [DEPLOYMENT.md](DEPLOYMENT.md) - Troubleshooting |
| API errors | [API.md](API.md) - Error Responses |

## 📊 Project Statistics

- **Total Files**: 38+
- **Python Files**: 12
- **React Components**: 2
- **Documentation Files**: 7
- **Test Files**: 3
- **Configuration Files**: 8

## 🎯 Success Metrics

This project meets these requirements:

✅ **FR-2.1**: Airflow API integration with secure authentication  
✅ **FR-2.2**: Main dashboard with domain aggregation  
✅ **FR-2.3**: Drill-down to DAG level  
✅ **NFR-3.1**: API-only access (no DB queries)  
✅ **NFR-3.2**: Performance optimized (<5s load time)  
✅ **NFR-3.3**: Read-only security  
✅ **NFR-3.4**: User-friendly interface  

## 🔗 External Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## 📝 Document Maintenance

This documentation is organized as follows:

- **User-facing docs**: GETTING_STARTED, README
- **Technical docs**: SETUP, API, code comments
- **Operations docs**: DEPLOYMENT, docker-compose
- **Planning docs**: ROADMAP, PROJECT_SUMMARY

---

**Last Updated**: October 29, 2025  
**Project Version**: 1.0.0  
**Documentation Version**: 1.0.0

For questions or improvements to documentation, please update the relevant file and maintain this index.
