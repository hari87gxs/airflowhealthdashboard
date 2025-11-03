import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { formatDistanceToNow, format } from 'date-fns';

const TIME_RANGES = [
  { value: '24h', label: 'Last 24 Hours' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
];

function DomainDetail() {
  const { domainTag } = useParams();
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState('24h');
  const [domainData, setDomainData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedDag, setExpandedDag] = useState(null);
  const [dagRuns, setDagRuns] = useState({});
  const [isAirflowAvailable, setIsAirflowAvailable] = useState(true);
  const [isForceRefreshing, setIsForceRefreshing] = useState(false);
  const [lastRefreshTime, setLastRefreshTime] = useState(null);

  const fetchDomainDetail = useCallback(async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      if (forceRefresh) {
        setIsForceRefreshing(true);
      }
      const data = await api.getDomainDetail(domainTag, timeRange, forceRefresh);
      setDomainData(data);
      setIsAirflowAvailable(true);
      setLastRefreshTime(new Date());
    } catch (err) {
      setError(err.message);
      setIsAirflowAvailable(false);
      console.error('Failed to fetch domain detail:', err);
    } finally {
      setLoading(false);
      setIsForceRefreshing(false);
    }
  }, [domainTag, timeRange]);

  useEffect(() => {
    fetchDomainDetail();
  }, [fetchDomainDetail]);

  const handleRefresh = () => {
    fetchDomainDetail(true); // Force refresh from Airflow
  };

  const fetchDagRuns = async (dagId) => {
    if (dagRuns[dagId]) {
      // Already fetched
      return;
    }

    try {
      const runs = await api.getDagRuns(domainTag, dagId, timeRange, 20);
      setDagRuns((prev) => ({ ...prev, [dagId]: runs }));
    } catch (err) {
      console.error(`Failed to fetch runs for ${dagId}:`, err);
    }
  };

  const toggleDagExpansion = async (dagId) => {
    if (expandedDag === dagId) {
      setExpandedDag(null);
    } else {
      setExpandedDag(dagId);
      await fetchDagRuns(dagId);
    }
  };

  const getStateColor = (state) => {
    const colors = {
      success: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      running: 'bg-blue-100 text-blue-800',
      queued: 'bg-yellow-100 text-yellow-800',
    };
    return colors[state] || 'bg-gray-100 text-gray-800';
  };

  const getDagHealthColor = (dag) => {
    if (dag.failed_count > 0) return 'border-red-200 bg-red-50';
    if (dag.running_count > 0) return 'border-blue-200 bg-blue-50';
    return 'border-green-200 bg-green-50';
  };

  if (loading && !domainData) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => navigate('/')}
          className="text-blue-600 hover:text-blue-800 flex items-center"
        >
          ← Back to Dashboard
        </button>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-800 mb-2">Error</h2>
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Airflow Unavailable Warning */}
      {!isAirflowAvailable && domainData && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                <strong className="font-medium">Airflow is currently unavailable.</strong> Showing cached data. Data will automatically refresh when Airflow is back online.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/')}
          className="text-blue-600 hover:text-blue-800 flex items-center"
        >
          ← Back to Dashboard
        </button>

        <div className="flex items-center space-x-4">
          {lastRefreshTime && (
            <span className="text-sm text-gray-600">
              Last refreshed: {formatDistanceToNow(lastRefreshTime, { addSuffix: true })}
            </span>
          )}
          
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
          
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            title="Force refresh from Airflow (may take up to 2 minutes)"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Domain Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">{domainTag}</h1>
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <div className="text-sm text-gray-500">DAGs</div>
            <div className="text-2xl font-bold text-gray-900">{domainData?.summary.total_dags}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Total Runs</div>
            <div className="text-2xl font-bold text-gray-900">{domainData?.summary.total_runs}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Success</div>
            <div className="text-2xl font-bold text-green-600">{domainData?.summary.success_count}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Failed</div>
            <div className="text-2xl font-bold text-red-600">{domainData?.summary.failed_count}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Health Score</div>
            <div className="text-2xl font-bold text-gray-900">{domainData?.summary.health_score.toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* DAG List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">DAGs in {domainTag}</h2>
        </div>

        <div className="divide-y divide-gray-200">
          {domainData?.dags.map((dag) => (
            <div key={dag.dag_id} className={`border-l-4 ${getDagHealthColor(dag)}`}>
              {/* DAG Summary */}
              <div
                className="p-6 cursor-pointer hover:bg-gray-50"
                onClick={() => toggleDagExpansion(dag.dag_id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-base font-semibold text-gray-900">
                        {dag.dag_display_name || dag.dag_id}
                      </h3>
                      {dag.is_paused && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          Paused
                        </span>
                      )}
                    </div>
                    
                    {dag.description && (
                      <p className="text-sm text-gray-500 mt-1">{dag.description}</p>
                    )}

                    <div className="mt-3 flex items-center space-x-6 text-sm">
                      <div>
                        <span className="text-gray-500">Total Runs:</span>
                        <span className="ml-1 font-medium">{dag.total_runs}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Success:</span>
                        <span className="ml-1 font-medium text-green-600">{dag.success_count}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Failed:</span>
                        <span className="ml-1 font-medium text-red-600">{dag.failed_count}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Running:</span>
                        <span className="ml-1 font-medium text-blue-600">{dag.running_count}</span>
                      </div>
                      {dag.last_run_date && (
                        <div>
                          <span className="text-gray-500">Last Run:</span>
                          <span className="ml-1 font-medium">
                            {formatDistanceToNow(new Date(dag.last_run_date), { addSuffix: true })}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="ml-4 flex items-center space-x-2">
                    <a
                      href={dag.airflow_dag_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      View in Airflow →
                    </a>
                    <svg
                      className={`h-5 w-5 text-gray-400 transition-transform ${
                        expandedDag === dag.dag_id ? 'transform rotate-90' : ''
                      }`}
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

              {/* Expanded DAG Runs */}
              {expandedDag === dag.dag_id && (
                <div className="px-6 pb-6 bg-gray-50">
                  {dagRuns[dag.dag_id] ? (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-gray-700 mb-3">Recent Runs</h4>
                      {dagRuns[dag.dag_id].map((run) => (
                        <div
                          key={run.dag_run_id}
                          className="bg-white rounded border border-gray-200 p-3 flex items-center justify-between"
                        >
                          <div className="flex items-center space-x-4">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStateColor(run.state)}`}>
                              {run.state}
                            </span>
                            <div className="text-sm">
                              <div className="font-medium text-gray-900">
                                {format(new Date(run.execution_date), 'MMM d, yyyy HH:mm:ss')}
                              </div>
                              {run.start_date && run.end_date && (
                                <div className="text-gray-500">
                                  Duration: {Math.round((new Date(run.end_date) - new Date(run.start_date)) / 1000)}s
                                </div>
                              )}
                            </div>
                          </div>
                          <a
                            href={run.airflow_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 text-sm"
                          >
                            View →
                          </a>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex justify-center py-4">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {domainData?.dags.length === 0 && (
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <p className="text-gray-500">No DAGs found in this domain.</p>
        </div>
      )}
    </div>
  );
}

export default DomainDetail;
