import React, { useEffect, useMemo, useRef, useState } from 'react';
import './FreshnessQA.css';
import { storageService } from '../services/storage';

const BLEEDING_GUIDE = {
  excellent: 'Gills flushed, belly clean, no residual blood pooling.',
  good: 'Gills draining, minor pooling around belly. Stay attentive.',
  poor: 'Dark blood at gills/belly. Rinse and re-bleed ASAP.'
};

const ICE_GUIDE = {
  excellent: 'Full flank contact with shaved ice, cavity packed.',
  good: 'Partial flank contact. Pack more ice around shoulders.',
  poor: 'Gaps along lateral line. Repack with slurry or fresh ice.'
};

const BRUISING_GUIDE = {
  excellent: 'No visible bruising or dents on fillet zones.',
  good: 'Minor scuffs. Rotate fish and add separator.',
  poor: 'Dark bruises spotted. Separate and ice individually.'
};

const nextActionByGrade = {
  a: 'Excellent capture. Shift to chilled storage and log haul.',
  b: 'Solid baseline. Top off ice at gills and log check-in reminder.',
  c: 'Below target. Re-bleed, add fresh ice, and re-check in 20 minutes. '
    + 'Flag for potential downgrade.',
  d: 'Critical. Call out for inspection, remediate handling, and verify ice supply.'
};

