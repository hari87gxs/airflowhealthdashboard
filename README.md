# Airflow Health Dashboard

A comprehensive monitoring and analytics dashboard for Apache Airflow deployments, providing real-time insights into DAG health, failure patterns, and AI-powered recommendations for system optimization.

## 🚀 Features

### Core Monitoring
- **Real-time DAG Monitoring**: Track health and status of 294+ DAGs across multiple domains
- **Domain-based Organization**: Automated categorization across 8 business domains (Finance, Ecosystem, Marketing, etc.)
- **Comprehensive Health Metrics**: Success rates, failure counts, and performance trends
- **Background Caching**: 5-minute TTL caching system for optimal performance

### AI-Powered Analysis
- **Intelligent Failure Analysis**: Azure OpenAI GPT-4o integration for smart failure categorization
- **Pattern Recognition**: Automatic identification of failure patterns (Data Quality, Configuration, Infrastructure)
- **Actionable Recommendations**: Prioritized action items with specific affected DAGs
- **Root Cause Analysis**: Deep insights into failure causes and prevention strategies

### Slack Integration 🆕
- **Automated Reports**: Scheduled health reports at 10 AM & 7 PM UTC (configurable)
- **Rich Message Formatting**: Visual health bars, emojis, and Slack Block Kit
- **AI Insights in Slack**: GPT-4 analysis delivered directly to your team
- **Manual Triggers**: On-demand report generation via API
- **Critical Alerts**: Immediate notifications for health issues

### Advanced Capabilities
- **Interactive Dashboard**: Modern React-based UI with real-time updates and responsive design
- **Historical Trends**: Track performance trends and identify patterns over time
- **Detailed Logging**: Comprehensive failure logs with task-level error details
- **REST API**: Full REST API for integration with monitoring tools and automation systems
- **Robust Error Handling**: Comprehensive null-safety and defensive programming
- **AWS Deployment Ready**: Complete Terraform infrastructure as code for production deployment

## 🏗️ Architecture

The dashboard consists of five main components:

1. **Frontend**: React 18 + Vite application with Tailwind CSS for modern, responsive UI
2. **Backend**: FastAPI-based Python service with async processing and background tasks
3. **Scheduler**: Automated reporting service for scheduled Slack notifications
4. **AI Service**: Azure OpenAI integration for intelligent failure analysis and recommendations
5. **Airflow Integration**: Direct integration with Airflow REST API for real-time data access
6. **Redis Cache**: Distributed caching for performance optimization

### Key Technical Improvements
- ✅ **Null-Safety**: Comprehensive null pointer error prevention with defensive programming
- ✅ **Background Processing**: Async task management with lifespan event handling  
- ✅ **Caching System**: In-memory caching with automatic refresh for performance
- ✅ **Error Recovery**: Robust error handling with detailed logging and graceful degradation

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose (recommended)
- Node.js 18+ (for local development)
- Python 3.8+ with virtual environment support
- Access to Airflow REST API
- Azure OpenAI API key (optional, for AI features)

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/hari87gxs/airflowhealthdashboard.git
cd airflowhealthdashboard

# Set up environment variables
cp .env.example .env
# Edit .env with your Airflow URL and credentials

# Start the services
docker-compose up -d

# Access the dashboard
open http://localhost:3000
```

### Local Development Setup

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp config/.env.example .env
# Edit .env with your configuration

# Start the backend server
PYTHONPATH=/path/to/backend python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev

# Access the application at http://localhost:3000
```

## 📊 API Endpoints

### Core Endpoints

- `GET /api/v1/domains?time_range=24h` - Get DAG health metrics by domain
- `GET /api/v1/analysis/failures?time_range=24h` - Get comprehensive failure analysis with AI insights
- `GET /api/v1/domains/{domain}/dags?time_range=24h` - Get detailed DAG information for a specific domain

### Slack & Reporting Endpoints 🆕

- `POST /api/slack/test` - Test Slack webhook connection
- `POST /api/reports/send` - Manually trigger a health report to Slack
- `GET /api/reports/schedule` - Get current report schedule configuration

### Sample API Response

```json
{
  "llm_analysis": {
    "summary": "System analysis showing 94% success rate with focused issues in data quality and configuration",
    "categories": [
      {
        "name": "Data Quality Issues",
        "count": 6,
        "dag_ids": ["ingestion__lending", "dm__daily_extraction"],
        "description": "Failures caused by missing or invalid data during processing"
      }
    ],
    "action_items": [
      {
        "priority": "high",
        "title": "Investigate data quality in ingestion pipelines",
        "description": "Audit upstream data sources and implement validation checks"
      }
    ]
  },
  "total_failed_dags": 17,
  "total_analyzed_dags": 294
}
```

