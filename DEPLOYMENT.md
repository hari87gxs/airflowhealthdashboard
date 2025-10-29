# Production Deployment Guide

## Architecture Overview

The Airflow Health Dashboard is designed to be deployed as a standalone read-only monitoring tool that connects to your existing Airflow infrastructure via the REST API.

## Deployment Options

### Option 1: Docker Compose (Recommended for Small/Medium Scale)

1. **Prepare Environment**
   ```bash
   # Create production directory
   mkdir -p /opt/airflow-health-dashboard
   cd /opt/airflow-health-dashboard
   
   # Copy files
   # ... copy your built application files
   
   # Create production .env
   cp config/.env.example .env
   nano .env  # Configure with production values
   ```

2. **Production Environment Variables**
   ```env
   AIRFLOW_BASE_URL=https://airflow.company.com
   AIRFLOW_API_TOKEN=your_secure_api_token
   
   REDIS_URL=redis://redis:6379/0
   CACHE_TTL_SECONDS=120
   REFRESH_INTERVAL_SECONDS=300
   
   BACKEND_HOST=0.0.0.0
   BACKEND_PORT=8000
   
   CORS_ORIGINS=["https://health-dashboard.company.com"]
   LOG_LEVEL=WARNING
   ```

3. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

4. **Set up Reverse Proxy (Nginx/Traefik)**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name health-dashboard.company.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Option 2: Kubernetes Deployment

1. **Create Kubernetes Manifests**

   **backend-deployment.yaml**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: airflow-health-backend
   spec:
     replicas: 2
     selector:
       matchLabels:
         app: airflow-health-backend
     template:
       metadata:
         labels:
           app: airflow-health-backend
       spec:
         containers:
         - name: backend
           image: your-registry/airflow-health-backend:latest
           ports:
           - containerPort: 8000
           env:
           - name: AIRFLOW_BASE_URL
             valueFrom:
               secretKeyRef:
                 name: airflow-health-secrets
                 key: airflow-url
           - name: AIRFLOW_API_TOKEN
             valueFrom:
               secretKeyRef:
                 name: airflow-health-secrets
                 key: airflow-token
           - name: REDIS_URL
             value: redis://redis-service:6379/0
           resources:
             requests:
               memory: "256Mi"
               cpu: "250m"
             limits:
               memory: "512Mi"
               cpu: "500m"
           livenessProbe:
             httpGet:
               path: /api/v1/health
               port: 8000
             initialDelaySeconds: 30
             periodSeconds: 10
   ```

   **frontend-deployment.yaml**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: airflow-health-frontend
   spec:
     replicas: 2
     selector:
       matchLabels:
         app: airflow-health-frontend
     template:
       metadata:
         labels:
           app: airflow-health-frontend
       spec:
         containers:
         - name: frontend
           image: your-registry/airflow-health-frontend:latest
           ports:
           - containerPort: 80
           resources:
             requests:
               memory: "128Mi"
               cpu: "100m"
             limits:
               memory: "256Mi"
               cpu: "200m"
   ```

2. **Create Services and Ingress**
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: backend-service
   spec:
     selector:
       app: airflow-health-backend
     ports:
     - port: 8000
       targetPort: 8000
   ---
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: airflow-health-ingress
     annotations:
       cert-manager.io/cluster-issuer: letsencrypt-prod
   spec:
     tls:
     - hosts:
       - health-dashboard.company.com
       secretName: health-dashboard-tls
     rules:
     - host: health-dashboard.company.com
       http:
         paths:
         - path: /api
           pathType: Prefix
           backend:
             service:
               name: backend-service
               port:
                 number: 8000
         - path: /
           pathType: Prefix
           backend:
             service:
               name: frontend-service
               port:
                 number: 80
   ```

## Security Considerations

### 1. Authentication & Authorization

**Option A: Internal Network Only**
- Deploy behind company firewall
- Restrict access via network policies
- No public internet access

**Option B: SSO Integration**
- Use OAuth2/OIDC proxy (e.g., oauth2-proxy)
- Integrate with company SSO (Okta, Azure AD, Google Workspace)
- Example with oauth2-proxy:
  ```yaml
  # Add to kubernetes deployment
  - name: oauth2-proxy
    image: quay.io/oauth2-proxy/oauth2-proxy:latest
    args:
    - --provider=oidc
    - --client-id=your-client-id
    - --client-secret=your-client-secret
    - --upstream=http://localhost:3000
    - --cookie-secret=random-secret
  ```

### 2. API Credentials Management

**Use Secrets Manager**
```bash
# AWS Secrets Manager example
aws secretsmanager create-secret \
    --name airflow-health/api-token \
    --secret-string "your-airflow-api-token"
