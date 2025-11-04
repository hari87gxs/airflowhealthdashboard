# Quick Deployment Guide

This guide will help you deploy the Airflow Health Dashboard to Kubernetes using Helm.

## Prerequisites

1. **Kubernetes cluster** - Running Kubernetes 1.19+
2. **Helm 3** - Install from https://helm.sh/docs/intro/install/
3. **kubectl** - Configured to access your cluster
4. **Docker images** - Backend and frontend images built and pushed to a registry

## Step 1: Build and Push Docker Images

```bash
# Navigate to project root
cd /path/to/airflowhealthdashboard

# Build backend image
docker build -t your-registry/airflow-health-backend:1.0.0 ./backend
docker push your-registry/airflow-health-backend:1.0.0

# Build frontend image
docker build -t your-registry/airflow-health-frontend:1.0.0 ./frontend
docker push your-registry/airflow-health-frontend:1.0.0
```

## Step 2: Create a Namespace

```bash
kubectl create namespace airflow-health
```

## Step 3: Create Secrets (Recommended)

Instead of putting secrets in values.yaml, create them separately:

```bash
kubectl create secret generic airflow-health-secrets \
  --namespace airflow-health \
  --from-literal=airflow-username='admin' \
  --from-literal=airflow-password='your-secure-password' \
  --from-literal=llm-api-key='your-llm-api-key' \
  --from-literal=slack-webhook-url='https://hooks.slack.com/services/YOUR/WEBHOOK'
```

## Step 4: Create Custom Values File

Create a file named `my-values.yaml`:

```yaml
global:
  imageRegistry: "your-registry"  # e.g., "mycompany.azurecr.io"

backend:
  image:
    repository: airflow-health-backend
    tag: "1.0.0"
  
  airflow:
    baseUrl: "http://airflow-webserver.airflow.svc.cluster.local:8080"
    authMethod: "basic"
  
  llm:
    enabled: true
    provider: "azure_openai"
    model: "gpt-4o"
    azureOpenAI:
      endpoint: "https://your-resource.openai.azure.com/"
      deploymentName: "gpt-4o"
  
  slack:
    enabled: true
  
  scheduledReports:
    enabled: true
    dashboardUrl: "https://airflow-health.example.com"

frontend:
  image:
    repository: airflow-health-frontend
    tag: "1.0.0"
  
  apiUrl: "http://airflow-health-backend:8000/api/v1"
  airflowUrl: "http://airflow-webserver.airflow.svc.cluster.local:8080"

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

secrets:
  create: false  # We created secrets manually
```

## Step 5: Install the Chart

```bash
helm install airflow-health \
  ./helm/airflow-health-dashboard \
  --namespace airflow-health \
  --values my-values.yaml
```

## Step 6: Verify Installation

```bash
# Check pods
kubectl get pods -n airflow-health

# Check services
kubectl get svc -n airflow-health

# Check ingress
kubectl get ingress -n airflow-health

# View logs
kubectl logs -f -l app.kubernetes.io/component=backend -n airflow-health
```

## Step 7: Access the Application

### Option A: Via Ingress (Production)

If you configured ingress, access via the hostname:
```
https://airflow-health.example.com
```

### Option B: Via Port Forward (Development)

```bash
# Frontend
kubectl port-forward -n airflow-health svc/airflow-health-frontend 3000:80

# Backend
kubectl port-forward -n airflow-health svc/airflow-health-backend 8000:8000
```

Then access:
- Frontend: http://localhost:3000
- API: http://localhost:8000/api/v1

## Common Configurations

### Using External Redis

```yaml
redis:
  enabled: true
  external:
    enabled: true
    url: "redis://redis-master.redis.svc.cluster.local:6379"
```

### Using OpenAI Instead of Azure OpenAI

```yaml
backend:
  llm:
    enabled: true
    provider: "openai"
    model: "gpt-4o"
```

### Enabling Autoscaling

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

## Updating the Deployment

After making changes to your values file:

```bash
helm upgrade airflow-health \
  ./helm/airflow-health-dashboard \
  --namespace airflow-health \
  --values my-values.yaml
```

## Uninstalling

```bash
helm uninstall airflow-health --namespace airflow-health
kubectl delete namespace airflow-health
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod -n airflow-health <pod-name>

# Check events
kubectl get events -n airflow-health --sort-by='.lastTimestamp'
```

### Backend Can't Connect to Airflow

1. Verify Airflow is running: `kubectl get pods -n airflow`
2. Test connectivity from backend pod:
```bash
kubectl exec -it -n airflow-health <backend-pod> -- curl http://airflow-webserver.airflow.svc.cluster.local:8080/health
```

### Image Pull Errors

If using a private registry, create an image pull secret:

```bash
kubectl create secret docker-registry acr-secret \
  --namespace airflow-health \
  --docker-server=your-registry.azurecr.io \
  --docker-username=<username> \
  --docker-password=<password>
```

Then add to values:
```yaml
global:
  imagePullSecrets:
    - name: acr-secret
```

## Production Checklist

- [ ] Use external Redis for high availability
- [ ] Enable autoscaling
- [ ] Configure resource limits appropriately
- [ ] Enable ingress with TLS
- [ ] Use external secret management (Sealed Secrets, External Secrets Operator)
- [ ] Enable network policies
- [ ] Configure pod disruption budgets
- [ ] Set up monitoring and alerting
- [ ] Configure backup for Redis (if using internal)
- [ ] Review and adjust CORS settings
- [ ] Test failover scenarios

## Next Steps

- Review the full [README](./README.md) for detailed configuration options
- Check the [values-production.yaml](./values-production.yaml) for production settings
- Set up monitoring with Prometheus/Grafana
- Configure log aggregation (ELK, Loki, etc.)
