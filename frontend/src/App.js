import React, { useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useSwipeable } from 'react-swipeable';
import './App.css';
import PlanCard from './components/PlanCard';
import SonarAssist from './components/SonarAssist';
import FreshnessQA from './components/FreshnessQA';

const tabs = [
  { id: 'plan', label: 'Plan Card', Component: PlanCard },
  { id: 'sonar', label: 'Sonar Assist', Component: SonarAssist },
  { id: 'freshness', label: 'Freshness QA', Component: FreshnessQA }
];

const swipeVariants = {
  enter: (direction) => ({
    x: direction >= 0 ? '100%' : '-100%',
    opacity: 0,
    position: 'absolute'
  }),
  center: {
    x: '0%',
    opacity: 1,
    position: 'relative'
  },
  exit: (direction) => ({
    x: direction >= 0 ? '-100%' : '100%',
    opacity: 0,
    position: 'absolute'
  })
};

function App() {
  const [activeTab, setActiveTab] = useState(tabs[0].id);
  const [direction, setDirection] = useState(0);

  const activeIndex = tabs.findIndex((tab) => tab.id === activeTab);
  const safeIndex = activeIndex === -1 ? 0 : activeIndex;

  const ActiveComponent = useMemo(
    () => tabs[safeIndex]?.Component ?? PlanCard,
    [safeIndex]
  );

  const goToTabIndex = (targetIndex) => {
    if (targetIndex < 0 || targetIndex >= tabs.length || targetIndex === safeIndex) {
      return;
    }

    setDirection(targetIndex > safeIndex ? 1 : -1);
    setActiveTab(tabs[targetIndex].id);
  };

  const handleTabSelect = (tabId) => {
    const targetIndex = tabs.findIndex((tab) => tab.id === tabId);
    if (targetIndex === -1) {
      return;
    }

    goToTabIndex(targetIndex);
  };

  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => goToTabIndex(safeIndex + 1),
    onSwipedRight: () => goToTabIndex(safeIndex - 1),
    trackTouch: true,
    trackMouse: true,
    delta: 10
  });

  return (
    <div className="App">
      <header className="app-header">
        <h1>LEVIATHAN</h1>
        <p>Bringing big insights for small crews</p>
      </header>

      <nav className="tab-navigation">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            aria-pressed={activeTab === tab.id}
            onClick={() => handleTabSelect(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="main-content">
        <div className="swipe-container" {...swipeHandlers}>
          <AnimatePresence initial={false} custom={direction} mode="wait">
            <motion.div
              key={activeTab}
              className="tab-panel"
              custom={direction}
              variants={swipeVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.28, ease: 'easeInOut' }}
            >
              <ActiveComponent />
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

export default App;