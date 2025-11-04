# Helm Charts for Airflow Health Dashboard

This directory contains the Helm chart for deploying the Airflow Health Dashboard on Kubernetes.

## Contents

- **airflow-health-dashboard/** - The Helm chart
- **QUICKSTART.md** - Quick deployment guide

## Quick Start

1. **Install the chart with default values**:
   ```bash
   helm install my-release ./airflow-health-dashboard
   ```

2. **Install with custom values**:
   ```bash
   helm install my-release ./airflow-health-dashboard -f my-values.yaml
   ```

3. **Access the application**:
   ```bash
   kubectl port-forward svc/my-release-frontend 3000:80
   ```
   Then visit http://localhost:3000

## Documentation

- [Quick Start Guide](./QUICKSTART.md) - Step-by-step deployment instructions
- [Chart README](./airflow-health-dashboard/README.md) - Detailed configuration and usage
- [Production Values](./airflow-health-dashboard/values-production.yaml) - Production-ready configuration example
- [Development Values](./airflow-health-dashboard/values-dev.yaml) - Local development configuration

## Chart Structure

```
airflow-health-dashboard/
├── Chart.yaml                          # Chart metadata
├── values.yaml                         # Default configuration values
├── values-production.yaml              # Production example
├── values-dev.yaml                     # Development example
├── README.md                           # Detailed documentation
├── .helmignore                         # Files to ignore when packaging
└── templates/
    ├── _helpers.tpl                    # Template helpers
    ├── NOTES.txt                       # Post-install notes
    ├── configmap.yaml                  # Configuration
    ├── secret.yaml                     # Secrets
    ├── serviceaccount.yaml             # Service account
    ├── backend-deployment.yaml         # Backend deployment
    ├── backend-service.yaml            # Backend service
    ├── backend-hpa.yaml                # Backend autoscaling
    ├── frontend-deployment.yaml        # Frontend deployment
    ├── frontend-service.yaml           # Frontend service
    ├── frontend-hpa.yaml               # Frontend autoscaling
    ├── redis-statefulset.yaml          # Redis StatefulSet
    ├── redis-service.yaml              # Redis service
    ├── ingress.yaml                    # Ingress configuration
    ├── networkpolicy.yaml              # Network policies
    └── poddisruptionbudget.yaml        # Pod disruption budgets
```

## Common Commands

### Install
```bash
helm install airflow-health ./airflow-health-dashboard
```

### Upgrade
```bash
helm upgrade airflow-health ./airflow-health-dashboard
```

### Uninstall
```bash
helm uninstall airflow-health
```

### Validate
```bash
helm lint ./airflow-health-dashboard
helm template airflow-health ./airflow-health-dashboard --debug
```

### Package
```bash
helm package ./airflow-health-dashboard
```

## Key Features

- **High Availability**: Supports multiple replicas with autoscaling
- **Security**: Pod security contexts, network policies, secret management
- **Flexibility**: External or internal Redis, multiple LLM providers
- **Production Ready**: Resource limits, health checks, disruption budgets
- **Observability**: Structured logging, health endpoints

## Requirements

- Kubernetes 1.19+
- Helm 3.2.0+
- Persistent Volume support (for Redis persistence)

## Support

For issues and questions:
- GitHub: https://github.com/hari87gxs/airflowhealthdashboard
- Documentation: See README files in this directory
