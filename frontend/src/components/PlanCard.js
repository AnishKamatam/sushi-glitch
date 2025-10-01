import React, { useEffect, useMemo, useState } from 'react';
import './PlanCard.css';

const defaultPosition = { lat: 47.613, lng: -122.342 };

const fishermanForecast = {
  locationName: 'Coastal Shelf',
  conditionSummary: 'Calm dawn seas with light NW windline building after lunch.',
  seaSurfaceTemp: 56,
  airTemp: 58,
  solunar: 'Major 05:48 AM - 07:15 AM · Minor 11:32 AM - 12:10 PM',
  swellSummary: '2.5 ft WNW @ 9s',
  tideSummary: 'Flooding to +5.7 ft by 09:40',
  warnings: [
    'NW windline builds 18 kt after 14:00; expect tight chop beyond 3 nm.',
    'Dense crab pot field along 60 ft contour heading south.'
  ],
  biteWindows: [
    {
      label: 'Dawn Window',
      window: '5:20 AM - 7:40 AM',
      action: 'Drop metal jigs on reef peak',
      tide: 'Slack flood',
      confidence: 'High'
    },
    {
      label: 'Late Morning',
      window: '10:30 AM - 12:00 PM',
      action: 'Slow drift bait rigs',
      tide: 'First ebb push',
      confidence: 'Medium'
    },
    {
      label: 'Plan B',
      window: '2:30 PM - 4:00 PM',
      action: 'Slide inside kelp edges for halibut',
      tide: 'Building ebb · wind 15+ kt',
      confidence: 'Contingency'
    }
  ],
  hourly: [
    {
      label: 'Now',
      time: '5:30 AM',
      wind: 'NW 8 kt',
      gust: '12 kt',
      seas: '2.4 ft @ 9s',
      current: '0.5 kt NW',
      comment: 'Prime drop',
      rating: 'good'
    },
    {
      label: '07:00',
      time: '7:00 AM',
      wind: 'NW 9 kt',
      gust: '13 kt',
      seas: '2.6 ft @ 9s',
      current: '0.6 kt NW',
      comment: 'Slack, stay on spot',
      rating: 'good'
    },
    {
      label: '09:00',
      time: '9:00 AM',
      wind: 'NW 11 kt',
      gust: '15 kt',
      seas: '3.0 ft @ 8s',
      current: '0.8 kt NW',
      comment: 'Slide along ridge',
      rating: 'fair'
    },
    {
      label: '12:00',
      time: '12:00 PM',
      wind: 'NW 15 kt',
      gust: '20 kt',
      seas: '3.6 ft @ 7s',
      current: '1.1 kt NW',
      comment: 'Windline forming',
      rating: 'caution'
    },
    {
      label: '15:00',
      time: '3:00 PM',
      wind: 'NW 18 kt',
      gust: '24 kt',
      seas: '4.2 ft @ 7s',
      current: '1.4 kt NW',
      comment: 'Shift inshore',
      rating: 'planb'
    }
  ]
};


