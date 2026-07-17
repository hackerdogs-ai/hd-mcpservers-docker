import React from 'react';
import ReactDOM from 'react-dom/client';
import { applyStoredTheme } from './lib/theme.js';
import './index.css';
import App from './App.jsx';

applyStoredTheme();

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
