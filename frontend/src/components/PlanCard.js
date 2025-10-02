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
    },
    {
      label: '16:00',
      time: '4:00 PM',
      wind: 'NW 16 kt',
      gust: '22 kt',
      seas: '3.8 ft @ 7s',
      current: '1.2 kt NW',
      comment: 'Winds easing',
      rating: 'caution'
    },
    {
      label: '17:00',
      time: '5:00 PM',
      wind: 'NW 14 kt',
      gust: '20 kt',
      seas: '3.4 ft @ 8s',
      current: '1.0 kt NW',
      comment: 'Improving',
      rating: 'caution'
    },
    {
      label: '18:00',
      time: '6:00 PM',
      wind: 'NW 12 kt',
      gust: '18 kt',
      seas: '3.0 ft @ 8s',
      current: '0.8 kt NW',
      comment: 'Better conditions',
      rating: 'caution'
    },
    {
      label: '19:00',
      time: '7:00 PM',
      wind: 'NW 10 kt',
      gust: '15 kt',
      seas: '2.6 ft @ 9s',
      current: '0.6 kt NW',
      comment: 'Good evening',
      rating: 'good'
    },
    {
      label: '20:00',
      time: '8:00 PM',
      wind: 'NW 8 kt',
      gust: '12 kt',
      seas: '2.2 ft @ 9s',
      current: '0.4 kt NW',
      comment: 'Calm evening',
      rating: 'good'
    },
    {
      label: '21:00',
      time: '9:00 PM',
      wind: 'NW 6 kt',
      gust: '10 kt',
      seas: '1.8 ft @ 10s',
      current: '0.3 kt NW',
      comment: 'Perfect night',
      rating: 'good'
    },
    {
      label: '22:00',
      time: '10:00 PM',
      wind: 'NW 4 kt',
      gust: '8 kt',
      seas: '1.4 ft @ 10s',
      current: '0.2 kt NW',
      comment: 'Glass calm',
      rating: 'good'
    },
    {
      label: '23:00',
      time: '11:00 PM',
      wind: 'NW 3 kt',
      gust: '6 kt',
      seas: '1.0 ft @ 11s',
      current: '0.1 kt NW',
      comment: 'Dead calm',
      rating: 'good'
    },
    {
      label: '00:00',
      time: '12:00 AM',
      wind: 'NW 2 kt',
      gust: '4 kt',
      seas: '0.8 ft @ 11s',
      current: '0.1 kt NW',
      comment: 'Ideal night',
      rating: 'good'
    },
    {
      label: '01:00',
      time: '1:00 AM',
      wind: 'NW 1 kt',
      gust: '3 kt',
      seas: '0.6 ft @ 12s',
      current: '0.1 kt NW',
      comment: 'Perfect calm',
      rating: 'good'
    },
    {
      label: '02:00',
      time: '2:00 AM',
      wind: 'NW 2 kt',
      gust: '4 kt',
      seas: '0.8 ft @ 12s',
      current: '0.1 kt NW',
      comment: 'Still calm',
      rating: 'good'
    },
    {
      label: '03:00',
      time: '3:00 AM',
      wind: 'NW 3 kt',
      gust: '5 kt',
      seas: '1.0 ft @ 11s',
      current: '0.2 kt NW',
      comment: 'Light breeze',
      rating: 'good'
    },
    {
      label: '04:00',
      time: '4:00 AM',
      wind: 'NW 4 kt',
      gust: '7 kt',
      seas: '1.2 ft @ 11s',
      current: '0.3 kt NW',
      comment: 'Building breeze',
      rating: 'good'
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

  // Determine weather condition for background
  const getWeatherCondition = () => {
    const hour = new Date().getHours();
    const windSpeed = mockPlanData.conditions.windSpeed;
    const waveHeight = mockPlanData.conditions.waveHeight;
    
    if (hour >= 6 && hour < 18) {
      // Daytime conditions
      if (windSpeed > 15 || waveHeight > 4) return 'stormy-day';
      if (windSpeed > 10 || waveHeight > 2) return 'windy-day';
      return 'clear-day';
    } else {
      // Nighttime conditions
      if (windSpeed > 15 || waveHeight > 4) return 'stormy-night';
      if (windSpeed > 10 || waveHeight > 2) return 'windy-night';
      return 'clear-night';
    }
  };

  const weatherCondition = getWeatherCondition();

  // Swipe functionality for hourly forecast
  useEffect(() => {
    const hourlyStrip = document.getElementById('hourly-strip');
    if (!hourlyStrip) return;

    let startX = 0;
    let currentX = 0;
    let isDragging = false;

    const handleTouchStart = (e) => {
      startX = e.touches[0].clientX;
      isDragging = true;
      hourlyStrip.style.transition = 'none';
    };

    const handleTouchMove = (e) => {
      if (!isDragging) return;
      currentX = e.touches[0].clientX;
      const diffX = currentX - startX;
      hourlyStrip.style.transform = `translateX(${diffX}px)`;
    };

    const handleTouchEnd = () => {
      if (!isDragging) return;
      isDragging = false;
      hourlyStrip.style.transition = 'transform 0.3s ease';
      
      const diffX = currentX - startX;
      const threshold = 50;
      
      if (Math.abs(diffX) > threshold) {
        if (diffX > 0) {
          // Swipe right - scroll left
          hourlyStrip.scrollBy({ left: -200, behavior: 'smooth' });
        } else {
          // Swipe left - scroll right
          hourlyStrip.scrollBy({ left: 200, behavior: 'smooth' });
        }
      }
      
      hourlyStrip.style.transform = 'translateX(0)';
    };

    hourlyStrip.addEventListener('touchstart', handleTouchStart);
    hourlyStrip.addEventListener('touchmove', handleTouchMove);
    hourlyStrip.addEventListener('touchend', handleTouchEnd);

    return () => {
      hourlyStrip.removeEventListener('touchstart', handleTouchStart);
      hourlyStrip.removeEventListener('touchmove', handleTouchMove);
      hourlyStrip.removeEventListener('touchend', handleTouchEnd);
    };
  }, []);


  return (
    <div className={`weather-plan-card ${weatherCondition}`}>
      {/* Weather-style Marine Conditions Display */}
      <div className="marine-weather-display">
        <div className="location-header">
          <span className="location-name">Coastal Shelf</span>
        </div>
        
        <div className="main-conditions">
          <div className="primary-temp">{fishermanForecast.airTemp}°</div>
          <div className="feels-like">Feels Like: {fishermanForecast.airTemp - 6}°</div>
          <div className="high-low">H:{fishermanForecast.airTemp + 12}° L:{fishermanForecast.airTemp - 2}°</div>
        </div>
      </div>

      {/* Combined Weather Card */}
      <div className="combined-weather-card">
        <div className="weather-description">
          <p>{fishermanForecast.conditionSummary} Wind gusts up to {fishermanForecast.hourly[0]?.gust || '15'} kt are making the temperature feel like {fishermanForecast.airTemp - 6}°.</p>
        </div>
        
        <div className="hourly-forecast-container">
          <div className="hourly-forecast-strip" id="hourly-strip">
            {fishermanForecast.hourly.map((entry, index) => (
              <div className="hourly-item" key={entry.time}>
                <div className="hourly-time">{entry.label}</div>
                <div className={`hourly-icon ${entry.rating === 'good' ? 'moon-icon' : 'cloud-icon'}`}></div>
                <div className="hourly-temp">{entry.wind.split(' ')[1]}°</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Vessel Position Card */}
      <div className="vessel-position-card">
        <div className="vessel-header">
          <div className="vessel-title">
            <div className="map-icon"></div>
            <span>Vessel Position</span>
          </div>
          <div className="coordinates-display">
            <span className="coord-value">{position.lat >= 0 ? `${position.lat.toFixed(2)}°N` : `${Math.abs(position.lat).toFixed(2)}°S`}</span>
            <span className="coord-value">{position.lng >= 0 ? `${position.lng.toFixed(2)}°E` : `${Math.abs(position.lng).toFixed(2)}°W`}</span>
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