const PlanCard = () => {
  const [position, setPosition] = useState(defaultPosition);
  const [geoStatus, setGeoStatus] = useState('loading');

  useEffect(() => {
    if (!navigator.geolocation) {
      setGeoStatus('unsupported');
      return;
    }

    // Get initial position
    navigator.geolocation.getCurrentPosition(
      (coords) => {
        setPosition({
          lat: coords.coords.latitude,
          lng: coords.coords.longitude
        });
        setGeoStatus('ready');
      },
      () => {
        setGeoStatus('denied');
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );

    // Set up real-time position tracking
    const watchId = navigator.geolocation.watchPosition(
      (coords) => {
        setPosition({
          lat: coords.coords.latitude,
          lng: coords.coords.longitude
        });
        setGeoStatus('ready');
      },
      () => {
        setGeoStatus('denied');
      },
      { 
        enableHighAccuracy: true, 
        timeout: 10000,
        maximumAge: 5000 // Update every 5 seconds
      }
    );

    // Cleanup watch on unmount
    return () => {
      navigator.geolocation.clearWatch(watchId);
    };
  }, []);


  const mockPlanData = useMemo(() => ({
    targetSpecies: 'Rockfish, Lingcod',
    depthBand: '80-120 ft',
    timeWindow: 'Dawn + 2hrs (5:30 AM - 7:30 AM)',
    areaHint: 'North reef structure, 2nm offshore',
    conditions: {
      windSpeed: 8,
      windDirection: 'NW',
      waveHeight: 2.5,
      tide: 'Rising',
      lunar: 'New moon'
    },
    fuelNotes: '15 gal estimated for 6hr trip',
    safetyNotes: 'VHF Channel 16, EPIRB active',
    planB: 'Shallow water halibut (40-60ft) if conditions worsen'
  }), []);

  const locationLabel = useMemo(() => {
    if (geoStatus === 'ready') {
      const latDir = position.lat >= 0 ? 'N' : 'S';
      const lngDir = position.lng >= 0 ? 'E' : 'W';
      return `Lat ${Math.abs(position.lat).toFixed(2)}° ${latDir} · Lon ${Math.abs(position.lng).toFixed(2)}° ${lngDir}`;
    }

    if (geoStatus === 'loading') {
      return 'Locating vessel…';
    }

    if (geoStatus === 'unsupported') {
      return 'Geolocation unavailable · using home port';
    }

    return 'Location denied · centered on home port';
  }, [geoStatus, position.lat, position.lng]);

  return (
    <div className="plan-card">
      <div className="vessel-position-card">
        <div className="vessel-header">
          <div className="vessel-title">
            <div className="map-icon"></div>
            <span>Vessel Position</span>
          </div>
          <div className="location-status">
            <div className="status-icon"></div>
            <span>
              {geoStatus === 'ready' ? 'Location services active' : 
               geoStatus === 'loading' ? 'Locating vessel...' :
               geoStatus === 'denied' ? 'Location denied' :
               geoStatus === 'unsupported' ? 'GPS unavailable' : 'Location services active'}
            </span>
          </div>
        </div>
        
        <div className="map-display">
          <div className="map-area">
            <div className="position-pin"></div>
            <div className="position-label">Current Position</div>
            <div className="radius-circle"></div>
            <div className="radius-label">~2 nautical miles</div>
          </div>
        </div>
        
        <div className="coordinates-display">
          <div className="coord-column">
            <div className="coord-label">Latitude</div>
            <div className="coord-value">{position.lat >= 0 ? `${position.lat.toFixed(4)}°N` : `${Math.abs(position.lat).toFixed(4)}°S`}</div>
          </div>
          <div className="coord-column">
            <div className="coord-label">Longitude</div>
            <div className="coord-value">{position.lng >= 0 ? `${position.lng.toFixed(4)}°E` : `${Math.abs(position.lng).toFixed(4)}°W`}</div>
          </div>
        </div>
      </div>

      <div className="plan-overview">

        <div className="forecast-panel">
          <div className="forecast-hero">
            <div className="hero-topline">
              <span className="hero-location">{fishermanForecast.locationName}</span>
              <span className="hero-metric">Sea {fishermanForecast.seaSurfaceTemp}&deg;F</span>
            </div>
            <div className="hero-main">
              <span className="hero-temp">{fishermanForecast.airTemp}&deg;</span>
              <div className="hero-details">
                <span className="hero-condition">{fishermanForecast.conditionSummary}</span>
                <span className="hero-sub">{fishermanForecast.swellSummary}</span>
                <span className="hero-sub">{fishermanForecast.tideSummary}</span>
                <span className="hero-sub">{fishermanForecast.solunar}</span>
              </div>
            </div>
          </div>

          <div className="forecast-metrics">
            {fishermanForecast.biteWindows.map((window) => (
              <div className="forecast-metric" key={window.label}>
                <span className="metric-label">{window.label}</span>
                <span className="metric-value">{window.window}</span>
                <span className="metric-caption">{window.action}</span>
                <span className="metric-caption subtle">{window.tide}</span>
                <span className="metric-tag">Confidence: {window.confidence}</span>
              </div>
            ))}
          </div>

          <div className="hourly-strip">
            {fishermanForecast.hourly.map((entry) => (
              <div className={`hourly-card rating-${entry.rating}`} key={entry.time}>
                <span className="hourly-label">{entry.label}</span>
                <span className="hourly-time">{entry.time}</span>
                <span className="hourly-metric">{entry.wind}</span>
                <span className="hourly-metric">G {entry.gust}</span>
                <span className="hourly-metric">{entry.seas}</span>
                <span className="hourly-metric">Drift {entry.current}</span>
                <span className="hourly-comment">{entry.comment}</span>
              </div>
            ))}
          </div>

          <div className="forecast-warnings">
            {fishermanForecast.warnings.map((notice) => (
              <div className="warning-pill" key={notice}>
                {notice}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="planning-grid">
        <div className="plan-card primary-target">
          <div className="card-header">
            <div className="card-icon target-icon"></div>
            <h3>Primary Target</h3>
          </div>
          <div className="card-content">
            <p><strong>Species:</strong> {mockPlanData.targetSpecies}</p>
            <p><strong>Depth:</strong> {mockPlanData.depthBand}</p>
            <p><strong>Best Time:</strong> {mockPlanData.timeWindow}</p>
            <p><strong>Area:</strong> {mockPlanData.areaHint}</p>
          </div>
        </div>

        <div className="plan-card marine-conditions">
          <div className="card-header">
            <div className="card-icon conditions-icon"></div>
            <h3>Marine Conditions</h3>
          </div>
          <div className="card-content">
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
        </div>

        <div className="plan-card logistics">
          <div className="card-header">
            <div className="card-icon logistics-icon"></div>
            <h3>Logistics</h3>
          </div>
          <div className="card-content">
            <p><strong>Fuel:</strong> {mockPlanData.fuelNotes}</p>
            <p><strong>Safety:</strong> {mockPlanData.safetyNotes}</p>
          </div>
        </div>

        <div className="plan-card plan-b">
          <div className="card-header">
            <div className="card-icon planb-icon"></div>
            <h3>Plan B</h3>
          </div>
          <div className="card-content">
            <p><strong>Strategy:</strong> {mockPlanData.planB}</p>
          </div>
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