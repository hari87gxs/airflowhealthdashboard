/**
 * API Client for communicating with the backend
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

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
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
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
    const response = await apiClient.get('/health');
    return response.data;
  },

  /**
   * Get all domain summaries
   * @param {string} timeRange - '24h', '7d', or '30d'
   */
  async getDomains(timeRange = '24h') {
    const response = await apiClient.get('/domains', {
      params: { time_range: timeRange },
    });
    return response.data;
  },

  /**
   * Get detailed information for a specific domain
   * @param {string} domainTag - The domain tag
   * @param {string} timeRange - '24h', '7d', or '30d'
   */
  async getDomainDetail(domainTag, timeRange = '24h') {
    const response = await apiClient.get(`/domains/${domainTag}`, {
      params: { time_range: timeRange },
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
