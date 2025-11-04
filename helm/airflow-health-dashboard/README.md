# Airflow Health Dashboard - Helm Chart

This Helm chart deploys the Airflow Health Dashboard on Kubernetes. The dashboard provides monitoring, health checks, and AI-powered failure analysis for Apache Airflow.

## Components

- **Backend**: FastAPI service providing REST API for Airflow monitoring
- **Frontend**: React-based web interface
- **Redis**: Caching layer (optional, can use external Redis)

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV provisioner support in the underlying infrastructure (for Redis persistence)
- An existing Apache Airflow deployment

## Installation

### Quick Start

1. **Add the repository** (if publishing to a Helm repository):
```bash
helm repo add airflow-health https://your-repo-url
helm repo update
```

2. **Install the chart**:
```bash
helm install my-airflow-health ./helm/airflow-health-dashboard
```

### Custom Installation

1. **Create a custom values file** (e.g., `my-values.yaml`):

```yaml
backend:
  airflow:
    baseUrl: "http://airflow-webserver.airflow.svc.cluster.local:8080"
    username: "admin"
    password: "your-password"
  
  llm:
    enabled: true
    provider: "azure_openai"
    model: "gpt-4o"
    azureOpenAI:
      endpoint: "https://your-resource.openai.azure.com/"
      deploymentName: "gpt-4o"
  
  slack:
    enabled: true

secrets:
  airflowPassword: "your-secure-password"
  llmApiKey: "your-llm-api-key"
  slackWebhookUrl: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: airflow-health.example.com
      paths:
        - path: /
          pathType: Prefix
          backend: frontend
        - path: /api
          pathType: Prefix
          backend: backend
  tls:
    - secretName: airflow-health-tls
      hosts:
        - airflow-health.example.com
```

2. **Install with custom values**:
```bash
helm install my-airflow-health ./helm/airflow-health-dashboard -f my-values.yaml
```

### Install in a specific namespace

```bash
kubectl create namespace airflow-health
helm install my-airflow-health ./helm/airflow-health-dashboard -n airflow-health
```

## Configuration

### Key Configuration Options

#### Airflow Connection

```yaml
backend:
  airflow:
    baseUrl: "http://airflow-webserver:8080"
    authMethod: "basic"  # or "token"
    username: "admin"
    password: "admin"
    # OR use API token
    apiToken: "your-api-token"
```

#### LLM Configuration (Azure OpenAI)

```yaml
backend:
  llm:
    enabled: true
    provider: "azure_openai"
    model: "gpt-4o"
    azureOpenAI:
      endpoint: "https://your-resource.openai.azure.com/"
      apiVersion: "2024-08-01-preview"
      deploymentName: "gpt-4o"

secrets:
  llmApiKey: "your-azure-openai-api-key"
```

#### LLM Configuration (OpenAI)

```yaml
backend:
  llm:
    enabled: true
    provider: "openai"
    model: "gpt-4o"

secrets:
  llmApiKey: "your-openai-api-key"
```

#### Slack Integration

```yaml
backend:
  slack:
    enabled: true
  scheduledReports:
    enabled: true
    morningReportHour: 10
    eveningReportHour: 19

secrets:
  slackWebhookUrl: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

#### Redis Configuration

**Internal Redis (default)**:
```yaml
redis:
  enabled: true
  persistence:
    enabled: true
    size: 8Gi
```

**External Redis**:
```yaml
redis:
  enabled: true
  external:
    enabled: true
    url: "redis://redis-master.redis.svc.cluster.local:6379"
```

**Disable Redis** (use in-memory cache):
```yaml
redis:
  enabled: false
```

#### Autoscaling

```yaml
backend:
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 80

frontend:
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 80
```

#### Ingress Configuration

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: airflow-health.example.com
      paths:
        - path: /
          pathType: Prefix
          backend: frontend
        - path: /api
          pathType: Prefix
          backend: backend
  tls:
    - secretName: airflow-health-tls
      hosts:
        - airflow-health.example.com
```

#### Resource Limits

```yaml
backend:
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi

frontend:
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 250m
      memory: 256Mi
```

### Full Configuration Reference

See [values.yaml](./values.yaml) for all available configuration options.

## Upgrading

```bash
helm upgrade my-airflow-health ./helm/airflow-health-dashboard -f my-values.yaml
```

## Uninstalling

```bash
helm uninstall my-airflow-health
```

To delete the namespace:
```bash
kubectl delete namespace airflow-health
```

