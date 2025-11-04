# Kubernetes Deployment Guide

This guide explains how to deploy the Airflow Health Dashboard to Kubernetes using Helm.

## Overview

The Airflow Health Dashboard is deployed as a multi-component application:

- **Backend**: FastAPI service providing the REST API
- **Frontend**: React-based web interface served by Nginx
- **Redis**: Caching layer for improved performance

## Quick Links

- [Quick Start Guide](./helm/QUICKSTART.md) - Get started in 5 minutes
- [Helm Chart README](./helm/airflow-health-dashboard/README.md) - Detailed configuration
- [Production Values](./helm/airflow-health-dashboard/values-production.yaml) - Production example
- [Development Values](./helm/airflow-health-dashboard/values-dev.yaml) - Local dev example

## Prerequisites

1. **Kubernetes Cluster** (1.19+)
   - Local: Minikube, kind, Docker Desktop, or Rancher Desktop
   - Cloud: EKS, AKS, GKE, or any managed Kubernetes

2. **Helm 3** - [Install Helm](https://helm.sh/docs/intro/install/)

3. **kubectl** - [Install kubectl](https://kubernetes.io/docs/tasks/tools/)

4. **Docker Images** - Backend and frontend images in a registry

## Installation Options

### Option 1: Quick Install (Development)

For quick testing with default values:

```bash
cd helm
./install-chart.sh my-release airflow-health
```

### Option 2: Custom Install (Recommended)

1. Copy the example values:
   ```bash
   cp helm/airflow-health-dashboard/values-example.yaml my-values.yaml
   ```

2. Edit `my-values.yaml` with your configuration

3. Install:
   ```bash
   cd helm
   ./install-chart.sh my-release airflow-health my-values.yaml
   ```

### Option 3: Production Install

For production deployments:

```bash
cd helm
./install-chart.sh airflow-health airflow-health values-production.yaml
```

## Configuration

### Minimal Configuration

At minimum, you need to configure:

1. **Container Images**:
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

2. **Airflow Connection**:
   ```yaml
   backend:
     airflow:
       baseUrl: "http://airflow-webserver:8080"
       username: "admin"
       password: "your-password"
   ```

3. **Secrets**:
   ```yaml
   secrets:
     airflowPassword: "your-password"
     llmApiKey: "your-llm-api-key"  # if using LLM features
   ```

### Advanced Configuration

See the [Helm Chart README](./helm/airflow-health-dashboard/README.md) for:
- External Redis configuration
- Ingress setup with TLS
- Autoscaling configuration
- Resource limits and requests
- Network policies
- Pod disruption budgets

## Deployment Architectures

### Development Setup

```
┌─────────────────────────────────────────┐
│         Kubernetes Cluster              │
│                                         │
│  ┌──────────┐    ┌──────────┐          │
│  │ Frontend │    │ Backend  │          │
│  │  (1 pod) │───▶│ (1 pod)  │          │
│  └──────────┘    └──────────┘          │
│                        │                │
│                   ┌────▼─────┐          │
│                   │  Redis   │          │
│                   │ (1 pod)  │          │
│                   └──────────┘          │
└─────────────────────────────────────────┘
         │
    Port Forward
         │
    ┌────▼─────┐
    │  Browser │
    └──────────┘
```

### Production Setup with Ingress

```
                    Internet
                       │
                  ┌────▼─────┐
                  │  Ingress │
                  │   (TLS)  │
                  └────┬─────┘
         ┌─────────────┴────────────┐
         │                          │
┌────────▼─────────┐    ┌───────────▼────────┐
│  Frontend Svc    │    │   Backend Svc      │
│                  │    │                    │
│  ┌────────────┐  │    │  ┌──────────────┐  │
│  │ Frontend   │  │    │  │  Backend     │  │
│  │ (3 pods)   │  │    │  │  (3 pods)    │  │
│  │ + HPA      │  │    │  │  + HPA       │  │
│  └────────────┘  │    │  └──────┬───────┘  │
└──────────────────┘    └─────────┼──────────┘
                                  │
                          ┌───────▼────────┐
                          │ External Redis │
                          │  (Managed)     │
                          └────────────────┘
```

## Building and Pushing Images

Before deploying, build and push your Docker images:

```bash
# Set your registry
export REGISTRY="your-registry.azurecr.io"
export VERSION="1.0.0"

# Build backend
docker build -t $REGISTRY/airflow-health-backend:$VERSION ./backend
docker push $REGISTRY/airflow-health-backend:$VERSION

# Build frontend  
docker build -t $REGISTRY/airflow-health-frontend:$VERSION ./frontend
docker push $REGISTRY/airflow-health-frontend:$VERSION
```

## Accessing the Application

### During Development (Port Forward)

```bash
# Frontend
kubectl port-forward -n airflow-health svc/airflow-health-frontend 3000:80

# Backend API
kubectl port-forward -n airflow-health svc/airflow-health-backend 8000:8000

# Redis (if needed)
kubectl port-forward -n airflow-health svc/airflow-health-redis 6379:6379
```

Then access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1
- API Docs: http://localhost:8000/docs

### In Production (Ingress)

Configure ingress in your values file:

```yaml
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: airflow-health.company.com
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
        - airflow-health.company.com
```

Access at: https://airflow-health.company.com

## Monitoring and Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n airflow-health
```

### View Logs

```bash
# Backend logs
kubectl logs -f -l app.kubernetes.io/component=backend -n airflow-health

# Frontend logs
kubectl logs -f -l app.kubernetes.io/component=frontend -n airflow-health

# Redis logs
kubectl logs -f -l app.kubernetes.io/component=redis -n airflow-health
```

### Describe Resources

```bash
kubectl describe deployment airflow-health-backend -n airflow-health
kubectl describe pod <pod-name> -n airflow-health
```

### Check Events

```bash
kubectl get events -n airflow-health --sort-by='.lastTimestamp'
```

### Test Connectivity

```bash
# Test backend health endpoint
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://airflow-health-backend:8000/health

# Test Redis connection
kubectl run -it --rm debug --image=redis:alpine --restart=Never -- \
  redis-cli -h airflow-health-redis ping
```

## Updating the Deployment

### Update Configuration

1. Edit your values file
2. Run the upgrade script:
   ```bash
   cd helm
   ./upgrade-chart.sh my-release airflow-health my-values.yaml
   ```

### Update Images

1. Build and push new images:
   ```bash
   docker build -t $REGISTRY/airflow-health-backend:1.1.0 ./backend
   docker push $REGISTRY/airflow-health-backend:1.1.0
   ```

2. Update image tags in values file:
   ```yaml
   backend:
     image:
       tag: "1.1.0"
   ```

3. Upgrade:
   ```bash
   cd helm
   ./upgrade-chart.sh my-release airflow-health my-values.yaml
   ```

## Security Best Practices

1. **Use External Secret Management**
   - Don't store secrets in values files
   - Use Sealed Secrets, External Secrets Operator, or cloud-native solutions

2. **Enable TLS**
   - Always use TLS/HTTPS in production
   - Use cert-manager for certificate management

3. **Network Policies**
   - Enable network policies to restrict traffic
   - Only allow necessary pod-to-pod communication

4. **Resource Limits**
   - Set appropriate resource limits
   - Enable pod disruption budgets for high availability

5. **RBAC**
   - Use service accounts with minimal permissions
   - Don't run pods as root

6. **Image Security**
   - Scan images for vulnerabilities
   - Use minimal base images
   - Keep images updated

## Production Checklist

Before deploying to production:

- [ ] Images built and pushed to production registry
- [ ] Secrets managed externally (not in values.yaml)
- [ ] TLS/HTTPS configured with valid certificates
- [ ] Resource limits and requests configured
- [ ] Autoscaling enabled and tested
- [ ] External Redis configured for high availability
- [ ] Network policies enabled
- [ ] Pod disruption budgets configured
- [ ] Monitoring and alerting set up
- [ ] Backup strategy for Redis data (if applicable)
- [ ] Tested failover scenarios
- [ ] Documentation updated with production details
- [ ] Runbook created for common operations

## Common Issues and Solutions

### Pods Not Starting

**Symptom**: Pods in `Pending` or `ImagePullBackOff` state

**Solutions**:
- Check image pull secrets are configured
- Verify image names and tags are correct
- Ensure sufficient cluster resources

### Backend Can't Connect to Airflow

**Symptom**: Backend logs show connection errors

**Solutions**:
- Verify Airflow URL is correct
- Check network policies allow egress
- Test connectivity from backend pod

### Redis Connection Failed

**Symptom**: Cache errors in backend logs

**Solutions**:
- Check Redis pod is running
- Verify Redis URL configuration
- Test Redis connectivity

### High Memory Usage

**Symptom**: Pods being OOMKilled

**Solutions**:
- Increase memory limits
- Enable autoscaling
- Review cache TTL settings

## Further Reading

- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Project Documentation](./README.md)
- [API Documentation](./API.md)
- [Architecture](./ARCHITECTURE.md)

## Support

For questions or issues:
- GitHub Issues: https://github.com/hari87gxs/airflowhealthdashboard/issues
- Documentation: See the docs in this repository
