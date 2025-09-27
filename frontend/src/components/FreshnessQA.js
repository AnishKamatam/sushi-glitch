import React, { useState, useRef } from 'react';
import './FreshnessQA.css';

const FreshnessQA = () => {
  const [capturedImage, setCapturedImage] = useState(null);
  const [score, setScore] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [scores, setScores] = useState([]);
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [cameraActive, setCameraActive] = useState(false);

  const mockFreshnessAnalysis = () => {
    const mockScores = [
      {
        bleeding: 95,
        iceContact: 88,
        bruising: 92,
        overall: 92,
        grade: 'A',
        nextAction: "Excellent! Continue current handling. Move to ice storage.",
        timestamp: new Date().toLocaleTimeString()
      },
      {
        bleeding: 78,
        iceContact: 65,
        bruising: 85,
        overall: 76,
        grade: 'B',
        nextAction: "Good bleeding. Improve ice contact - add more ice around gills.",
        timestamp: new Date().toLocaleTimeString()
      },
      {
        bleeding: 60,
        iceContact: 45,
        bruising: 70,
        overall: 58,
        grade: 'C',
        nextAction: "Re-bleed fish and pack with fresh ice immediately.",
        timestamp: new Date().toLocaleTimeString()
      }
    ];
    return mockScores[Math.floor(Math.random() * mockScores.length)];
  };

  const handleImageUpload = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setCapturedImage(e.target?.result);
        analyzeFreshness();
      };
      reader.readAsDataURL(file);
    }
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setCameraActive(true);
      }
    } catch (error) {
      alert('Camera access denied or not available');
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      const context = canvas.getContext('2d');

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      if (context) {
        context.drawImage(video, 0, 0);
        const imageData = canvas.toDataURL('image/jpeg');
        setCapturedImage(imageData);
        stopCamera();
        analyzeFreshness();
      }
    }
  };

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      setCameraActive(false);
    }
  };

  const analyzeFreshness = () => {
    setIsAnalyzing(true);
    setScore(null);

    setTimeout(() => {
      const analysis = mockFreshnessAnalysis();
      setScore(analysis);
      setScores(prev => [analysis, ...prev.slice(0, 4)]);
      setIsAnalyzing(false);
    }, 1500);
  };

  const getGradeColor = (grade) => {
    switch (grade) {
      case 'A': return '#16a34a';
      case 'B': return '#65a30d';
      case 'C': return '#eab308';
      case 'D': return '#dc2626';
      default: return '#6b7280';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 90) return '#16a34a';
    if (score >= 75) return '#65a30d';
    if (score >= 60) return '#eab308';
    return '#dc2626';
  };

  return (
    <div className="freshness-qa">
      <div className="freshness-header">
        <h2>Freshness QA</h2>
        <p>AI-powered freshness assessment for optimal market value</p>
      </div>

      <div className="capture-section">
        <div className="capture-buttons">
          <button
            className="btn btn-primary"
            onClick={startCamera}
            disabled={cameraActive}
          >
            Start Camera
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => fileInputRef.current?.click()}
          >
            Upload Photo
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

      {cameraActive && (
        <div className="camera-section">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="camera-feed"
          />
          <div className="camera-controls">
            <button className="btn btn-primary" onClick={capturePhoto}>
              Capture
            </button>
            <button className="btn btn-secondary" onClick={stopCamera}>
              Cancel
            </button>
          </div>
        </div>
      )}

      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {capturedImage && (
        <div className="image-display">
          <div className="image-container">
            <img src={capturedImage} alt="Fish for analysis" className="captured-image" />
            {isAnalyzing && (
              <div className="analyzing-overlay">
                <div className="spinner"></div>
                <p>Analyzing freshness...</p>
              </div>
            )}
          </div>
        </div>
      )}

      {score && (
        <div className="analysis-results">
          <div className="score-header">
            <h3>Freshness Analysis</h3>
            <div
              className="grade-badge"
              style={{ backgroundColor: getGradeColor(score.grade) }}
            >
              Grade {score.grade}
            </div>
          </div>

          <div className="score-grid">
            <div className="score-item">
              <span className="label">Bleeding</span>
              <div className="score-bar">
                <div
                  className="score-fill"
                  style={{
                    width: `${score.bleeding}%`,
                    backgroundColor: getScoreColor(score.bleeding)
                  }}
                ></div>
              </div>
              <span className="score-value">{score.bleeding}%</span>
            </div>

            <div className="score-item">
              <span className="label">Ice Contact</span>
              <div className="score-bar">
                <div
                  className="score-fill"
                  style={{
                    width: `${score.iceContact}%`,
                    backgroundColor: getScoreColor(score.iceContact)
                  }}
                ></div>
              </div>
              <span className="score-value">{score.iceContact}%</span>
            </div>

            <div className="score-item">
              <span className="label">Bruising</span>
              <div className="score-bar">
                <div
                  className="score-fill"
                  style={{
                    width: `${score.bruising}%`,
                    backgroundColor: getScoreColor(score.bruising)
                  }}
                ></div>
              </div>
              <span className="score-value">{score.bruising}%</span>
            </div>

            <div className="score-item overall">
              <span className="label">Overall</span>
              <div className="score-bar">
                <div
                  className="score-fill"
                  style={{
                    width: `${score.overall}%`,
                    backgroundColor: getScoreColor(score.overall)
                  }}
                ></div>
              </div>
              <span className="score-value">{score.overall}%</span>
            </div>
          </div>

          <div className="next-action">
            <h4>Next Action</h4>
            <p>{score.nextAction}</p>
          </div>
        </div>
      )}

      {scores.length > 0 && (
        <div className="score-history">
          <h3>Recent Scores</h3>
          <div className="history-list">
            {scores.map((s, index) => (
              <div key={index} className="history-item">
                <div className="history-time">{s.timestamp}</div>
                <div
                  className="history-grade"
                  style={{ backgroundColor: getGradeColor(s.grade) }}
                >
                  {s.grade}
                </div>
                <div className="history-score">{s.overall}%</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="freshness-tips">
        <h3>Freshness Tips</h3>
        <ul>
          <li>Bleed fish immediately after catch</li>
          <li>Keep fish in direct contact with ice</li>
          <li>Avoid dropping or rough handling</li>
          <li>Check freshness every 30 minutes</li>
        </ul>
      </div>
    </div>
  );
};

export default FreshnessQA;