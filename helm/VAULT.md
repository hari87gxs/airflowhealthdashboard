# HashiCorp Vault Integration

This Helm chart supports HashiCorp Vault for secure secret management as an alternative to Kubernetes secrets.

## Overview

When Vault is enabled, secrets are injected into pods using the Vault Agent Injector. The secrets are sourced from Vault and made available as environment variables via a shell script (`/vault/secrets/secrets`) that is sourced before the application starts.

## Prerequisites

1. **HashiCorp Vault** must be installed and configured in your Kubernetes cluster
2. **Vault Agent Injector** must be deployed
3. **IAM Role** configured for IRSA (IAM Roles for Service Accounts) with appropriate Vault access
4. **Vault Role** created for the application with appropriate policies

## Configuration

### 1. Enable Vault in Values

```yaml
backend:
  vault:
    enabled: true
    role: "airflow-health-dashboard-role"
    path: "data-dev/app/data-dev-de/platform-apps/airflow-health-dashboard"
```

### 2. Configure ServiceAccount with IAM Role

```yaml
serviceAccount:
  create: true
  name: airflow-health-dashboard
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::ACCOUNT_ID:role/RoleName"
```

### 3. Vault Annotations

The following annotations are automatically added to backend pods when Vault is enabled:

```yaml
podAnnotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "airflow-health-dashboard-role"
  vault.hashicorp.com/agent-cache-enable: "true"
  vault.hashicorp.com/agent-init-first: "true"
  vault.hashicorp.com/agent-pre-populate-only: "true"
```

## Required Secrets in Vault

Store the following secrets at the configured Vault path:

### For Staging/Development
Path: `data-dev/app/data-dev-de/platform-apps/airflow-health-dashboard`

```json
{
  "AIRFLOW_USERNAME": "admin",
  "AIRFLOW_PASSWORD": "your-airflow-password",
  "LLM_API_KEY": "your-llm-api-key",
  "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/XXX/YYY/ZZZ"
}
```

### For Production
Path: `data-prod/app/data-prod-de/platform-apps/airflow-health-dashboard`

```json
{
  "AIRFLOW_USERNAME": "admin",
  "AIRFLOW_PASSWORD": "your-airflow-password",
  "LLM_API_KEY": "your-llm-api-key",
  "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/XXX/YYY/ZZZ"
}
```

## Secret Injection Mechanism

The Vault Agent Injector creates a file at `/vault/secrets/secrets` containing:

```bash
export AIRFLOW_USERNAME='value-from-vault'
export AIRFLOW_PASSWORD='value-from-vault'
export LLM_API_KEY='value-from-vault'
export SLACK_WEBHOOK_URL='value-from-vault'
```

This file is sourced via the `BASH_ENV` environment variable set in the deployment:

```yaml
env:
  - name: BASH_ENV
    value: /vault/secrets/secrets
```

## Vault Setup

### 1. Create IAM Role for IRSA

```bash
# Create trust policy for OIDC provider
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/oidc.eks.REGION.amazonaws.com/id/CLUSTER_ID"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.REGION.amazonaws.com/id/CLUSTER_ID:sub": "system:serviceaccount:NAMESPACE:airflow-health-dashboard"
        }
      }
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
  --role-name AmazonEKSClusterAirflowHealthDashboardRole \
  --assume-role-policy-document file://trust-policy.json

# Attach policies as needed
```

### 2. Create Vault Role

```bash
vault write auth/kubernetes/role/airflow-health-dashboard-role \
  bound_service_account_names=airflow-health-dashboard \
  bound_service_account_namespaces=NAMESPACE \
  policies=airflow-health-dashboard-policy \
  ttl=24h
```

### 3. Create Vault Policy

```bash
vault policy write airflow-health-dashboard-policy - <<EOF
path "data-dev/app/data-dev-de/platform-apps/airflow-health-dashboard" {
  capabilities = ["read"]
}

path "data-prod/app/data-prod-de/platform-apps/airflow-health-dashboard" {
  capabilities = ["read"]
}
EOF
```

### 4. Store Secrets in Vault

```bash
# For staging
vault kv put data-dev/app/data-dev-de/platform-apps/airflow-health-dashboard \
  AIRFLOW_USERNAME="admin" \
  AIRFLOW_PASSWORD="your-password" \
  LLM_API_KEY="your-api-key" \
  SLACK_WEBHOOK_URL="https://hooks.slack.com/..."

# For production
vault kv put data-prod/app/data-prod-de/platform-apps/airflow-health-dashboard \
  AIRFLOW_USERNAME="admin" \
  AIRFLOW_PASSWORD="your-password" \
  LLM_API_KEY="your-api-key" \
  SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
```

## Deployment

### Staging
```bash
helm upgrade --install airflow-health-dashboard . \
  -f values.yaml \
  -f values.stg.yaml \
  --namespace airflow-health-dashboard \
  --create-namespace
```

### Production
```bash
helm upgrade --install airflow-health-dashboard . \
  -f values.yaml \
  -f values.prod.yaml \
  --namespace airflow-health-dashboard \
  --create-namespace
```

## Troubleshooting

### Check Vault Agent Status

```bash
# View vault agent logs
kubectl logs -n NAMESPACE POD_NAME -c vault-agent-init

# View application logs
kubectl logs -n NAMESPACE POD_NAME -c backend
```

### Verify Secrets Injection

```bash
# Exec into the pod
kubectl exec -n NAMESPACE POD_NAME -c backend -- cat /vault/secrets/secrets

# Check environment variables
kubectl exec -n NAMESPACE POD_NAME -c backend -- env | grep -E "AIRFLOW|LLM|SLACK"
```

### Common Issues

1. **Pod fails to start**: Check IAM role ARN and trust policy
2. **Vault agent init fails**: Verify Vault role and service account binding
3. **Secrets not available**: Ensure secrets exist at the correct Vault path
4. **Permission denied**: Check Vault policy allows read access to the path

## Migration from Kubernetes Secrets

To migrate from Kubernetes secrets to Vault:

1. Store all secrets in Vault using the commands above
2. Update `values.yaml` to enable Vault:
   ```yaml
   backend:
     vault:
       enabled: true
   secrets:
     create: false
   ```
3. Redeploy the chart
4. Verify secrets are injected correctly
5. Delete old Kubernetes secrets if no longer needed

## References

- [Vault Agent Injector](https://www.vaultproject.io/docs/platform/k8s/injector)
- [Vault Kubernetes Auth](https://www.vaultproject.io/docs/auth/kubernetes)
- [IRSA Documentation](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
