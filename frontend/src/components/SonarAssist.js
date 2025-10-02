import React, { useCallback, useRef, useState } from 'react';
import './SonarAssist.css';
import { getApiService } from '../services/api';

const api = getApiService();

const SonarAssist = () => {
  const [sonarImage, setSonarImage] = useState(null);
  const [reading, setReading] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isVideo, setIsVideo] = useState(false);
  const [videoRef, setVideoRef] = useState(null);
  const fileInputRef = useRef(null);
  const canvasRef = useRef(null);

  const resetState = useCallback(() => {
    setReading(null);
    setError(null);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file && (file.type.startsWith('image/') || file.type.startsWith('video/'))) {
      processFile(file);
    }
  }, []);

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  }, []);

  const analyzeSonar = async (imageDataUrl) => {
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
        detectedObjects: result?.detected_objects ?? {},
        bottomType: result?.bottom_type,
        bottomDepth: result?.bottom_depth,
        fishSize: result?.fish_size,
        fishBehavior: result?.fish_behavior,
        baitfishPresent: result?.baitfish_present,
        speciesGuess: result?.species_guess,
      };

      setReading(normalizedReading);

      if (normalizedReading.recommendation && 'speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(normalizedReading.recommendation);
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        speechSynthesis.speak(utterance);
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to analyze sonar image');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const processFile = useCallback(async (file) => {
    const isVideoFile = file.type.startsWith('video/');
    setIsVideo(isVideoFile);

    if (isVideoFile) {
      // Handle video file - just display it, don't analyze yet
      const videoUrl = URL.createObjectURL(file);
      setSonarImage(videoUrl);
    } else {
      // Handle image file
      const reader = new FileReader();
      reader.onload = async (e) => {
        const dataUrl = e.target?.result;
        if (!dataUrl || typeof dataUrl !== 'string') {
          setError('Unable to read image file');
          return;
        }

        setSonarImage(dataUrl);
        await analyzeSonar(dataUrl);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const clearAll = useCallback(() => {
    // Stop any playing video
    if (videoRef) {
      videoRef.pause();
      if (videoRef.src) {
        URL.revokeObjectURL(videoRef.src);
      }
    }

    setSonarImage(null);
    setReading(null);
    setError(null);
    setIsVideo(false);
    setVideoRef(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [videoRef]);

  const getDensityColor = (density) => {
    const normalized = density?.toLowerCase();
    switch (normalized) {
      case 'dense': return '#16a34a';
      case 'moderate': return '#eab308';
      case 'sparse': return '#dc2626';
      default: return '#6b7280';
    }
  };

  const repeatAudio = () => {
    if (reading?.recommendation && 'speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(reading.recommendation);
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      speechSynthesis.speak(utterance);
    }
  };

  const captureVideoFrame = () => {
    // Get the video element from the DOM
    const videoElement = document.querySelector('video.sonar-preview-image');
    if (!videoElement || !isVideo) return;

    const canvas = canvasRef.current || document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoElement, 0, 0);

    const frameDataUrl = canvas.toDataURL('image/jpeg');
    analyzeSonar(frameDataUrl);
  };

  return (
    <div className="sonar-assist">
      <div className="sonar-container">
        {/* Left Panel - Upload */}
        <div className="upload-panel">
          <div className="panel-header">
            <h2 className="panel-title">Upload Sonar</h2>
            <p className="panel-subtitle">Analyze fishfinder screenshots with AI</p>
          </div>

          <div className="upload-zone">
            {!sonarImage ? (
              <div
                className={`drop-area ${isDragging ? 'drag-over' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="drop-icon">↑</div>
                <div className="drop-text">Click or drag media here</div>
                <div className="drop-hint">Supports images (JPG, PNG) and videos (MP4, MOV)</div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,video/*"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
              </div>
            ) : (
              <div className="image-preview-container">
                {isVideo ? (
                  <video
                    src={sonarImage}
                    className="sonar-preview-image"
                    controls
                    autoPlay
                    loop
                    muted
                    playsInline
                  />
                ) : (
                  <img src={sonarImage} alt="Sonar" className="sonar-preview-image" />
                )}
                {isAnalyzing && (
                  <div className="analyzing-overlay">
                    <div className="spinner"></div>
                    <div className="analyzing-text">Analyzing sonar data...</div>
                  </div>
                )}
              </div>
            )}

            <div className="action-buttons">
              {isVideo && sonarImage && (
                <button
                  className="btn btn-primary"
                  onClick={captureVideoFrame}
                  disabled={isAnalyzing}
                >
                  Analyze Frame
                </button>
              )}
              {sonarImage && (
                <button
                  className="btn btn-secondary"
                  onClick={clearAll}
                  disabled={isAnalyzing}
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right Panel - Results */}
        <div className="results-panel">
          {error && (
            <div className="error-banner">
              ⚠ {error}
            </div>
          )}

          {!reading && !error && (
            <div className="empty-state">
              <div className="empty-state-icon">⌁</div>
              <div className="empty-state-text">Upload a sonar image to begin analysis</div>
            </div>
          )}

          {reading && (
            <>
              <div className="results-header">
                <h3 className="results-title">Analysis Results</h3>
                {typeof reading.confidence === 'number' && (
                  <div className="confidence-badge">
                    {Math.round(reading.confidence * 100)}% Confidence
                  </div>
                )}
              </div>

              {/* Metrics Grid */}
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Fish Detected</div>
                  <div className="metric-value">
                    {reading.detectedObjects?.fish_arches || 0}
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-label">Fish Depth</div>
                  <div className="metric-value">
                    {reading.depth || 0}
                    <span className="metric-unit">ft</span>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-label">School Density</div>
                  <div
                    className="density-badge"
                    style={{ backgroundColor: getDensityColor(reading.density) }}
                  >
                    {reading.density?.toUpperCase() || 'UNKNOWN'}
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-label">School Width</div>
                  <div className="metric-value" style={{ fontSize: '1.3rem' }}>
                    {reading.schoolWidth || 'Unknown'}
                  </div>
                </div>
              </div>

              {/* Fish Intelligence Section */}
              {(reading.speciesGuess || reading.fishSize || reading.fishBehavior || reading.baitfishPresent !== undefined) && (
                <div className="analysis-section">
                  <h4 className="section-header">
                    <span className="section-icon">◈</span>
                    Fish Intelligence
                  </h4>
                  <div className="info-list">
                    {reading.speciesGuess && (
                      <div className="info-item">
                        <span className="info-label">Species Likely</span>
                        <span className="info-value">{reading.speciesGuess}</span>
                      </div>
                    )}
                    {reading.fishSize && (
                      <div className="info-item">
                        <span className="info-label">Fish Size</span>
                        <span className="info-value">{reading.fishSize.toUpperCase()}</span>
                      </div>
                    )}
                    {reading.fishBehavior && (
                      <div className="info-item">
                        <span className="info-label">Behavior</span>
                        <span className="info-value">{reading.fishBehavior.toUpperCase()}</span>
                      </div>
                    )}
                    {reading.baitfishPresent !== undefined && (
                      <div className="info-item">
                        <span className="info-label">Baitfish Present</span>
                        <span className="info-value">{reading.baitfishPresent ? 'Yes' : 'No'}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Structure & Environment Section */}
              {(reading.bottomType || reading.bottomDepth || reading.detectedObjects?.thermocline || reading.detectedObjects?.bottom_structure !== undefined) && (
                <div className="analysis-section">
                  <h4 className="section-header">
                    <span className="section-icon">◊</span>
                    Structure & Environment
                  </h4>
                  <div className="info-list">
                    {reading.bottomType && (
                      <div className="info-item">
                        <span className="info-label">Bottom Type</span>
                        <span className="info-value">{reading.bottomType.toUpperCase()}</span>
                      </div>
                    )}
                    {reading.bottomDepth && (
                      <div className="info-item">
                        <span className="info-label">Bottom Depth</span>
                        <span className="info-value">{reading.bottomDepth} ft</span>
                      </div>
                    )}
                    {reading.detectedObjects?.thermocline && (
                      <div className="info-item">
                        <span className="info-label">Thermocline</span>
                        <span className="info-value">{reading.detectedObjects.thermocline} ft</span>
                      </div>
                    )}
                    {reading.detectedObjects?.bottom_structure !== undefined && (
                      <div className="info-item">
                        <span className="info-label">Bottom Structure</span>
                        <span className="info-value">{reading.detectedObjects.bottom_structure ? 'Detected' : 'None'}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Recommendation Section */}
              <div className="recommendation-section">
                <h4 className="recommendation-header">Recommendation</h4>
                <p className="recommendation-text">
                  {reading.recommendation.split('\n').map((line, index) => (
                    <span key={index}>
                      {line}
                      {index < reading.recommendation.split('\n').length - 1 && <br />}
                    </span>
                  ))}
                </p>
                <button className="audio-button" onClick={repeatAudio}>
                  Repeat Audio
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default SonarAssist;
