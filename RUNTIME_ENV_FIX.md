# Runtime Environment Variables Fix

## Problem

The frontend was showing the wrong Airflow URL (http://localhost:8080 instead of https://airflow.sgbank.st) because Vite bakes environment variables into the JavaScript bundle at **build time**, not runtime.

This means:
- Environment variables set in Kubernetes deployment had no effect
- The hardcoded build-time defaults were always used
- Different environments required different image builds

## Solution

Implemented **runtime environment variable injection** using a shell script that creates a configuration file when the container starts.

## Changes Made

### 1. Created `frontend/env.sh`
A script that runs at container startup to inject environment variables:
```bash
#!/bin/sh
cat <<EOF > /usr/share/nginx/html/env-config.js
window._env_ = {
  VITE_API_URL: "${VITE_API_URL:-/api/v1}",
  VITE_AIRFLOW_URL: "${VITE_AIRFLOW_URL:-http://localhost:8080}"
};
EOF
exec nginx -g 'daemon off;'
```

### 2. Updated `frontend/index.html`
Added script tag to load runtime config:
```html
<script src="/env-config.js"></script>
```

### 3. Updated `frontend/src/api.js`
Modified to check runtime config first, then fall back to build-time env vars:
```javascript
const getEnvVar = (key, defaultValue) => {
  if (window._env_ && window._env_[key]) {
    return window._env_[key];
  }
  return import.meta.env[key] || defaultValue;
};
```

### 4. Updated `frontend/src/App.jsx`
Same runtime config support for Airflow URL link.

### 5. Updated `frontend/Dockerfile`
- Removed hardcoded build arguments
- Added env.sh script to `/docker-entrypoint.d/40-env.sh`
- Made script executable

### 6. Fixed nginx Port
Changed docker-compose frontend port from `3000:80` to `3000:8080` to match nginx config.

## How It Works

1. **Build Time**: Application is built WITHOUT hardcoded environment variables
2. **Container Start**: The `env.sh` script runs automatically (nginx alpine supports `/docker-entrypoint.d/`)
3. **Script Creates**: `/usr/share/nginx/html/env-config.js` with runtime env vars
4. **Browser Loads**: `index.html` loads `env-config.js` before the React app
5. **App Uses**: JavaScript checks `window._env_` first, then falls back to build-time values

## Benefits

✅ **Single Image**: One image works for all environments (dev, staging, prod)
✅ **Runtime Configuration**: Change URLs without rebuilding
✅ **Kubernetes Native**: Works seamlessly with ConfigMaps and Secrets
✅ **Backward Compatible**: Falls back to build-time env vars if runtime config is missing
✅ **Debug Friendly**: Console logs show both build-time and runtime config

## Deployment

The Helm deployment already injects the correct environment variables:
```yaml
env:
- name: VITE_API_URL
  value: "/airflow-health-dashboard/api/v1"
- name: VITE_AIRFLOW_URL
  value: "https://airflow.sgbank.st"
```

## Verification

Check browser console for:
```
🔧 API Client initialized with base URL: /airflow-health-dashboard/api/v1
🌍 Runtime environment: {
  VITE_API_URL: "/airflow-health-dashboard/api/v1",
  VITE_AIRFLOW_URL: "https://airflow.sgbank.st"
}
```

## Docker Runtime Error Fix

The error `failed to get create response: rpc error: code = Unavailable desc = connection error: desc = "transport: Error while dialing: dial unix /var/run/tw.runc.sock: connect: connection refused"` is a Docker/containerd issue, not application code.

**To fix:**
1. Restart Docker Desktop
2. Or run: `docker system prune -a` (warning: removes all unused images)
3. Or check if OrbStack needs restart

This is typically a transient Docker daemon communication issue and should resolve after Docker restart.

## Image Versions

- **v.0.0.10**: Fixed nginx log_format directive error
- **v.0.0.11**: Added runtime environment variable support (CURRENT)

## Testing Locally

```bash
cd /Users/jiangzheng.xie/Projects/airflowhealthdashboard
docker-compose up -d

# Check logs to verify env-config.js is created
docker logs airflow-health-frontend

# Open http://localhost:3000 and check browser console
```
