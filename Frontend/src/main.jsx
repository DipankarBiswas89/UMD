import React from 'react';
import ReactDOM from 'react-dom/client'; // For React 18+
//import './index.css'; // Import global styles
import App from './App'; // Import the main App component

// This is where you initialize the app and render it to the DOM
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);