const FreshnessQA = () => {
  const [capturedImage, setCapturedImage] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [history, setHistory] = useState([]);
  const [cameraActive, setCameraActive] = useState(false);
  const [viewMode, setViewMode] = useState('capture');
  const [scoreFocus, setScoreFocus] = useState('overall');
  const [confidence, setConfidence] = useState(null);
  const [selectedHistoryId, setSelectedHistoryId] = useState(null);
  const [isHistoryModalOpen, setHistoryModalOpen] = useState(false);
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const closeHistoryModal = () => {
    setHistoryModalOpen(false);
    setSelectedHistoryId(null);
  };

  const openHistoryModal = (id) => {
    setSelectedHistoryId(id);
    setHistoryModalOpen(true);
  };

  useEffect(() => {
    document.body.style.overflow = isHistoryModalOpen ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [isHistoryModalOpen]);

  useEffect(() => {
    const fetched = storageService.getFreshnessHistory();
    setHistory(fetched);
  }, []);

  useEffect(() => {
    if (!history.length) {
      if (selectedHistoryId !== null) {
        setSelectedHistoryId(null);
      }
      setHistoryModalOpen(false);
      return;
    }

    if (selectedHistoryId !== null && !history.some(entry => entry.id === selectedHistoryId)) {
      setSelectedHistoryId(history[0].id);
    }
  }, [history, selectedHistoryId]);

  useEffect(() => {
    if (!isHistoryModalOpen) {
      return;
    }

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        closeHistoryModal();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isHistoryModalOpen]);

  useEffect(() => {
    if (analysis && analysis.nextAction && 'speechSynthesis' in window) {
      try {
        const utterance = new SpeechSynthesisUtterance(analysis.nextAction);
        utterance.rate = 0.92;
        utterance.pitch = 1.08;
        speechSynthesis.speak(utterance);
      } catch (error) {
        console.warn('TTS unavailable:', error);
      }
    }
  }, [analysis]);

  const guidance = useMemo(() => {
    if (!analysis) {
      return null;
    }

    const gradeKey = analysis.grade?.toLowerCase?.() ?? 'c';
    const bleedingTier = tierForScore(analysis.bleeding);
    const iceTier = tierForScore(analysis.iceContact);
    const bruiseTier = tierForScore(analysis.bruising);

    return {
      bleeding: BLEEDING_GUIDE[bleedingTier],
      iceContact: ICE_GUIDE[iceTier],
      bruising: BRUISING_GUIDE[bruiseTier],
      gradeAction: nextActionByGrade[gradeKey]
    };
  }, [analysis]);

  const mockFreshnessAnalysis = () => {
    const mockScores = [
      {
        bleeding: 96,
        iceContact: 90,
        bruising: 94,
        overall: 94,
        grade: 'A',
        vibrancy: 'Bright eyes, firm flesh',
        handlingNote: 'Handled within 12 min of bleed.',
        nextAction: nextActionByGrade.a,
        timestamp: new Date().toISOString()
      },
      {
        bleeding: 78,
        iceContact: 71,
        bruising: 80,
        overall: 76,
        grade: 'B',
        vibrancy: 'Clear eyes, mild belly discoloration',
        handlingNote: 'Check belly cavity for ice pooling.',
        nextAction: nextActionByGrade.b,
        timestamp: new Date().toISOString()
      },
      {
        bleeding: 63,
        iceContact: 56,
        bruising: 68,
        overall: 61,
        grade: 'C',
        vibrancy: 'Eyes clouding; belly tacky',
        handlingNote: 'Likely delay between bleed and ice.',
        nextAction: nextActionByGrade.c,
        timestamp: new Date().toISOString()
      }
    ];

    return mockScores[Math.floor(Math.random() * mockScores.length)];
  };

  const handleImageUpload = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const imageData = e.target?.result;
      if (!imageData) {
        return;
      }

      setCapturedImage(imageData);
      runAnalysis(imageData);
    };
    reader.readAsDataURL(file);
    setViewMode('analysis');
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setCameraActive(true);
        setViewMode('camera');
      }
    } catch (error) {
      alert('Camera access denied or not available');
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) {
      return;
    }

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const context = canvas.getContext('2d');

    if (!context) {
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);
    const imageData = canvas.toDataURL('image/jpeg');
    setCapturedImage(imageData);
    stopCamera();
    runAnalysis(imageData);
    setViewMode('analysis');
  };

  const stopCamera = () => {
    const stream = videoRef.current?.srcObject;
    if (stream) {
      const tracks = stream.getTracks();
      tracks.forEach(track => track.stop());
    }
    setCameraActive(false);
  };

  const runAnalysis = (imageOverride) => {
    const imageData = imageOverride ?? capturedImage;

    if (!imageData) {
      return;
    }

    if (imageOverride) {
      setCapturedImage(imageOverride);
    }

    setIsAnalyzing(true);
    setAnalysis(null);
    setConfidence(null);

    setTimeout(() => {
      const result = {
        id: `freshness_${Date.now()}`,
        ...mockFreshnessAnalysis()
      };

      const randomConfidence = 0.78 + Math.random() * 0.18;
      const persisted = {
        ...result,
        confidence: randomConfidence,
        checkPoint: buildCheckpointMeta(),
        image: imageData
      };

      storageService.saveFreshnessReading(persisted);
      setHistory(prev => [persisted, ...prev.filter(item => item.id !== persisted.id)]);
      storageService.appendTripEvent({
        type: 'freshness-check',
        capturedAt: new Date().toISOString(),
        meta: {
          score: persisted.overall,
          grade: persisted.grade,
          nextAction: persisted.nextAction,
          image: imageData,
          analysisId: persisted.id
        }
      });

      setAnalysis(persisted);
      setConfidence(randomConfidence);
      setIsAnalyzing(false);
      setSelectedHistoryId(persisted.id);
      if (viewMode === 'history') {
        setHistoryModalOpen(true);
      }
    }, 1700);
  };

  const buildCheckpointMeta = () => {
    const events = storageService.getCurrentTripEvents();
    const order = events.length + 1;
    return {
      eventIndex: order,
      deckPhase: order <= 1 ? 'initial bleed' : order <= 3 ? 'cooling cycle' : 'holding',
      reminderOffsetMinutes: 30
    };
  };

  function tierForScore(value) {
    if (value >= 90) {
      return 'excellent';
    }
    if (value >= 75) {
      return 'good';
    }
    return 'poor';
  }

  const gradeColor = (grade) => {
    switch (grade?.toUpperCase()) {
      case 'A':
        return '#16a34a';
      case 'B':
        return '#65a30d';
      case 'C':
        return '#eab308';
      case 'D':
        return '#dc2626';
      default:
        return '#6b7280';
    }
  };

  const scoreColor = (value) => {
    if (value >= 90) {
      return '#16a34a';
    }
    if (value >= 75) {
      return '#65a30d';
    }
    if (value >= 60) {
      return '#eab308';
    }
    return '#dc2626';
  };

  function renderHistory() {
    if (!history.length) {
      return (
        <div className="empty-history">
          <p>No checks logged yet. Run your first assessment to track freshness.</p>
        </div>
      );
    }

    return history.slice(0, 10).map((item) => (
      <div
        key={item.id}
        className={`history-card ${selectedHistoryId === item.id ? 'active' : ''}`}
        onClick={() => openHistoryModal(item.id)}
      >
        <div className="history-card-header">
          <div className="history-grade" style={{ backgroundColor: gradeColor(item.grade) }}>
            {item.grade}
          </div>
          <div className="history-meta">
            <span className="history-time">{formatTimestamp(item.timestamp)}</span>
            <span className="history-score">{item.overall}% overall</span>
          </div>
          <button
            type="button"
            className={`history-thumb ${selectedHistoryId === item.id ? 'active' : ''}`}
            onClick={(event) => {
              event.stopPropagation();
              openHistoryModal(item.id);
            }}
            aria-label="View capture and analysis"
          >
            {item.image ? (
              <img src={item.image} alt="Fish capture thumbnail" />
            ) : (
              <span>View</span>
            )}
          </button>
        </div>
        <div className="history-body">
          <div className="history-scores">
            <span>Bleeding {item.bleeding}%</span>
            <span>Ice {item.iceContact}%</span>
            <span>Bruising {item.bruising}%</span>
          </div>
          <div className="history-note">{item.nextAction}</div>
        </div>
      </div>
    ));
  }

  const selectedHistory = useMemo(
    () => history.find(entry => entry.id === selectedHistoryId) || null,
    [history, selectedHistoryId]
  );

  const renderHistoryDetail = () => {
    if (!selectedHistory) {
      return (
        <div className="history-detail-card placeholder">
          <p>Select a logged check to review the capture and guidance.</p>
        </div>
      );
    }

    const detailGuidance = {
      bleeding: BLEEDING_GUIDE[tierForScore(selectedHistory.bleeding)] ?? '',
      iceContact: ICE_GUIDE[tierForScore(selectedHistory.iceContact)] ?? '',
      bruising: BRUISING_GUIDE[tierForScore(selectedHistory.bruising)] ?? '',
      gradeAction: nextActionByGrade[selectedHistory.grade?.toLowerCase?.() ?? 'c'] ?? ''
    };

    return (
      <>
        <div className="history-detail-image">
          {selectedHistory.image ? (
            <img src={selectedHistory.image} alt="Logged fish" />
          ) : (
            <div className="image-placeholder">No image captured</div>
          )}
        </div>
        <div className="history-detail-info">
          <div className="history-detail-header">
            <div>
              <h4>Freshness Snapshot</h4>
              <span className="timestamp">{formatTimestamp(selectedHistory.timestamp)}</span>
            </div>
            <div className="grade-badge" style={{ backgroundColor: gradeColor(selectedHistory.grade) }}>
              Grade {selectedHistory.grade}
            </div>
          </div>

          <div className="history-detail-scores">
            <div>
              <span className="label">Bleeding</span>
              <span className="value" style={{ color: scoreColor(selectedHistory.bleeding) }}>
                {selectedHistory.bleeding}%
              </span>
            </div>
            <div>
              <span className="label">Ice Contact</span>
              <span className="value" style={{ color: scoreColor(selectedHistory.iceContact) }}>
                {selectedHistory.iceContact}%
              </span>
            </div>
            <div>
              <span className="label">Bruising</span>
              <span className="value" style={{ color: scoreColor(selectedHistory.bruising) }}>
                {selectedHistory.bruising}%
              </span>
            </div>
            <div>
              <span className="label">Overall</span>
              <span className="value" style={{ color: scoreColor(selectedHistory.overall) }}>
                {selectedHistory.overall}%
              </span>
            </div>
          </div>

          <div className="history-detail-guidance">
            <h5>Guidance</h5>
            <ul>
              <li>{detailGuidance.bleeding}</li>
              <li>{detailGuidance.iceContact}</li>
              <li>{detailGuidance.bruising}</li>
              <li>{selectedHistory.nextAction || detailGuidance.gradeAction}</li>
            </ul>
          </div>

          <div className="history-detail-meta">
            <span>
              Deck phase: {selectedHistory.checkPoint?.deckPhase ?? 'not logged'}
            </span>
            <span>
              Event #{selectedHistory.checkPoint?.eventIndex ?? '-'}
            </span>
          </div>
        </div>
      </>
    );
  };

  const formatTimestamp = (isoString) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoString;
    }
  };

  const renderScoreDetail = () => {
    if (!analysis) {
      return null;
    }

    const segments = [
      { key: 'bleeding', label: 'Bleeding' },
      { key: 'iceContact', label: 'Ice Contact' },
      { key: 'bruising', label: 'Bruising' },
      { key: 'overall', label: 'Overall Score' }
    ];

    return segments.map(({ key, label }) => {
      const value = analysis[key];
      const isFocused = scoreFocus === key;

      return (
        <button
          key={key}
          className={`score-chip ${isFocused ? 'focused' : ''}`}
          onClick={() => setScoreFocus(key)}
        >
          <span className="chip-label">{label}</span>
          <span className="chip-value" style={{ color: scoreColor(value) }}>{value}%</span>
        </button>
      );
    });
  };

  const renderScoreNarrative = () => {
    if (!analysis || !guidance) {
      return null;
    }

    switch (scoreFocus) {
      case 'bleeding':
        return guidance.bleeding;
      case 'iceContact':
        return guidance.iceContact;
      case 'bruising':
        return guidance.bruising;
      default:
        return analysis.nextAction ?? guidance.gradeAction;
    }
  };

  function renderConfidence() {
    if (confidence == null) {
      return null;
    }

    const pct = Math.round(confidence * 100);
    return (
      <div className="confidence-indicator">
        Model confidence {pct}% · {pct >= 80 ? 'High' : 'Moderate'} certainty
      </div>
    );
  }

  function resetCapture() {
    setCapturedImage(null);
    setAnalysis(null);
    setViewMode('capture');
    setConfidence(null);
  }

  return (
    <div className="freshness-qa">
      <header className="freshness-header">
        <h2>Freshness QA</h2>
        <p>Offline-ready checkpoint for bleed quality, ice contact, and deck handling.</p>
        {renderConfidence()}
      </header>

      <section className="workflow-switcher">
        <button
          className={`workflow-tab ${viewMode === 'capture' ? 'active' : ''}`}
          onClick={() => setViewMode('capture')}
        >
          Capture
        </button>
        <button
          className={`workflow-tab ${viewMode === 'analysis' ? 'active' : ''}`}
          onClick={() => setViewMode('analysis')}
          disabled={!analysis}
        >
          Review
        </button>
        <button
          className={`workflow-tab ${viewMode === 'history' ? 'active' : ''}`}
          onClick={() => setViewMode('history')}
        >
          History
        </button>
      </section>

      {viewMode === 'capture' && (
        <section className="capture-section">
          <div className="capture-buttons">
            <button className="btn btn-primary" onClick={startCamera} disabled={cameraActive}>
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

          {cameraActive && (
            <div className="camera-section">
              <video ref={videoRef} autoPlay playsInline className="camera-feed" />
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
        </section>
      )}

      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {viewMode === 'analysis' && (
        <section className="analysis-pane">
          <div className="analysis-grid">
            <div className="analysis-visual">
              {capturedImage ? (
                <div className="image-container">
                  <img src={capturedImage} alt="Fish capture" className="captured-image" />
                  {isAnalyzing && (
                    <div className="analyzing-overlay">
                      <div className="spinner"></div>
                      <p>Analyzing freshness...</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="placeholder-card">
                  <p>No capture loaded. Start camera or upload a deck photo.</p>
                </div>
              )}

              <div className="analysis-actions">
                <button className="btn btn-secondary" onClick={resetCapture}>
                  New Capture
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => runAnalysis()}
                  disabled={!capturedImage || isAnalyzing}
                >
                  Re-run Analysis
                </button>
              </div>
            </div>

            <div className="analysis-detail">
              {analysis ? (
                <div className="analysis-card">
                  <div className="score-header">
                    <div>
                      <h3>Freshness Summary</h3>
                      <span className="timestamp">Logged {formatTimestamp(analysis.timestamp)}</span>
                    </div>
                    <div className="grade-badge" style={{ backgroundColor: gradeColor(analysis.grade) }}>
                      Grade {analysis.grade}
                    </div>
                  </div>

                  <div className="score-chip-group">{renderScoreDetail()}</div>

                  <div className="score-narrative">
                    <h4>Guidance</h4>
                    <p>{renderScoreNarrative()}</p>
                  </div>

                  <div className="handling-notes">
                    <h4>Handling Notes</h4>
                    <ul>
                      <li>{analysis.vibrancy}</li>
                      <li>{analysis.handlingNote}</li>
                      <li>Reminder: re-check in {analysis.checkPoint.reminderOffsetMinutes} min</li>
                    </ul>
                  </div>

                  <div className="analysis-footer">
                    <span>Deck phase: {analysis.checkPoint.deckPhase}</span>
                    <span>Event #{analysis.checkPoint.eventIndex}</span>
                  </div>
                </div>
              ) : (
                <div className="placeholder-card">
                  <p>Capture a fish photo to generate an AI freshness score and next action.</p>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {viewMode === 'history' && (
        <section className="history-pane">
          <header className="history-header">
            <h3>Trip Log</h3>
            <button
              className="btn btn-secondary"
              onClick={() => {
                storageService.clearFreshnessHistory();
                setHistory([]);
                closeHistoryModal();
              }}
            >
              Clear History
            </button>
          </header>
          <div className="history-list">{renderHistory()}</div>
        </section>
      )}

      <section className="freshness-tips">
        <h3>Deck Playbook</h3>
        <ul>
          <li>Bleed within 60 seconds of gaff. Use gill cut and tail nick for big fish.</li>
          <li>Pack ice into cavity and along lateral line; rebuild slurry every hour.</li>
          <li>Rotate fish during long runs to avoid flat-spot bruising.</li>
          <li>Log every check to build auction-grade freshness history.</li>
        </ul>
      </section>

      {isHistoryModalOpen && selectedHistory && (
        <div
          className="history-modal"
          role="dialog"
          aria-modal="true"
          aria-label="Freshness analysis detail"
          onClick={closeHistoryModal}
        >
          <div className="history-modal-content" onClick={(event) => event.stopPropagation()}>
            <button
              className="modal-close"
              type="button"
              onClick={closeHistoryModal}
              aria-label="Close detail view"
            >
              ×
            </button>
            <div className="history-modal-body">
              {renderHistoryDetail()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FreshnessQA;