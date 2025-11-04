# Frontend Dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for environment variables
ARG VITE_API_URL=/api/v1
ARG VITE_AIRFLOW_URL=http://localhost:8080

# Set environment variables for build
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_AIRFLOW_URL=$VITE_AIRFLOW_URL

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create a custom nginx.conf that works with non-root user
RUN printf 'pid /tmp/nginx.pid;\n\
error_log /var/log/nginx/error.log warn;\n\
events {\n\
    worker_connections 1024;\n\
}\n\
http {\n\
    include /etc/nginx/mime.types;\n\
    default_type application/octet-stream;\n\
    log_format main '"'"'$remote_addr - $remote_user [$time_local] "$request" '"'"'\n\
                    '"'"'$status $body_bytes_sent "$http_referer" '"'"'\n\
                    '"'"'"$http_user_agent" "$http_x_forwarded_for"'"'"';\n\
    access_log /var/log/nginx/access.log main;\n\
    sendfile on;\n\
    keepalive_timeout 65;\n\
    include /etc/nginx/conf.d/*.conf;\n\
}\n' > /etc/nginx/nginx.conf && \
    mkdir -p /var/cache/nginx /var/run /var/log/nginx && \
    chown -R nginx:nginx /var/cache/nginx /var/run /var/log/nginx /usr/share/nginx/html /etc/nginx && \
    chmod -R 755 /var/cache/nginx /var/run /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown nginx:nginx /var/run/nginx.pid

# Use non-root user
USER nginx

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
