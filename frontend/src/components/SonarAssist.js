import React, { useCallback, useRef, useState } from 'react';
import './SonarAssist.css';
import { getApiService } from '../services/api';

const api = getApiService();

const SonarAssist = () => {
  const [sonarImage, setSonarImage] = useState(null);
  const [reading, setReading] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const resetState = useCallback(() => {
    setReading(null);
    setError(null);
  }, []);

  const handleImageUpload = useCallback(async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = async (e) => {
      const dataUrl = e.target?.result;
      if (!dataUrl || typeof dataUrl !== 'string') {
        setError('Unable to read image file.');
        return;
      }

      setSonarImage(dataUrl);
      await analyzeSonar(dataUrl);
    };
    reader.readAsDataURL(file);
  }, []);

  const analyzeSonar = useCallback(async (imageDataUrl) => {
    resetState();
    setIsAnalyzing(true);

    try {
      const result = await api.analyzeSonar({
        image: imageDataUrl,
        sonar_type: 'image_upload',
      });

      const normalizedReading = {
        depth: result?.depth ?? 0,
        density: result?.density ?? 'unknown',
        schoolWidth: result?.school_width ?? result?.schoolWidth ?? 'unknown',
        confidence: typeof result?.confidence === 'number' ? result.confidence : null,
        recommendation: result?.recommendation ?? 'No recommendation returned.',
      };

      setReading(normalizedReading);

      if (normalizedReading.recommendation && 'speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(normalizedReading.recommendation);
        utterance.rate = 0.9;
        utterance.pitch = 1.1;
        speechSynthesis.speak(utterance);
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to analyze sonar image.');
    } finally {
      setIsAnalyzing(false);
    }
  }, [resetState]);

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
          <button
            className="btn btn-secondary"
            onClick={() => fileInputRef.current?.click()}
          >
            Upload Image
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

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      {reading && (
        <div className="analysis-results">
          <div className="reading-header">
            <h3>Analysis Results</h3>
            {typeof reading.confidence === 'number' && (
              <div className="confidence-badge">
                Confidence: {Math.round(reading.confidence * 100)}%
              </div>
            )}
          </div>

          <div className="reading-grid">
            <div className="reading-item">
              <span className="label">Depth</span>
              <span className="value">{reading.depth || 0} ft</span>
            </div>
            <div className="reading-item">
              <span className="label">Density</span>
              <span
                className="value density-badge"
                style={{ backgroundColor: getDensityColor(reading.density) }}
              >
                {reading.density?.toUpperCase?.() || 'UNKNOWN'}
              </span>
            </div>
            <div className="reading-item">
              <span className="label">School Size</span>
              <span className="value">{reading.schoolWidth?.toUpperCase?.() || 'UNKNOWN'}</span>
            </div>
          </div>

          <div className="recommendation">
            <h4>Recommendation</h4>
            <p className="recommendation-text">
              {reading.recommendation.split('\n').map((line, index) => (
                <span key={index}>
                  {line}
                  {index < reading.recommendation.split('\n').length - 1 && <br />}
                </span>
              ))}
            </p>
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