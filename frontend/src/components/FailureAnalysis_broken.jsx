import React, { useState, useEffect } from 'react';
import { api } from '../api';

function FailureAnalysis({ timeRange }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalysis();
  }, [timeRange]);

  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getFailureAnalysis(timeRange);
      console.log('Failure analysis data:', data); // Debug log
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
      console.error('Failed to fetch failure analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // Show loading if no data loaded yet
  if (!analysis) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-4 text-gray-600">Loading analysis...</span>
        </div>
      </div>
    );
  }

  // Check if there are actually failures
  const hasFailures = analysis.total_failed_dags > 0 || 
                     (analysis.failed_dags && analysis.failed_dags.length > 0);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-4 text-gray-600">Analyzing failures with AI...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-800 mb-2">Analysis Error</h3>
        <p className="text-red-600">{error}</p>
        <button
          onClick={fetchAnalysis}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry Analysis
        </button>
      </div>
    );
  }

  const llm = analysis.llm_analysis || {};

  return (
    <div className="space-y-12">
      {/* ========================================== */}
      {/* SECTION 1: COMPREHENSIVE DAG SUMMARY */}
      {/* ========================================== */}
      <div className="space-y-6">
        {/* Section Header */}
        <div className="border-b-4 border-indigo-500 pb-4">
          <h2 className="text-3xl font-bold text-gray-900 flex items-center">
            <svg className="h-8 w-8 mr-3 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            DAG Health Summary & Analysis
          </h2>
          <p className="text-gray-600 mt-2 ml-11">
            Overall analysis of all DAGs for the {timeRange} time period
          </p>
          <button
            onClick={fetchAnalysis}
            disabled={loading}
            className="mt-3 ml-11 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 text-sm"
          >
            Refresh Analysis
          </button>
        </div>

        {/* Overall Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total DAGs Analyzed</p>
                <p className="text-2xl font-bold text-gray-900">{analysis.total_analyzed_dags || 'N/A'}</p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Healthy DAGs</p>
                <p className="text-2xl font-bold text-green-600">{(analysis.total_analyzed_dags || 0) - (analysis.total_failed_dags || 0)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-red-100 rounded-md flex items-center justify-center">
                  <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Failed DAGs</p>
                <p className="text-2xl font-bold text-red-600">{analysis.total_failed_dags || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-orange-100 rounded-md flex items-center justify-center">
                  <svg className="w-5 h-5 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Failed Runs</p>
                <p className="text-2xl font-bold text-orange-600">{analysis.total_failed_runs || 0}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Health Status Summary */}
        {!hasFailures ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center">
              <svg className="h-6 w-6 text-green-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h3 className="text-lg font-semibold text-green-900">All Systems Healthy</h3>
                <p className="text-sm text-green-700">All DAGs are running successfully in the selected time range. No failures detected.</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <div className="flex items-center">
              <svg className="h-6 w-6 text-yellow-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h3 className="text-lg font-semibold text-yellow-900">Attention Required</h3>
                <p className="text-sm text-yellow-700">
                  {analysis.total_failed_dags} DAG{analysis.total_failed_dags !== 1 ? 's have' : ' has'} failures requiring attention. 
                  See detailed analysis below.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ========================================== */}
      {/* SECTION 2: AI FAILURE ANALYSIS (Only if failures exist) */}
      {/* ========================================== */}
      {hasFailures && (
        <div className="space-y-6">
          {/* Section Header */}
          <div className="border-b-4 border-blue-500 pb-4">
            <h2 className="text-3xl font-bold text-gray-900 flex items-center">
              <svg className="h-8 w-8 mr-3 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              AI Failure Analysis
            </h2>
            <p className="text-gray-600 mt-2 ml-11">
              Intelligent analysis of {analysis.total_failed_dags} failed DAGs with {analysis.total_failed_runs} failed runs
            </p>
          </div>

        {/* Executive Summary */}
        {llm.summary && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-600 rounded-lg p-6 shadow-md">
            <h3 className="text-xl font-semibold text-blue-900 mb-3 flex items-center">
              <svg className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Executive Summary
            </h3>
            <p className="text-gray-800 text-lg leading-relaxed">{llm.summary}</p>
          </div>
        )}

        {/* Failure Categories */}
        {llm.categories && llm.categories.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="px-6 py-4 bg-gradient-to-r from-purple-600 to-purple-700 text-white">
              <h3 className="text-xl font-semibold flex items-center">
                <svg className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                Categories of Failures
              </h3>
            </div>
            <div className="divide-y divide-gray-200">
              {llm.categories.map((category, index) => (
                <div key={index} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h4 className="text-lg font-semibold text-gray-900">{category.name}</h4>
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                          {category.count} DAG{category.count !== 1 ? 's' : ''}
                        </span>
                      </div>
                      <p className="text-gray-700 mt-2">{category.description}</p>
                      {category.dag_ids && category.dag_ids.length > 0 && (
                        <div className="mt-3 p-3 bg-gray-50 rounded">
                          <p className="text-sm text-gray-600 font-medium mb-1">Affected DAGs:</p>
                          <p className="text-sm text-gray-800">
                            {category.dag_ids.slice(0, 5).join(', ')}
                            {category.dag_ids.length > 5 && (
                              <span className="text-gray-500"> +{category.dag_ids.length - 5} more</span>
                            )}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Items */}
        {llm.action_items && llm.action_items.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="px-6 py-4 bg-gradient-to-r from-orange-600 to-orange-700 text-white">
              <h3 className="text-xl font-semibold flex items-center">
                <svg className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
                Recommended Action Items
              </h3>
            </div>
            <div className="divide-y divide-gray-200">
              {llm.action_items.map((action, index) => (
                <div key={index} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold border-2 ${getPriorityColor(action.priority)}`}>
                        {action.priority?.toUpperCase() || 'MEDIUM'}
                      </span>
                    </div>
                    <div className="flex-1">
                      <h4 className="text-lg font-semibold text-gray-900">{action.title}</h4>
                      <p className="text-gray-700 mt-2">{action.description}</p>
                      {action.affected_dags && action.affected_dags.length > 0 && (
                        <div className="mt-3 p-3 bg-gray-50 rounded">
                          <p className="text-sm text-gray-600 font-medium mb-1">Affects:</p>
                          <p className="text-sm text-gray-800">
                            {action.affected_dags.slice(0, 5).join(', ')}
                            {action.affected_dags.length > 5 && (
                              <span className="text-gray-500"> +{action.affected_dags.length - 5} more</span>
                            )}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      )}

      {/* ========================================== */}
      {/* SECTION 3: ERROR REPORTS & LOGS (Only if failures exist) */}
      {/* ========================================== */}
      {hasFailures && (
        <div className="space-y-6 pt-8 border-t-4 border-red-500">
          {/* Section Header */}
          <div className="pb-4">
            <h2 className="text-3xl font-bold text-gray-900 flex items-center">
              <svg className="h-8 w-8 mr-3 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Error Reports &amp; Failed DAG Logs
            </h2>
            <p className="text-gray-600 mt-2 ml-11">
              Detailed logs and error information for all failed DAGs
            </p>
          </div>

        {/* Consolidated Logs */}
        {analysis.consolidated_logs && analysis.consolidated_logs.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="px-6 py-4 bg-gradient-to-r from-red-600 to-red-700 text-white">
              <h3 className="text-xl font-semibold">
                Failed Task Logs ({analysis.consolidated_logs.length})
              </h3>
            </div>
            <div className="divide-y divide-gray-200">
              {analysis.consolidated_logs.map((log, index) => (
                <div key={index} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900">{log.dag_id} / {log.task_id}</h4>
                      <p className="text-sm text-gray-600 mt-1">Run ID: {log.dag_run_id}</p>
                      <p className="text-sm text-gray-600">Execution: {new Date(log.execution_date).toLocaleString()}</p>
                    </div>
                    <a
                      href={log.airflow_log_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm flex items-center"
                    >
                      View in Airflow
                      <svg className="h-4 w-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </div>
                  <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-xs text-gray-100 font-mono whitespace-pre-wrap">
                      {log.log_content || 'No log content available'}
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Failed DAGs Summary Table */}
        {analysis.failed_dags && analysis.failed_dags.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="px-6 py-4 bg-gradient-to-r from-gray-700 to-gray-800 text-white">
              <h3 className="text-xl font-semibold">All Failed DAGs Summary</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DAG ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Domain</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Failed Runs</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {analysis.failed_dags.map((dag, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm font-medium text-gray-900">{dag.dag_id}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                          {dag.domain_tag}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          {dag.failed_count} failure{dag.failed_count !== 1 ? 's' : ''}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {dag.description || 'No description'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default FailureAnalysis;
