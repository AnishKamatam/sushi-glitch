import React from 'react';
import './LoadingScreen.css';

const LoadingScreen = () => {
  return (
    <div className="loading-screen">
      <div className="loading-container">
        {/* LEVIATHAN Logo */}
        <div className="logo-placeholder">
          <img 
            src="/leviathan-logo.png" 
            alt="LEVIATHAN Logo" 
            className="logo-image"
          />
        </div>
        
        {/* App title */}
        <h1 className="app-title">LEVIATHAN</h1>
        
        {/* Loading animation */}
        <div className="loading-spinner">
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
        </div>
        
      </div>
    </div>
  );
};

export default LoadingScreen;
