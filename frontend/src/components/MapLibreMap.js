import React, { useRef, useEffect, useState } from 'react';
import Map, { Marker, Source, Layer } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';

const MapLibreMap = ({ position }) => {
  const mapRef = useRef(null);

  // Validate position values
  const validPosition = {
    lat: Math.max(-90, Math.min(90, position.lat || 0)),
    lng: Math.max(-180, Math.min(180, position.lng || 0))
  };

  const [viewState, setViewState] = useState({
    longitude: validPosition.lng,
    latitude: validPosition.lat,
    zoom: 13
  });

  // Update map when position changes
  useEffect(() => {
    if (mapRef.current) {
      mapRef.current.flyTo({
        center: [validPosition.lng, validPosition.lat],
        zoom: 13,
        duration: 1500
      });
    } else {
      setViewState({
        longitude: validPosition.lng,
        latitude: validPosition.lat,
        zoom: 13
      });
    }
  }, [validPosition.lat, validPosition.lng]);

  // Create GeoJSON for the circle (2 nautical miles = 3.704 km)
  const createCircle = (center, radiusInKm) => {
    const points = 64;
    const coords = {
      latitude: center.lat,
      longitude: center.lng
    };

    const km = radiusInKm;
    const ret = [];
    const distanceX = km / (111.32 * Math.cos((coords.latitude * Math.PI) / 180));
    const distanceY = km / 110.574;

    for (let i = 0; i < points; i++) {
      const theta = (i / points) * (2 * Math.PI);
      const x = distanceX * Math.cos(theta);
      const y = distanceY * Math.sin(theta);

      ret.push([coords.longitude + x, coords.latitude + y]);
    }
    ret.push(ret[0]);

    return {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [ret]
      }
    };
  };

  const circleGeoJSON = {
    type: 'FeatureCollection',
    features: [createCircle(validPosition, 3.704)]
  };

  return (
    <Map
      ref={mapRef}
      {...viewState}
      onMove={evt => setViewState(evt.viewState)}
      style={{ width: '100%', height: '100%', borderRadius: '12px' }}
      mapStyle="https://demotiles.maplibre.org/style.json"
    >
      {/* Circle layer */}
      <Source id="radius-circle" type="geojson" data={circleGeoJSON}>
        <Layer
          id="circle-fill"
          type="fill"
          paint={{
            'fill-color': '#3b82f6',
            'fill-opacity': 0.1
          }}
        />
        <Layer
          id="circle-outline"
          type="line"
          paint={{
            'line-color': '#3b82f6',
            'line-width': 2
          }}
        />
      </Source>

      {/* Marker at position */}
      <Marker
        longitude={validPosition.lng}
        latitude={validPosition.lat}
        anchor="bottom"
      >
        <div style={{
          width: '24px',
          height: '24px',
          cursor: 'pointer'
        }}>
          <svg
            height="24"
            viewBox="0 0 24 24"
            style={{
              fill: '#dc2626',
              stroke: 'white',
              strokeWidth: 2,
              filter: 'drop-shadow(0px 2px 4px rgba(0,0,0,0.3))'
            }}
          >
            <path d="M12 0C7.58 0 4 3.58 4 8c0 5.25 8 13 8 13s8-7.75 8-13c0-4.42-3.58-8-8-8zm0 11c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"/>
          </svg>
        </div>
      </Marker>
    </Map>
  );
};

export default MapLibreMap;
