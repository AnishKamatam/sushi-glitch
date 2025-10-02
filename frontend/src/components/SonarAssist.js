import React, { useCallback, useRef, useState, useEffect } from 'react';
import './SonarAssist.css';
import { getApiService } from '../services/api';
import {
  MdRadar,
  MdLocationOn,
  MdAccessTime,
  MdUpload,
  MdSearch,
  MdClose,
  MdVolumeUp,
  MdTrendingUp
} from 'react-icons/md';
import {
  FaFish,
  FaArrowDown,
  FaBrain,
  FaChartArea,
  FaLayerGroup
} from 'react-icons/fa';
import { GiRadarSweep } from 'react-icons/gi';
import WAVES from 'vanta/dist/vanta.waves.min';
import * as THREE from 'three';

const api = getApiService();

const SonarAssist = () => {
  const [sonarImage, setSonarImage] = useState(null);
  const [reading, setReading] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isVideo, setIsVideo] = useState(false);
  const [videoRef, setVideoRef] = useState(null);
  const [liveCallouts, setLiveCallouts] = useState([]);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [currentDepth, setCurrentDepth] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const fileInputRef = useRef(null);
  const canvasRef = useRef(null);
  const vantaRef = useRef(null);
  const vantaEffect = useRef(null);

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Initialize Vanta.js background
  useEffect(() => {
    if (!sonarImage && vantaRef.current && !vantaEffect.current) {
      vantaEffect.current = WAVES({
        el: vantaRef.current,
        THREE: THREE,
        mouseControls: true,
        touchControls: true,
        gyroControls: false,
        minHeight: 200.00,
        minWidth: 200.00,
        scale: 1.00,
        scaleMobile: 1.00,
        color: 0x0a1929,
        shininess: 30.00,
        waveHeight: 15.00,
        waveSpeed: 0.75,
        zoom: 0.85
      });
    }
    return () => {
      if (vantaEffect.current) {
        vantaEffect.current.destroy();
        vantaEffect.current = null;
      }
    };
  }, [sonarImage]);

  // Get location
  useEffect(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCurrentLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.log('Location access denied or unavailable');
        }
      );
    }
  }, []);

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
      setCurrentDepth(normalizedReading.depth || normalizedReading.bottomDepth);

      // Create live callouts
      const callouts = [];
      if (normalizedReading.detectedObjects?.fish_arches > 0) {
        callouts.push({
          id: Date.now() + 1,
          text: `${normalizedReading.detectedObjects.fish_arches} fish detected`,
          timestamp: new Date(),
          type: 'fish'
        });
      }
      if (normalizedReading.density && normalizedReading.density !== 'unknown') {
        callouts.push({
          id: Date.now() + 2,
          text: `${normalizedReading.density.toUpperCase()} school density`,
          timestamp: new Date(),
          type: 'density'
        });
      }
      if (normalizedReading.speciesGuess) {
        callouts.push({
          id: Date.now() + 3,
          text: `Likely ${normalizedReading.speciesGuess}`,
          timestamp: new Date(),
          type: 'species'
        });
      }
      setLiveCallouts(callouts);

      // Use ElevenLabs TTS instead of browser speech synthesis
      if (normalizedReading.recommendation) {
        try {
          const audioBlob = await api.synthesizeSpeech(normalizedReading.recommendation);
          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          audio.play();

          // Store for replay functionality
          window.lastAudioUrl = audioUrl;
        } catch (ttsError) {
          console.error('TTS error:', ttsError);
          // Fallback to browser TTS if ElevenLabs fails
          if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(normalizedReading.recommendation);
            utterance.rate = 0.9;
            utterance.pitch = 1.0;
            speechSynthesis.speak(utterance);
          }
        }
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
      const videoUrl = URL.createObjectURL(file);
      setSonarImage(videoUrl);
    } else {
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
    setLiveCallouts([]);

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

  const repeatAudio = async () => {
    if (!reading?.recommendation) return;

    // Try to replay stored audio first
    if (window.lastAudioUrl) {
      const audio = new Audio(window.lastAudioUrl);
      audio.play();
      return;
    }

    // Otherwise, request new audio from ElevenLabs
    try {
      const audioBlob = await api.synthesizeSpeech(reading.recommendation);
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play();
      window.lastAudioUrl = audioUrl;
    } catch (error) {
      console.error('Replay audio error:', error);
      // Fallback to browser TTS
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(reading.recommendation);
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        speechSynthesis.speak(utterance);
      }
    }
  };

  const captureVideoFrame = () => {
    const videoElement = document.querySelector('video.sonar-feed-image');
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
      {/* Live Status Bar */}
      <div className="live-status-bar">
        <div className="status-indicator">
          <div className="live-pulse"></div>
          <GiRadarSweep className="status-icon-svg" />
          <span className="live-text">LIVE SONAR FEED</span>
        </div>
        <div className="live-stats">
          {currentLocation && (
            <div className="stat-item">
              <MdLocationOn className="stat-icon-svg" />
              <span className="stat-value">{currentLocation.lat.toFixed(4)}, {currentLocation.lng.toFixed(4)}</span>
            </div>
          )}
          {currentDepth && (
            <div className="stat-item">
              <FaArrowDown className="stat-icon-svg" />
              <span className="stat-value">{currentDepth} ft</span>
            </div>
          )}
          <div className="stat-item">
            <MdAccessTime className="stat-icon-svg" />
            <span className="stat-value">{currentTime.toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      <div className="sonar-container">
        {/* Main Feed Display */}
        <div className="feed-panel">
          <div className="feed-display">
            {!sonarImage ? (
              <div
                className={`drop-area ${isDragging ? 'drag-over' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <div ref={vantaRef} className="empty-feed">
                  <div className="drop-overlay">
                    <MdRadar className="drop-icon" />
                    <div className="drop-text">Connect Sonar Feed</div>
                    <div className="drop-hint">Upload sonar image/video to simulate live feed</div>
                  </div>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,video/*"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
              </div>
            ) : (
              <div className="sonar-feed-container">
                {isVideo ? (
                  <video
                    src={sonarImage}
                    className="sonar-feed-image"
                    controls
                    autoPlay
                    loop
                    muted
                    playsInline
                  />
                ) : (
                  <img src={sonarImage} alt="Sonar" className="sonar-feed-image" />
                )}

                {/* Live Callouts Overlay */}
                {liveCallouts.length > 0 && (
                  <div className="callouts-overlay">
                    {liveCallouts.map((callout) => (
                      <div key={callout.id} className={`live-callout ${callout.type}`}>
                        <div className="callout-pulse"></div>
                        <span className="callout-text">{callout.text}</span>
                      </div>
                    ))}
                  </div>
                )}

                {isAnalyzing && (
                  <div className="analyzing-overlay">
                    <div className="spinner"></div>
                    <div className="analyzing-text">AI ANALYZING...</div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Feed Controls */}
          <div className="feed-controls">
            <button
              className="control-btn upload-btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={isAnalyzing}
              title="Upload sonar data"
            >
              <MdUpload />
              <span>{sonarImage ? 'Upload New Feed' : 'Upload Feed'}</span>
            </button>
            {isVideo && sonarImage && (
              <button
                className="control-btn analyze-btn"
                onClick={captureVideoFrame}
                disabled={isAnalyzing}
                title="Analyze current frame"
              >
                <MdSearch />
                <span>Analyze Frame</span>
              </button>
            )}
            {sonarImage && (
              <button
                className="control-btn clear-btn"
                onClick={clearAll}
                disabled={isAnalyzing}
                title="Disconnect feed"
              >
                <MdClose />
                <span>Disconnect</span>
              </button>
            )}
          </div>
        </div>

        {/* Right Panel - Live Analysis */}
        <div className="analysis-panel">
          <div className="panel-header">
            <h3 className="panel-title">
              <FaBrain className="panel-icon" />
              AI ASSISTANT
            </h3>
            {typeof reading?.confidence === 'number' && (
              <div className="confidence-badge">
                {Math.round(reading.confidence * 100)}% AI
              </div>
            )}
          </div>

          {error && (
            <div className="error-banner">
              <MdClose className="error-icon" />
              {error}
            </div>
          )}

          {!reading && !error && (
            <div className="empty-state">
              <GiRadarSweep className="empty-state-icon" />
              <div className="empty-state-text">Waiting for sonar data...</div>
              <div className="empty-state-hint">AI will provide real-time callouts when feed is active</div>
            </div>
          )}

          {reading && (
            <>
              {/* Quick Metrics */}
              <div className="quick-metrics">
                <div className="quick-metric">
                  <FaFish className="metric-icon" />
                  <div className="metric-info">
                    <span className="metric-number">{reading.detectedObjects?.fish_arches || 0}</span>
                    <span className="metric-text">Fish</span>
                  </div>
                </div>

                <div className="quick-metric">
                  <FaArrowDown className="metric-icon" />
                  <div className="metric-info">
                    <span className="metric-number">{reading.depth || reading.bottomDepth || 0}</span>
                    <span className="metric-text">Depth (ft)</span>
                  </div>
                </div>

                <div className="quick-metric">
                  <span
                    className="metric-icon density-indicator"
                    style={{ color: getDensityColor(reading.density) }}
                  >
                    <MdTrendingUp />
                  </span>
                  <div className="metric-info">
                    <span className="metric-number">{reading.density?.toUpperCase() || 'N/A'}</span>
                    <span className="metric-text">Density</span>
                  </div>
                </div>
              </div>

              {/* Fish Intelligence Section */}
              {(reading.speciesGuess || reading.fishSize || reading.fishBehavior || reading.baitfishPresent !== undefined) && (
                <div className="analysis-section">
                  <h4 className="section-header">
                    <FaFish className="section-icon" />
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
                    <FaLayerGroup className="section-icon" />
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

              {/* AI Recommendation Section */}
              <div className="ai-recommendation">
                <h4 className="ai-header">
                  <FaChartArea className="ai-icon" />
                  AI Analysis
                </h4>
                <div className="recommendation-content">
                  <p className="recommendation-text">
                    {reading.recommendation.split('\n').map((line, index) => (
                      <span key={index}>
                        {line}
                        {index < reading.recommendation.split('\n').length - 1 && <br />}
                      </span>
                    ))}
                  </p>
                </div>
                <button className="audio-replay-btn" onClick={repeatAudio}>
                  <MdVolumeUp />
                  <span>Replay Audio Callout</span>
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
