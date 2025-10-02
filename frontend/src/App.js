import React, { useState, useEffect } from 'react';
import './App.css';
import PlanCard from './components/PlanCard';
import SonarAssist from './components/SonarAssist';
import FreshnessQA from './components/FreshnessQA';
import LoadingScreen from './components/LoadingScreen';

function App() {
  const [activeTab, setActiveTab] = useState('plan');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate loading time - you can adjust this or remove it
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 3000); // 3 second loading screen

    return () => clearTimeout(timer);
  }, []);

  const renderActiveComponent = () => {
    switch (activeTab) {
      case 'plan':
        return <PlanCard />;
      case 'sonar':
        return <SonarAssist />;
      case 'freshness':
        return <FreshnessQA />;
      default:
        return <PlanCard />;
    }
  };

  // Show loading screen while loading
  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <div className="App">
      <main className="main-content">
        {renderActiveComponent()}
      </main>

      {/* Bottom Navigation Bar */}
      <div className="bottom-navigation">
        <div className="nav-item" onClick={() => setActiveTab('plan')}>
          <div className={`nav-icon ${activeTab === 'plan' ? 'active' : ''}`}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
          </div>
        </div>
        <div className="nav-item" onClick={() => setActiveTab('sonar')}>
          <div className={`nav-icon ${activeTab === 'sonar' ? 'active' : ''}`}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
        </div>
        <div className="nav-item" onClick={() => setActiveTab('freshness')}>
          <div className={`nav-icon ${activeTab === 'freshness' ? 'active' : ''}`}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 12l2 2 4-4"/>
              <path d="M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9c1.3 0 2.52.28 3.63.8"/>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;