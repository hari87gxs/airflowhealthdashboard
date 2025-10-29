import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { formatDistanceToNow } from 'date-fns';

const TIME_RANGES = [
  { value: '24h', label: 'Last 24 Hours' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
];

function Dashboard() {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState('24h');
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchDashboard();
    
    if (autoRefresh) {
      const interval = setInterval(fetchDashboard, 120000); // Refresh every 2 minutes
      return () => clearInterval(interval);
    }
  }, [timeRange, autoRefresh]);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDomains(timeRange);
      setDashboardData(data);
    } catch (err) {
      setError(err.message);
      console.error('Failed to fetch dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDomainClick = (domainTag) => {
    navigate(`/domain/${encodeURIComponent(domainTag)}`);
  };

  const getHealthColor = (domain) => {
    if (domain.has_failures) return 'bg-red-50 border-red-200 hover:bg-red-100';
    if (domain.running_count > 0) return 'bg-blue-50 border-blue-200 hover:bg-blue-100';
    return 'bg-green-50 border-green-200 hover:bg-green-100';
  };

  const getHealthBadge = (domain) => {
    if (domain.has_failures) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          {domain.failed_count} Failed
        </span>
      );
    }
    if (domain.running_count > 0) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {domain.running_count} Running
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
        Healthy
      </span>
    );
  };

  if (loading && !dashboardData) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-red-800 mb-2">Error</h2>
        <p className="text-red-600">{error}</p>
        <button
          onClick={fetchDashboard}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-gray-700">Time Range:</label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {TIME_RANGES.map((range) => (
                <option key={range.value} value={range.value}>
                  {range.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Auto-refresh</span>
            </label>
            
            <button
              onClick={fetchDashboard}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {dashboardData?.last_updated && (
          <p className="text-xs text-gray-500 mt-2">
            Last updated: {formatDistanceToNow(new Date(dashboardData.last_updated), { addSuffix: true })}
          </p>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500">Total Domains</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">{dashboardData?.total_domains || 0}</div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500">Total DAGs</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">{dashboardData?.total_dags || 0}</div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500">Domains with Failures</div>
          <div className="text-3xl font-bold text-red-600 mt-2">
            {dashboardData?.domains.filter(d => d.has_failures).length || 0}
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500">Healthy Domains</div>
          <div className="text-3xl font-bold text-green-600 mt-2">
            {dashboardData?.domains.filter(d => !d.has_failures).length || 0}
          </div>
        </div>
      </div>

      {/* Domain List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Business Domains</h2>
        </div>
        
        <div className="divide-y divide-gray-200">
          {dashboardData?.domains.map((domain) => (
            <div
              key={domain.domain_tag}
              onClick={() => handleDomainClick(domain.domain_tag)}
              className={`p-6 cursor-pointer transition-colors border-l-4 ${getHealthColor(domain)}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {domain.domain_tag}
                    </h3>
                    {getHealthBadge(domain)}
                  </div>
                  
                  <div className="mt-2 grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">DAGs:</span>
                      <span className="ml-1 font-medium text-gray-900">{domain.total_dags}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Runs:</span>
                      <span className="ml-1 font-medium text-gray-900">{domain.total_runs}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Success:</span>
                      <span className="ml-1 font-medium text-green-600">{domain.success_count}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Failed:</span>
                      <span className="ml-1 font-medium text-red-600">{domain.failed_count}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Health:</span>
                      <span className="ml-1 font-medium text-gray-900">{domain.health_score.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
                
                <div className="ml-4">
                  <svg
                    className="h-5 w-5 text-gray-400"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M9 5l7 7-7 7"></path>
                  </svg>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {dashboardData?.domains.length === 0 && (
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <p className="text-gray-500">No domains found. Make sure your DAGs have tags configured in Airflow.</p>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