```

**Kubernetes Secrets**
```bash
kubectl create secret generic airflow-health-secrets \
    --from-literal=airflow-url=https://airflow.company.com \
    --from-literal=airflow-token=your-secure-token
```

### 3. Network Security

- Enable HTTPS/TLS for all traffic
- Use network policies to restrict pod communication
- Configure CORS properly (only allow your frontend domain)
- Rate limiting on API endpoints

## Monitoring & Observability

### 1. Application Metrics

- Backend exposes health endpoint: `/api/v1/health`
- Monitor cache hit rates
- Track API response times to Airflow

### 2. Logging

**Configure structured logging:**
```env
LOG_LEVEL=WARNING
LOG_FORMAT=json
```

**Aggregate logs:**
- Ship to ELK stack, Splunk, or CloudWatch
- Monitor for API errors
- Alert on Airflow connectivity issues

### 3. Alerting

Set up alerts for:
- Backend health check failures
- Airflow API connection errors
- High cache miss rates
- Memory/CPU threshold breaches

## Scaling Considerations

### Horizontal Scaling

**Backend:**
- Stateless, can scale horizontally
- Use Redis for distributed caching
- Load balancer distributes requests

**Frontend:**
- Static assets, highly cacheable
- CDN for global distribution
- Multiple replicas behind load balancer

### Performance Optimization

1. **Caching Strategy**
   - Increase CACHE_TTL for less frequent updates
   - Use Redis for persistent cache across restarts
   - Consider CDN for frontend assets

2. **API Optimization**
   - Batch requests to Airflow API
   - Implement request queuing
   - Rate limit frontend requests

3. **Database (if extending)**
   - Store historical data in separate database
   - Use time-series database for trends

## Backup & Disaster Recovery

1. **Configuration Backup**
   ```bash
   # Backup environment config
   tar -czf airflow-health-config-$(date +%Y%m%d).tar.gz .env config/
   ```

2. **Redis Persistence**
   - Enable AOF (Append-Only File) in Redis
   - Regular snapshots to persistent storage

3. **Recovery Plan**
   - Document Airflow API credentials location
   - Maintain deployment runbooks
   - Test recovery procedures regularly

## Maintenance

### Updates

1. **Backend Updates**
   ```bash
   docker-compose pull backend
   docker-compose up -d backend
   ```

2. **Frontend Updates**
   ```bash
   docker-compose pull frontend
   docker-compose up -d frontend
   ```

### Health Checks

Schedule regular checks:
```bash
# Cron job example
*/5 * * * * curl -f http://localhost:8000/api/v1/health || /path/to/alert-script.sh
```

## Cost Optimization

1. **Resource Sizing**
   - Backend: 256-512 MB RAM, 0.25-0.5 CPU
   - Frontend: 128-256 MB RAM, 0.1-0.2 CPU
   - Redis: 512 MB RAM

2. **Caching**
   - Reduces load on Airflow API
   - Lower API request costs
   - Faster response times

## Compliance

- **Data Privacy**: No DAG execution data stored permanently
- **Audit Logging**: Track all API access
- **Read-Only**: No modification capabilities
- **Data Retention**: Configure cache TTL per compliance requirements
