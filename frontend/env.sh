#!/bin/sh
# Script to inject runtime environment variables into the built frontend

# Create env-config.js in a writable location (/tmp)
cat <<EOF > /tmp/env-config.js
window._env_ = {
  VITE_API_URL: "${VITE_API_URL:-/api/v1}",
  VITE_AIRFLOW_URL: "${VITE_AIRFLOW_URL:-http://localhost:8080}"
};
EOF

echo "Environment configuration created:"
cat /tmp/env-config.js

# Start nginx
exec nginx -g 'daemon off;'
