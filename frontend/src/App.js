import React, { useState } from 'react';
import './App.css';
import PlanCard from './components/PlanCard';
import SonarAssist from './components/SonarAssist';
import FreshnessQA from './components/FreshnessQA';

function App() {
  const [activeTab, setActiveTab] = useState('plan');

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

  return (
    <div className="App">
      <header className="app-header">
        <h1>LEVIATHAN</h1>
        <p>Bringing big insights for small crews</p>
      </header>

      <nav className="tab-navigation">
        <button
          className={`tab ${activeTab === 'plan' ? 'active' : ''}`}
          onClick={() => setActiveTab('plan')}
        >
          Plan Card
        </button>
        <button
          className={`tab ${activeTab === 'sonar' ? 'active' : ''}`}
          onClick={() => setActiveTab('sonar')}
        >
          Sonar Assist
        </button>
        <button
          className={`tab ${activeTab === 'freshness' ? 'active' : ''}`}
          onClick={() => setActiveTab('freshness')}
        >
          Freshness QA
        </button>
      </nav>

      <main className="main-content">
        {renderActiveComponent()}
      </main>
    </div>
  );
}

export default App;