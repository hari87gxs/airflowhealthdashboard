import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

console.log('🚀 Frontend initialization started');
console.log('📍 Environment:', {
  apiUrl: import.meta.env.VITE_API_URL,
  airflowUrl: import.meta.env.VITE_AIRFLOW_URL,
  mode: import.meta.env.MODE,
  dev: import.meta.env.DEV,
  prod: import.meta.env.PROD,
});

const rootElement = document.getElementById('root');
console.log('📦 Root element found:', !!rootElement);

if (!rootElement) {
  console.error('❌ Root element not found! Cannot mount React app.');
} else {
  try {
    console.log('🎯 Creating React root...');
    const root = ReactDOM.createRoot(rootElement);
    
    console.log('🎨 Rendering React app...');
    root.render(
      <React.StrictMode>
        <BrowserRouter basename="/airflow-health-dashboard">
          <App />
        </BrowserRouter>
      </React.StrictMode>
    );
    console.log('✅ React app rendered successfully');
  } catch (error) {
    console.error('❌ Failed to render React app:', error);
  }
}
