import React, { useEffect, useMemo, useState } from 'react';
import MapLibreMap from './MapLibreMap';
import './PlanCard.css';

const defaultPosition = { lat: 47.613, lng: -122.342 };

const defaultForecast = {
  locationName: '',
  conditionSummary: '',
  seaSurfaceTemp: 0,
  airTemp: 0,
  solunar: '',
  swellSummary: '',
  tideSummary: '',
  warnings: [],
  biteWindows: [],
  hourly: [],
  marine_summary: ''
};

const PlanCard = () => {
  const [position, setPosition] = useState(defaultPosition);
  const [geoStatus, setGeoStatus] = useState('loading');
  const [locationInput, setLocationInput] = useState('');
  const [isLoadingPlan, setIsLoadingPlan] = useState(false);
  const [planData, setPlanData] = useState(null);
  const [forecastData, setForecastData] = useState(defaultForecast);
  const [isTeleported, setIsTeleported] = useState(false);

  useEffect(() => {
    if (!navigator.geolocation) {
      setGeoStatus('unsupported');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (coords) => {
        if (!isTeleported) {
          setPosition({ lat: coords.coords.latitude, lng: coords.coords.longitude });
          setGeoStatus('ready');
        }
      },
      () => setGeoStatus('denied'),
      { enableHighAccuracy: true, timeout: 10000 }
    );

    const watchId = navigator.geolocation.watchPosition(
      (coords) => {
        if (!isTeleported) {
          setPosition({ lat: coords.coords.latitude, lng: coords.coords.longitude });
          setGeoStatus('ready');
        }
      },
      () => setGeoStatus('denied'),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, [isTeleported]);

  const fetchPlanForLocation = async (lat, lng) => {
    setIsLoadingPlan(true);
    try {
      const response = await fetch('http://localhost:8000/api/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: { lat, lng },
          target_species: null,
          trip_duration: 6
        })
      });

      if (!response.ok) throw new Error('Failed to fetch plan');

      const data = await response.json();
      setPlanData(data);

      // Update forecast data
      if (data.forecast) {
        setForecastData({
          locationName: data.forecast.location_name || 'Unknown Location',
          conditionSummary: data.forecast.condition_summary || '',
          seaSurfaceTemp: data.forecast.sea_surface_temp || data.conditions.temperature || 0,
          airTemp: data.forecast.air_temp || data.conditions.temperature || 0,
          marine_summary: data.forecast.marine_summary || '',
          solunar: data.forecast.solunar || 'N/A',
          swellSummary: data.forecast.swell_summary || 'N/A',
          tideSummary: data.forecast.tide_summary || 'N/A',
          warnings: data.forecast.warnings || [],
          biteWindows: data.forecast.bite_windows || [],
          hourly: data.forecast.hourly || []
        });
      }
    } catch (error) {
      console.error('Error fetching plan:', error);
      alert('Failed to load plan data. Using mock data.');
    } finally {
      setIsLoadingPlan(false);
    }
  };

  const handleLocationSubmit = async (e) => {
    e.preventDefault();
    if (!locationInput.trim()) return;

    // Parse location input (support "lat, lng" or place name)
    const coords = locationInput.split(',').map(s => s.trim());
    if (coords.length === 2) {
      const lat = parseFloat(coords[0]);
      const lng = parseFloat(coords[1]);
      if (!isNaN(lat) && !isNaN(lng)) {
        setIsTeleported(true);
        setPosition({ lat, lng });
        setGeoStatus('ready');
        await fetchPlanForLocation(lat, lng);
        return;
      }
    }

    // If not coordinates, try geocoding (simplified - you can add Google/Mapbox geocoding)
    alert('Please enter coordinates in format: latitude, longitude (e.g., 34.0522, -118.2437)');
  };

  const mockPlanData = useMemo(() => ({
    targetSpecies: planData?.target_species || '',
    depthBand: planData?.depth_band || '',
    timeWindow: planData?.time_window || '',
    areaHint: planData?.area_hint || '',
    conditions: planData?.conditions ? {
      windSpeed: planData.conditions.wind_speed,
      windDirection: planData.conditions.wind_direction,
      waveHeight: planData.conditions.wave_height,
      tide: planData.conditions.tide,
      lunar: planData.conditions.lunar,
      temperature: planData.conditions.temperature
    } : { windSpeed: 0, windDirection: '', waveHeight: 0, tide: '', lunar: '', temperature: 0 },
    fuelNotes: planData?.fuel_notes || '',
    safetyNotes: planData?.safety_notes || '',
    planB: planData?.plan_b || ''
  }), [planData]);

  const getWeatherCondition = () => {
    const hour = new Date().getHours();
    const { windSpeed, waveHeight } = mockPlanData.conditions;
    if (hour >= 6 && hour < 18) {
      if (windSpeed > 15 || waveHeight > 4) return 'stormy-day';
      if (windSpeed > 10 || waveHeight > 2) return 'windy-day';
      return 'clear-day';
    } else {
      if (windSpeed > 15 || waveHeight > 4) return 'stormy-night';
      if (windSpeed > 10 || waveHeight > 2) return 'windy-night';
      return 'clear-night';
    }
  };

  const weatherCondition = getWeatherCondition();

  return (
    <div className={`weather-plan-card ${weatherCondition}`}>
      <div className="marine-weather-display">
        <div className="location-header">
          <span className="location-name">{forecastData.locationName || 'Enter coordinates to get forecast'}</span>
        </div>
        {forecastData.airTemp > 0 ? (
          <div className="main-conditions">
            <div className="primary-temp">{forecastData.airTemp}°</div>
            <div className="feels-like">Feels Like: {forecastData.airTemp - 6}°</div>
            <div className="high-low">H:{forecastData.airTemp + 12}° L:{forecastData.airTemp - 2}°</div>
          </div>
        ) : (
          <div className="main-conditions">
            <div className="primary-temp" style={{ fontSize: '1.5rem', opacity: 0.5 }}>No data</div>
          </div>
        )}
      </div>

      {(forecastData.conditionSummary || forecastData.hourly.length > 0) && (
        <div className="combined-weather-card">
          <div className="weather-description">
            <p>{forecastData.conditionSummary} {forecastData.hourly.length > 0 && `Wind gusts up to ${forecastData.hourly[0]?.gust || '15 kt'} are making the temperature feel like ${forecastData.airTemp - 6}°.`}</p>
          </div>
          {forecastData.hourly.length > 0 && (
            <div className="hourly-forecast-container">
              <div className="hourly-forecast-strip" id="hourly-strip">
                {forecastData.hourly.map((entry, idx) => (
                  <div className="hourly-item" key={idx}>
                    <div className="hourly-time">{entry.label}</div>
                    <div className={`hourly-icon ${entry.rating === 'good' ? 'moon-icon' : 'cloud-icon'}`}></div>
                    <div className="hourly-temp">{entry.temperature}°</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="vessel-position-card">
        <div className="vessel-header">
          <div className="vessel-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div className="map-icon"></div>
              <span>Vessel Position</span>
            </div>
            {geoStatus === 'loading' && <span className="geo-status loading">Getting location...</span>}
            {geoStatus === 'denied' && <span className="geo-status denied">Location denied</span>}
            {geoStatus === 'unsupported' && <span className="geo-status error">Not supported</span>}
            {geoStatus === 'ready' && <span className="geo-status ready">● Live</span>}
          </div>
          <div className="coordinates-display">
            <span className="coord-value">{position.lat >= 0 ? `${position.lat.toFixed(4)}°N` : `${Math.abs(position.lat).toFixed(4)}°S`}</span>
            <span className="coord-value">{position.lng >= 0 ? `${position.lng.toFixed(4)}°E` : `${Math.abs(position.lng).toFixed(4)}°W`}</span>
          </div>
        </div>

        <div className="map-display">
          {geoStatus === 'ready' ? (
            <MapLibreMap position={position} />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'white', fontSize: '0.9rem' }}>
              {geoStatus === 'loading' && 'Loading map...'}
              {geoStatus === 'denied' && 'Location access denied - cannot display map'}
              {geoStatus === 'unsupported' && 'Geolocation not supported'}
            </div>
          )}
        </div>
      </div>

      {/* Location Teleport Input */}
      <div className="location-teleport-card">
        <form onSubmit={handleLocationSubmit} className="teleport-form">
          <div className="teleport-header">
            <span className="teleport-icon"></span>
            <h3>Teleport to Location</h3>
          </div>
          <div className="teleport-input-group">
            <input
              type="text"
              value={locationInput}
              onChange={(e) => setLocationInput(e.target.value)}
              placeholder="Enter coordinates: 34.0522, -118.2437"
              className="teleport-input"
              disabled={isLoadingPlan}
            />
            <button type="submit" className="btn btn-primary" disabled={isLoadingPlan}>
              {isLoadingPlan ? 'Loading...' : 'Get Plan'}
            </button>
            {isTeleported && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setIsTeleported(false)}
                style={{ marginLeft: '0.5rem' }}
              >
                Use Live Location
              </button>
            )}
          </div>
          {isLoadingPlan && <div className="loading-text">Fetching marine conditions and generating plan...</div>}
        </form>
      </div>

      {planData && (
        <div className="planning-grid">
          <div className="plan-card primary-target">
            <div className="card-header"><div className="card-icon target-icon"></div><h3>Primary Target</h3></div>
            <div className="card-content">
              <p><strong>Species:</strong> {mockPlanData.targetSpecies || 'N/A'}</p>
              <p><strong>Depth:</strong> {mockPlanData.depthBand || 'N/A'}</p>
              <p><strong>Best Time:</strong> {mockPlanData.timeWindow || 'N/A'}</p>
              <p><strong>Area:</strong> {mockPlanData.areaHint || 'N/A'}</p>
            </div>
          </div>

          <div className="plan-card marine-conditions">
            <div className="card-header"><div className="card-icon conditions-icon"></div><h3>Marine Conditions</h3></div>
            <div className="card-content">
              <div className="conditions-grid">
                <div className="condition-item"><span className="label">Wind:</span><span className="value">{mockPlanData.conditions.windSpeed || 0} mph {mockPlanData.conditions.windDirection}</span></div>
                <div className="condition-item"><span className="label">Waves:</span><span className="value">{mockPlanData.conditions.waveHeight || 0} ft</span></div>
                <div className="condition-item"><span className="label">Tide:</span><span className="value">{mockPlanData.conditions.tide || 'N/A'}</span></div>
                <div className="condition-item"><span className="label">Moon:</span><span className="value">{mockPlanData.conditions.lunar || 'N/A'}</span></div>
                <div className="condition-item"><span className="label">Water:</span><span className="value">{mockPlanData.conditions.temperature || 0}°F</span></div>
              </div>
              {forecastData.marine_summary && (
                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                  <p style={{ fontSize: '0.9rem', lineHeight: '1.5', opacity: 0.9 }}>{forecastData.marine_summary}</p>
                </div>
              )}
            </div>
          </div>

          <div className="plan-card logistics">
            <div className="card-header"><div className="card-icon logistics-icon"></div><h3>Logistics</h3></div>
            <div className="card-content">
              <p><strong>Fuel:</strong> {mockPlanData.fuelNotes || 'N/A'}</p>
              <p><strong>Safety:</strong> {mockPlanData.safetyNotes || 'N/A'}</p>
            </div>
          </div>

          <div className="plan-card plan-b">
            <div className="card-header"><div className="card-icon planb-icon"></div><h3>Plan B</h3></div>
            <div className="card-content"><p><strong>Strategy:</strong> {mockPlanData.planB || 'N/A'}</p></div>
          </div>
        </div>
      )}

    </div>
  );
};

export default PlanCard;