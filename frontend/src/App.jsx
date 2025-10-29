import React, { useState, useEffect } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import DomainDetail from './components/DomainDetail';
import { api } from './api';

function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const health = await api.getHealth();
      setHealthStatus(health);
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthStatus({ status: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <Link to="/" className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                Airflow Health Dashboard
              </h1>
            </Link>
            
            <div className="flex items-center space-x-4">
              {!loading && healthStatus && (
                <div className="flex items-center space-x-2">
                  <div
                    className={`h-3 w-3 rounded-full ${
                      healthStatus.status === 'healthy'
                        ? 'bg-green-500'
                        : healthStatus.status === 'degraded'
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                  />
                  <span className="text-sm text-gray-600">
                    {healthStatus.airflow_connection === 'connected'
                      ? 'Connected'
                      : 'Disconnected'}
                  </span>
                </div>
              )}
              
              <a
                href={`${import.meta.env.VITE_AIRFLOW_URL || 'http://localhost:8080'}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Open Airflow UI →
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : healthStatus?.status === 'error' ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">
              Connection Error
            </h2>
            <p className="text-red-600">
              Unable to connect to the backend API. Please check the configuration.
            </p>
          </div>
        ) : (
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/domain/:domainTag" element={<DomainDetail />} />
          </Routes>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            {healthStatus?.version && `v${healthStatus.version} · `}
            Read-only monitoring dashboard · Data refreshed every{' '}
            {Math.floor((healthStatus?.cache_ttl || 120) / 60)} minutes
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
