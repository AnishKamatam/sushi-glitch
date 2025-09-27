import React from 'react';
import './PlanCard.css';

const PlanCard = () => {
  const mockPlanData = {
    targetSpecies: "Rockfish, Lingcod",
    depthBand: "80-120 ft",
    timeWindow: "Dawn + 2hrs (5:30-7:30 AM)",
    areaHint: "North reef structure, 2nm offshore",
    conditions: {
      windSpeed: 8,
      windDirection: "NW",
      waveHeight: 2.5,
      tide: "Rising",
      lunar: "New moon"
    },
    fuelNotes: "15 gal estimated for 6hr trip",
    safetyNotes: "VHF Channel 16, EPIRB active",
    planB: "Shallow water halibut (40-60ft) if conditions worsen"
  };

  return (
    <div className="plan-card">
      <div className="plan-header">
        <h2>Today's Plan</h2>
        <div className="plan-status">
          <span className="status-indicator good">Conditions: Good</span>
        </div>
      </div>

      <div className="plan-grid">
        <div className="plan-section primary-target">
          <h3>Primary Target</h3>
          <div className="target-info">
            <p><strong>Species:</strong> {mockPlanData.targetSpecies}</p>
            <p><strong>Depth:</strong> {mockPlanData.depthBand}</p>
            <p><strong>Best Time:</strong> {mockPlanData.timeWindow}</p>
            <p><strong>Area:</strong> {mockPlanData.areaHint}</p>
          </div>
        </div>

        <div className="plan-section conditions">
          <h3>Marine Conditions</h3>
          <div className="conditions-grid">
            <div className="condition-item">
              <span className="label">Wind:</span>
              <span className="value">{mockPlanData.conditions.windSpeed} kt {mockPlanData.conditions.windDirection}</span>
            </div>
            <div className="condition-item">
              <span className="label">Waves:</span>
              <span className="value">{mockPlanData.conditions.waveHeight} ft</span>
            </div>
            <div className="condition-item">
              <span className="label">Tide:</span>
              <span className="value">{mockPlanData.conditions.tide}</span>
            </div>
            <div className="condition-item">
              <span className="label">Moon:</span>
              <span className="value">{mockPlanData.conditions.lunar}</span>
            </div>
          </div>
        </div>

        <div className="plan-section logistics">
          <h3>Logistics</h3>
          <p><strong>Fuel:</strong> {mockPlanData.fuelNotes}</p>
          <p><strong>Safety:</strong> {mockPlanData.safetyNotes}</p>
        </div>

        <div className="plan-section plan-b">
          <h3>Plan B</h3>
          <p>{mockPlanData.planB}</p>
        </div>
      </div>

      <div className="plan-actions">
        <button className="btn btn-primary">Start Trip Log</button>
        <button className="btn btn-secondary">Update Conditions</button>
      </div>
    </div>
  );
};

export default PlanCard;