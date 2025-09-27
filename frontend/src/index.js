import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import * as serviceWorker from './services/serviceWorker';

const root = ReactDOM.createRoot(
  document.getElementById('root')
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

serviceWorker.register({
  onSuccess: () => {
    console.log('LEVIATHAN is ready for offline use');
  },
  onUpdate: () => {
    console.log('New version of LEVIATHAN is available');
    if (window.confirm('A new version is available. Refresh to update?')) {
      window.location.reload();
    }
  }
});

reportWebVitals();