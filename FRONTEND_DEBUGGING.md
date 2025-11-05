# Frontend Debugging Guide

## Overview
This guide helps you debug frontend issues when the application is not showing content.

## Logging System

The frontend now has comprehensive logging at every level:

### 1. Browser Console Logs

Open your browser's Developer Tools (F12 or Cmd+Option+I on Mac) and check the Console tab. You should see:

#### Application Initialization
- `🚀 Frontend initialization started` - App is loading
- `📍 Environment:` - Shows all environment variables
- `📦 Root element found: true/false` - Whether the DOM root exists
- `✅ React app rendered successfully` - React mounted successfully

#### Health Check
- `🏥 App mounted, performing health check...` - Health check started
- `✅ Health check successful:` - Health check passed
- `❌ Health check failed:` - Health check failed (check details)

#### API Calls
All API calls are logged with:
- `📤 API Request:` - Outgoing request details
- `📥 API Response:` - Successful response
- `❌ API Error:` - Error details including status codes

#### Dashboard Loading
- `📊 Dashboard component mounted` - Dashboard started loading
- `🔄 Fetching dashboard data...` - Data fetch initiated
- `✅ Dashboard data fetched successfully:` - Data loaded
- `❌ Failed to fetch dashboard:` - Data fetch failed

#### Navigation
- `🧭 Route changed:` - Shows current route path

### 2. Nginx Logs (Docker)

To view nginx logs when running in Docker:

```bash
# View nginx access logs
docker logs <frontend-container-name> 2>&1 | grep "GET\|POST"

# View nginx error logs
docker logs <frontend-container-name> 2>&1 | grep "error"

# Follow logs in real-time
docker logs -f <frontend-container-name>

# Access logs inside container
docker exec -it <frontend-container-name> tail -f /var/log/nginx/access.log

# Error logs inside container
docker exec -it <frontend-container-name> tail -f /var/log/nginx/error.log
```

### 3. Network Tab

Check the Network tab in Developer Tools to see:
- All HTTP requests and their status codes
- Request/response headers
- Response payloads
- Request timing

## Common Issues and Solutions

### Issue 1: Blank Page, No Console Logs

**Symptoms:**
- Page is completely blank
- No console logs appear

**Diagnosis:**
1. Check if JavaScript is enabled in browser
2. Check if there are any CSP (Content Security Policy) errors
3. Look for syntax errors that prevent JS from loading

**Solution:**
```bash
# Rebuild the frontend
cd frontend
npm run build
```

### Issue 2: "Root element not found" Error

**Symptoms:**
- Console shows: `❌ Root element not found!`

**Diagnosis:**
- The `index.html` file is not being served correctly
- Build process failed

**Solution:**
```bash
# Check if index.html exists
ls -la frontend/dist/index.html

# Rebuild frontend
cd frontend
npm run build
```

### Issue 3: API Connection Errors

**Symptoms:**
- Console shows: `❌ Health check failed`
- Red connection error banner appears

**Diagnosis:**
Look at the API error details in console:
- `status: 0` or `Network Error` = Backend not reachable
- `status: 404` = Wrong API URL or endpoint
- `status: 500` = Backend error
- `isTimeout: true` = Request took too long

**Solution:**

```bash
# Check environment variables
echo $VITE_API_URL

# Verify backend is running
curl http://localhost:8000/api/v1/health

# Check docker-compose services
docker-compose ps

# View backend logs
docker logs <backend-container-name>
```

### Issue 4: No Dashboard Data

**Symptoms:**
- App loads but no domains shown
- Console shows: `✅ Dashboard data fetched successfully` but `domainsCount: 0`

**Diagnosis:**
- Backend returned empty data
- Airflow has no DAGs or no DAGs with tags

**Solution:**
1. Check backend response in Network tab
2. Verify Airflow has DAGs with tags
3. Check Airflow connection in backend logs

### Issue 5: Stuck on Loading Spinner

**Symptoms:**
- Loading spinner shows indefinitely
- Console shows request started but no response

**Diagnosis:**
- Request timeout
- Backend is processing but not responding

**Solution:**
```bash
# Check backend logs
docker logs <backend-container-name>

# Check if request is still processing
# Look for timeout errors in console
```

## Environment Variables

Ensure these are set correctly:

```bash
# Frontend environment variables
VITE_API_URL=http://localhost:8000/api/v1  # Backend API URL
VITE_AIRFLOW_URL=http://localhost:8080      # Airflow UI URL
```

Check in console under `📍 Environment:` to see actual values being used.

## Debug Checklist

1. ✅ Open browser console (F12)
2. ✅ Check for `🚀 Frontend initialization started`
3. ✅ Verify environment variables in console
4. ✅ Check health check result
5. ✅ Monitor API requests in Network tab
6. ✅ Look for any red errors in console
7. ✅ Check nginx logs (if in Docker)
8. ✅ Verify backend is running
9. ✅ Test backend health endpoint directly

## Testing Endpoints Manually

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test domains endpoint
curl http://localhost:8000/api/v1/domains?time_range=24h

# Test with verbose output
curl -v http://localhost:8000/api/v1/health
```

## Browser Console Commands

Useful commands to run in browser console:

```javascript
// Check current environment
console.log(import.meta.env);

// Test API call manually
fetch('http://localhost:8000/api/v1/health')
  .then(r => r.json())
  .then(d => console.log('Health:', d))
  .catch(e => console.error('Error:', e));

// Check if app is mounted
console.log(document.getElementById('root'));
```

## Getting Help

When reporting issues, include:
1. Full browser console output (copy all logs)
2. Network tab screenshot showing failed requests
3. Browser and version
4. Environment variables being used
5. Docker logs (if applicable)

The emoji-prefixed logs make it easy to spot different types of events:
- 🚀 = Initialization
- 🏥 = Health checks
- 📤/📥 = API requests/responses
- ❌ = Errors
- ✅ = Success
- 📊 = Dashboard events
- 🧭 = Navigation
- 🔄 = Data refresh
- ⏳ = Loading states
