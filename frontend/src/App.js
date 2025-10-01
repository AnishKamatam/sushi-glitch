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
      <nav className="floating-bottom-nav">
        <button
          className={`nav-item ${activeTab === 'plan' ? 'active' : ''}`}
          onClick={() => setActiveTab('plan')}
          title="Plan Card"
        >
          <div className="nav-icon plan-icon"></div>
        </button>
        <button
          className={`nav-item ${activeTab === 'sonar' ? 'active' : ''}`}
          onClick={() => setActiveTab('sonar')}
          title="Sonar Assist"
        >
          <div className="nav-icon sonar-icon"></div>
        </button>
        <button
          className={`nav-item ${activeTab === 'freshness' ? 'active' : ''}`}
          onClick={() => setActiveTab('freshness')}
          title="Freshness QA"
        >
          <div className="nav-icon freshness-icon"></div>
        </button>
      </nav>

      <main className="main-content">
        {renderActiveComponent()}
      </main>
    </div>
  );
}

export default App;