import React, { useState, useRef } from 'react';
import './SonarAssist.css';

const SonarAssist = () => {
  const [sonarImage, setSonarImage] = useState(null);
  const [reading, setReading] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const fileInputRef = useRef(null);

  const mockSonarAnalysis = () => {
    const mockReadings = [
      {
        depth: 85,
        density: 'high',
        schoolWidth: 'wide',
        confidence: 0.92,
        recommendation: "Strong school detected! Drop lines now at 80-90ft."
      },
      {
        depth: 45,
        density: 'medium',
        schoolWidth: 'narrow',
        confidence: 0.78,
        recommendation: "Medium activity. Try slow trolling through area."
      },
      {
        depth: 120,
        density: 'low',
        schoolWidth: 'medium',
        confidence: 0.65,
        recommendation: "Light activity at depth. Consider moving to shallower water."
      }
    ];
    return mockReadings[Math.floor(Math.random() * mockReadings.length)];
  };

  const handleImageUpload = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSonarImage(e.target?.result);
        analyzeSonar();
      };
      reader.readAsDataURL(file);
    }
  };

  const analyzeSonar = () => {
    setIsAnalyzing(true);
    setReading(null);

    setTimeout(() => {
      const analysis = mockSonarAnalysis();
      setReading(analysis);
      setIsAnalyzing(false);

      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(analysis.recommendation);
        utterance.rate = 0.9;
        utterance.pitch = 1.1;
        speechSynthesis.speak(utterance);
      }
    }, 2000);
  };

  const handleCameraCapture = () => {
    alert('Camera capture would open device camera to take sonar screen photo');
  };

  const getDensityColor = (density) => {
    switch (density) {
      case 'high': return '#16a34a';
      case 'medium': return '#eab308';
      case 'low': return '#dc2626';
      default: return '#6b7280';
    }
  };

  return (
    <div className="sonar-assist">
      <div className="sonar-header">
        <h2>Sonar Assist</h2>
        <p>Upload sonar screenshots for AI-powered fish detection</p>
      </div>

      <div className="upload-section">
        <div className="upload-buttons">
          <button
            className="btn btn-primary"
            onClick={() => fileInputRef.current?.click()}
          >
            Upload Sonar Image
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleCameraCapture}
          >
            Capture Screen
          </button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          style={{ display: 'none' }}
        />
      </div>

      {sonarImage && (
        <div className="sonar-display">
          <div className="image-container">
            <img src={sonarImage} alt="Sonar reading" className="sonar-image" />
            {isAnalyzing && (
              <div className="analyzing-overlay">
                <div className="spinner"></div>
                <p>Analyzing sonar data...</p>
              </div>
            )}
          </div>
        </div>
      )}

      {reading && (
        <div className="analysis-results">
          <div className="reading-header">
            <h3>Analysis Results</h3>
            <div className="confidence-badge">
              Confidence: {Math.round(reading.confidence * 100)}%
            </div>
          </div>

          <div className="reading-grid">
            <div className="reading-item">
              <span className="label">Depth</span>
              <span className="value">{reading.depth} ft</span>
            </div>
            <div className="reading-item">
              <span className="label">Density</span>
              <span
                className="value density-badge"
                style={{ backgroundColor: getDensityColor(reading.density) }}
              >
                {reading.density.toUpperCase()}
              </span>
            </div>
            <div className="reading-item">
              <span className="label">School Size</span>
              <span className="value">{reading.schoolWidth.toUpperCase()}</span>
            </div>
          </div>

          <div className="recommendation">
            <h4>Recommendation</h4>
            <p>{reading.recommendation}</p>
            <button
              className="btn btn-accent"
              onClick={() => {
                if ('speechSynthesis' in window) {
                  const utterance = new SpeechSynthesisUtterance(reading.recommendation);
                  speechSynthesis.speak(utterance);
                }
              }}
            >
              Repeat Audio
            </button>
          </div>
        </div>
      )}

      <div className="sonar-tips">
        <h3>Tips</h3>
        <ul>
          <li>Take clear photos of your sonar screen</li>
          <li>Include depth markers and fish arches</li>
          <li>Audio cues will speak automatically</li>
          <li>Works with most sonar units and fish finders</li>
        </ul>
      </div>
    </div>
  );
};

export default SonarAssist;