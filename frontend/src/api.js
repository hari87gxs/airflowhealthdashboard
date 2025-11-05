/**
 * API Client for communicating with the backend
 */

import axios from 'axios';

// Use runtime config if available, otherwise fall back to build-time env vars
const getEnvVar = (key, defaultValue) => {
  // Check runtime config first
  if (window._env_ && window._env_[key]) {
    return window._env_[key];
  }
  // Fall back to build-time Vite env vars
  return import.meta.env[key] || defaultValue;
};

const API_BASE_URL = getEnvVar('VITE_API_URL', 'http://localhost:8000/api/v1');

console.log('🔧 API Client initialized with base URL:', API_BASE_URL);
console.log('🌍 Runtime environment:', window._env_);

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const timestamp = new Date().toISOString();
    console.log(`📤 [${timestamp}] API Request:`, {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      fullUrl: `${config.baseURL}${config.url}`,
      params: config.params,
      timeout: config.timeout,
    });
    return config;
  },
  (error) => {
    console.error('❌ Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    const timestamp = new Date().toISOString();
    console.log(`📥 [${timestamp}] API Response:`, {
      status: response.status,
      statusText: response.statusText,
      url: response.config.url,
      dataSize: JSON.stringify(response.data).length,
      data: response.data,
    });
    return response;
  },
  (error) => {
    const timestamp = new Date().toISOString();
    console.error(`❌ [${timestamp}] API Error:`, {
      message: error.message,
      code: error.code,
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      baseURL: error.config?.baseURL,
      data: error.response?.data,
      isTimeout: error.code === 'ECONNABORTED',
      isNetworkError: error.message === 'Network Error',
    });
    return Promise.reject(error);
  }
);

/**
 * API Service
 */
export const api = {
  /**
   * Get health status
   */
  async getHealth() {
    console.log('🏥 Calling getHealth()...');
    try {
      const response = await apiClient.get('/health');
      console.log('✅ getHealth() successful');
      return response.data;
    } catch (error) {
      console.error('❌ getHealth() failed:', error.message);
      throw error;
    }
  },

  /**
   * Get all domain summaries
   * @param {string} timeRange - '24h', '7d', or '30d'
   * @param {boolean} forceRefresh - Force refresh from Airflow, bypassing cache
   */
  async getDomains(timeRange = '24h', forceRefresh = false) {
    console.log(`📊 Calling getDomains(timeRange=${timeRange}, forceRefresh=${forceRefresh})...`);
    try {
      const response = await apiClient.get('/domains', {
        params: { 
          time_range: timeRange,
          force_refresh: forceRefresh
        },
        timeout: forceRefresh ? 120000 : 30000, // 120s for force refresh, 30s for cached
      });
      console.log(`✅ getDomains() successful, found ${response.data?.domains?.length || 0} domains`);
      return response.data;
    } catch (error) {
      console.error('❌ getDomains() failed:', error.message);
      throw error;
    }
  },

  /**
   * Get detailed information for a specific domain
   * @param {string} domainTag - The domain tag
   * @param {string} timeRange - '24h', '7d', or '30d'
   * @param {boolean} forceRefresh - Force refresh from Airflow, bypassing cache
   */
  async getDomainDetail(domainTag, timeRange = '24h', forceRefresh = false) {
    const response = await apiClient.get(`/domains/${domainTag}`, {
      params: { 
        time_range: timeRange,
        force_refresh: forceRefresh
      },
      timeout: 120000, // 120 second timeout for large domains
    });
    return response.data;
  },

  /**
   * Get DAG runs for a specific DAG
   * @param {string} domainTag - The domain tag
   * @param {string} dagId - The DAG ID
   * @param {string} timeRange - '24h', '7d', or '30d'
   * @param {number} limit - Maximum number of runs to return
   */
  async getDagRuns(domainTag, dagId, timeRange = '24h', limit = 50) {
    const response = await apiClient.get(`/domains/${domainTag}/dags/${dagId}/runs`, {
      params: { time_range: timeRange, limit },
    });
    return response.data;
  },

  /**
   * Clear cache
   */
  async clearCache() {
    const response = await apiClient.post('/cache/clear');
    return response.data;
  },

  /**
   * Get AI-powered failure analysis
   * @param {string} timeRange - '24h', '7d', or '30d'
   */
  async getFailureAnalysis(timeRange = '24h') {
    const response = await apiClient.get('/analysis/failures', {
      params: { time_range: timeRange },
      timeout: 60000, // 60 second timeout for LLM analysis
    });
    return response.data;
  },
};

export default api;
