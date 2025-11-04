# Airflow Health Dashboard - Vault Integration Changes

## Summary
Modified the airflow-health-dashboard Helm chart to support HashiCorp Vault for secret management, similar to the data-catalog implementation.

## Files Modified

### 1. `templates/backend-deployment.yaml`
**Changes:**
- Removed `checksum/secret` annotation (no longer needed since secrets come from Vault)
- Added conditional logic for Vault vs Kubernetes secrets:
  - When `backend.vault.enabled: true`, sets `BASH_ENV=/vault/secrets/secrets` to source secrets from Vault
  - When `backend.vault.enabled: false`, falls back to Kubernetes secrets (maintains backward compatibility)
- Secrets are now sourced from Vault-injected shell script instead of Kubernetes Secret references

### 2. `values.yaml`
**Changes:**
- Added `backend.vault` configuration section:
  ```yaml
  vault:
    enabled: false  # Default to disabled for backward compatibility
    role: "airflow-health-dashboard-role"
    path: "data-dev/app/data-dev-de/platform-apps/airflow-health-dashboard"
  ```

### 3. `values.stg.yaml`
**Changes:**
- Added ServiceAccount with IAM role annotation for IRSA
- Enabled Vault integration with `backend.vault.enabled: true`
- Added comprehensive Vault agent annotations in `backend.podAnnotations`:
  - `vault.hashicorp.com/agent-inject: "true"`
  - `vault.hashicorp.com/role: "airflow-health-dashboard-role"`
  - Secret injection template that creates shell exports for:
    - `AIRFLOW_USERNAME`
    - `AIRFLOW_PASSWORD`
    - `LLM_API_KEY`
    - `SLACK_WEBHOOK_URL` (conditional)
- Disabled Kubernetes secrets with `secrets.create: false`

### 4. `values.prod.yaml` (New File)
**Created production-ready values file with:**
- Production environment configuration
- Vault integration enabled with production path: `data-prod/app/data-prod-de/platform-apps/airflow-health-dashboard`
- Production-appropriate resource limits and autoscaling
- All production secrets managed via Vault
- Ingress, network policies, and PDB enabled

### 5. `VAULT.md` (New File)
**Created comprehensive documentation covering:**
- Overview of Vault integration
- Prerequisites and configuration steps
- Required secrets format and storage
- Vault setup instructions (IAM roles, Vault roles, policies)
- Deployment commands
- Troubleshooting guide
- Migration path from Kubernetes secrets to Vault

## Architecture

### Vault Secret Flow
1. **ServiceAccount** annotated with IAM role ARN for AWS IRSA
2. **Vault Agent Injector** injects init container that:
   - Authenticates using ServiceAccount token
   - Retrieves secrets from configured Vault path
   - Creates `/vault/secrets/secrets` file with exported environment variables
3. **Backend container** sources the secrets file via `BASH_ENV` environment variable
4. Application code accesses secrets as regular environment variables

### Backward Compatibility
- Chart maintains backward compatibility with Kubernetes secrets
- When `backend.vault.enabled: false`, uses traditional secret references
- When `secrets.create: true`, creates Kubernetes Secret resource
- Allows gradual migration from K8s secrets to Vault

## Required Vault Secrets

For each environment, store these secrets in Vault:

```json
{
  "AIRFLOW_USERNAME": "admin",
  "AIRFLOW_PASSWORD": "secure-password",
  "LLM_API_KEY": "api-key-for-llm-provider",
  "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/..." 
}
```

**Staging Path:** `data-dev/app/data-dev-de/platform-apps/airflow-health-dashboard`
**Production Path:** `data-prod/app/data-prod-de/platform-apps/airflow-health-dashboard`

## Deployment

### Staging
```bash
helm upgrade --install airflow-health-dashboard . \
  -f values.yaml \
  -f values.stg.yaml \
  --namespace airflow-health-dashboard
```

### Production
```bash
helm upgrade --install airflow-health-dashboard . \
  -f values.yaml \
  -f values.prod.yaml \
  --namespace airflow-health-dashboard
```

## Benefits

1. **Security**: Secrets stored centrally in Vault with access controls and audit logging
2. **Rotation**: Simplified secret rotation without redeploying applications
3. **Compliance**: Better audit trail and access management
4. **Consistency**: Follows same pattern as data-catalog and other platform services
5. **IRSA Integration**: Leverages AWS IAM roles for secure authentication

## Next Steps

1. **Configure Vault**:
   - Create IAM role with appropriate trust policy
   - Create Vault role and policy
   - Store secrets in Vault at the configured paths

2. **Update IAM Role ARN**:
   - Replace placeholder ARN in `values.stg.yaml` and `values.prod.yaml`
   - Ensure trust policy allows the ServiceAccount

3. **Test Deployment**:
   - Deploy to staging environment first
   - Verify Vault agent injection
   - Confirm secrets are available in backend container
   - Test application functionality

4. **Migrate Production**:
   - Store production secrets in Vault
   - Deploy with production values
   - Monitor for any issues
   - Optionally remove old Kubernetes secrets

## Comparison with data-catalog

Similar patterns used:
- ✅ ServiceAccount with IAM role annotation
- ✅ Vault agent annotations in podAnnotations
- ✅ BASH_ENV pointing to vault secrets file
- ✅ Shell script with exported environment variables
- ✅ Environment-specific Vault paths (data-dev, data-prod)

Key differences:
- data-catalog also injects key files (public_key.der, private_key.der) for JWT
- airflow-health-dashboard only needs simple string secrets
- Simpler secret structure (no base64 decoding needed)
