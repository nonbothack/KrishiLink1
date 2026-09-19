import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './styles/tokens.css';
import './styles/app.css';

const root = document.getElementById('root');
const app = (
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
if (root.hasAttribute('data-prerendered')) ReactDOM.hydrateRoot(root, app);
else ReactDOM.createRoot(root).render(app);