## 🔧 Configuration

### Environment Variables

#### Backend Configuration (.env)
```bash
# Airflow Connection
AIRFLOW_BASE_URL=https://your-airflow-instance.com
AIRFLOW_USERNAME=your_username
AIRFLOW_PASSWORD=your_password

# Azure OpenAI (optional)
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_TTL=120
REFRESH_INTERVAL=300

# Slack Integration (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_ENABLED=true
DASHBOARD_URL=http://localhost:3000

# Scheduled Reports (optional)
SCHEDULED_REPORTS_ENABLED=true
MORNING_REPORT_HOUR=10
MORNING_REPORT_MINUTE=0
EVENING_REPORT_HOUR=19
EVENING_REPORT_MINUTE=0
```

#### Frontend Configuration
The frontend automatically connects to the backend API at `http://localhost:8000`.

## 🛠️ Advanced Features

### AI-Powered Insights
- **Pattern Recognition**: Automatically identifies common failure patterns
- **Categorization**: Groups failures by type (Data Quality, Configuration, Infrastructure)
- **Recommendations**: Provides prioritized action items with specific DAG references
- **Trend Analysis**: Identifies recurring issues and suggests preventive measures

### Background Processing
- **Automatic Refresh**: Background tasks update analysis every 5 minutes
- **Performance Optimization**: Cached results provide instant dashboard loading
- **Graceful Degradation**: System continues operation even if AI service is unavailable

### Robust Error Handling
- **Null-Safety**: Comprehensive protection against data inconsistencies
- **Defensive Programming**: Handles missing or malformed Airflow API responses
- **Detailed Logging**: Full error tracebacks for debugging and monitoring

## 📈 Monitoring & Health Metrics

The dashboard provides comprehensive monitoring across multiple dimensions:

### Domain Health Scores
- **Finance Domain**: ERP, lending, investment workflows
- **Ecosystem Domain**: Partner integrations (Grab, Singtel)
- **Marketing Domain**: Campaign and email automation
- **Regulatory Reporting**: Compliance and audit workflows
- **Credit Risk**: Risk assessment and validation
- **AML**: Anti-money laundering processes

### Key Performance Indicators
- **Overall Success Rate**: System-wide success percentage
- **Domain Health Scores**: Per-domain health metrics
- **Failure Rate Trends**: Historical failure pattern analysis
- **Recovery Time**: Average time to resolve failures

## 🔍 Troubleshooting

### Common Issues

#### Frontend Not Loading
```bash
# Check if both servers are running
lsof -i :3000  # Frontend
lsof -i :8000  # Backend

# Restart frontend
cd frontend && npm run dev
```

#### Backend API Errors
```bash
# Check backend logs
docker-compose logs backend

# Verify Airflow connectivity
curl -u username:password https://your-airflow-instance.com/api/v1/health
```

#### Analysis Not Updating
- Verify Azure OpenAI credentials in .env
- Check background task logs in backend console
- Ensure Airflow API is accessible and responsive

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Apache Airflow team for the excellent workflow management platform
- Azure OpenAI for providing intelligent analysis capabilities
- React and FastAPI communities for robust frameworks

## 📚 Documentation

For detailed documentation, see:
- [Project Summary](PROJECT_SUMMARY.md)
- [Architecture Guide](ARCHITECTURE.md)
- [API Documentation](API.md)
- [Getting Started Guide](GETTING_STARTED.md)
- [AWS Deployment Guide](AWS_DEPLOYMENT.md) 🆕
- [Slack Integration Guide](SLACK_INTEGRATION.md) 🆕
- [Deployment Guide](DEPLOYMENT.md)

## 🚀 AWS Deployment

Deploy to AWS with ECS Fargate, Application Load Balancer, and ElastiCache Redis:

```bash
# 1. Configure Terraform variables
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 2. Run deployment script
cd ..
./scripts/deploy.sh
```

Estimated AWS costs: **$135-145/month**

See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) for detailed instructions.

## 📬 Slack Notifications

Set up automated Slack reports:

```bash
# 1. Create Slack Incoming Webhook
# Visit: https://api.slack.com/messaging/webhooks

# 2. Configure environment
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export SLACK_ENABLED=true

# 3. Test integration
curl -X POST http://localhost:8000/api/slack/test
```

See [SLACK_INTEGRATION.md](SLACK_INTEGRATION.md) for complete guide.