## Accessing the Application

### Via Port Forward

**Frontend**:
```bash
kubectl port-forward svc/my-airflow-health-frontend 3000:80
# Access at http://localhost:3000
```

**Backend API**:
```bash
kubectl port-forward svc/my-airflow-health-backend 8000:8000
# Access at http://localhost:8000/api/v1
```

### Via Ingress

If ingress is enabled, access the application at the configured hostname:
```
https://airflow-health.example.com
```

## Security Best Practices

### 1. Use External Secret Management

Instead of storing secrets in `values.yaml`, use external secret management:

**Using Sealed Secrets**:
```bash
kubectl create secret generic airflow-health-secrets \
  --from-literal=airflow-password='your-password' \
  --from-literal=llm-api-key='your-api-key' \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml

kubectl apply -f sealed-secret.yaml
```

Then disable secret creation:
```yaml
secrets:
  create: false
```

**Using External Secrets Operator**:
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: airflow-health-secrets
spec:
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: airflow-health-secrets
  data:
    - secretKey: airflow-password
      remoteRef:
        key: airflow-health/airflow-password
    - secretKey: llm-api-key
      remoteRef:
        key: airflow-health/llm-api-key
```

### 2. Network Policies

Enable network policies to restrict pod-to-pod communication:
```yaml
networkPolicy:
  enabled: true
```

### 3. Pod Security

The chart includes secure defaults:
- Non-root user execution
- Read-only root filesystem
- Dropped capabilities
- No privilege escalation

### 4. TLS/HTTPS

Always use TLS in production:
```yaml
ingress:
  enabled: true
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  tls:
    - secretName: airflow-health-tls
      hosts:
        - airflow-health.example.com
```

## Monitoring

### Prometheus Integration

The chart is compatible with Prometheus ServiceMonitor:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: airflow-health-backend
spec:
  selector:
    matchLabels:
      app.kubernetes.io/component: backend
  endpoints:
  - port: http
    path: /metrics
```

### Logs

View logs for each component:
```bash
# Backend
kubectl logs -f -l app.kubernetes.io/component=backend

# Frontend
kubectl logs -f -l app.kubernetes.io/component=frontend

# Redis
kubectl logs -f -l app.kubernetes.io/component=redis
```

## Troubleshooting

### Check Pod Status
```bash
kubectl get pods -l app.kubernetes.io/name=airflow-health-dashboard
```

### Describe Pods
```bash
kubectl describe pod -l app.kubernetes.io/component=backend
```

### Check Configuration
```bash
kubectl get configmap my-airflow-health-config -o yaml
```

### Check Secrets
```bash
kubectl get secret my-airflow-health-secrets -o yaml
```

### Test Backend Connection
```bash
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://my-airflow-health-backend:8000/health
```

### Common Issues

**Backend can't connect to Airflow**:
- Verify `backend.airflow.baseUrl` is correct
- Check network policies allow egress to Airflow
- Verify credentials are correct

**LLM analysis not working**:
- Check `secrets.llmApiKey` is set correctly
- Verify the LLM provider and endpoint configuration
- Check backend logs for API errors

**Redis connection failed**:
- If using external Redis, verify the URL is correct
- Check Redis pod is running: `kubectl get pod -l app.kubernetes.io/component=redis`
- Verify network connectivity

## Development

### Building Docker Images

Build and push images before deploying:

```bash
# Backend
docker build -t your-registry/airflow-health-backend:1.0.0 ./backend
docker push your-registry/airflow-health-backend:1.0.0

# Frontend
docker build -t your-registry/airflow-health-frontend:1.0.0 ./frontend
docker push your-registry/airflow-health-frontend:1.0.0
```

Update `values.yaml`:
```yaml
global:
  imageRegistry: "your-registry"

backend:
  image:
    repository: airflow-health-backend
    tag: "1.0.0"

frontend:
  image:
    repository: airflow-health-frontend
    tag: "1.0.0"
```

### Testing the Chart

Lint the chart:
```bash
helm lint ./helm/airflow-health-dashboard
```

Template and review manifests:
```bash
helm template my-airflow-health ./helm/airflow-health-dashboard -f my-values.yaml > manifests.yaml
```

Dry run installation:
```bash
helm install my-airflow-health ./helm/airflow-health-dashboard --dry-run --debug
```

## Support

For issues, questions, or contributions, please visit:
https://github.com/hari87gxs/airflowhealthdashboard
