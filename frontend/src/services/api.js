const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiService {
  async makeRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async getPlan(request) {
    return this.makeRequest('/plan', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async analyzeSonar(request) {
    return this.makeRequest('/sonar/analyze', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async analyzeFreshness(request) {
    return this.makeRequest('/freshness/analyze', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async startTrip(location) {
    return this.makeRequest('/trips', {
      method: 'POST',
      body: JSON.stringify({
        startTime: new Date().toISOString(),
        location,
      }),
    });
  }

  async updateTrip(tripId, updates) {
    return this.makeRequest(`/trips/${tripId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async endTrip(tripId) {
    return this.makeRequest(`/trips/${tripId}/end`, {
      method: 'POST',
    });
  }

  async addCatch(tripId, catchRecord) {
    return this.makeRequest(`/trips/${tripId}/catches`, {
      method: 'POST',
      body: JSON.stringify(catchRecord),
    });
  }

  async getTrips() {
    return this.makeRequest('/trips');
  }

  async getTrip(tripId) {
    return this.makeRequest(`/trips/${tripId}`);
  }

  async getMarineConditions(location) {
    const { lat, lng } = location;
    return this.makeRequest(`/conditions?lat=${lat}&lng=${lng}`);
  }

  async uploadImage(file) {
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Image upload failed: ${response.status}`);
    }

    const result = await response.json();
    return result.url;
  }
}

export const apiService = new ApiService();

export const mockApiService = {
  async getPlan(request) {
    await new Promise(resolve => setTimeout(resolve, 1000));

    return {
      targetSpecies: "Rockfish, Lingcod",
      depthBand: "80-120 ft",
      timeWindow: "Dawn + 2hrs (5:30-7:30 AM)",
      areaHint: "North reef structure, 2nm offshore",
      conditions: {
        windSpeed: 8,
        windDirection: "NW",
        waveHeight: 2.5,
        tide: "Rising",
        lunar: "New moon",
        temperature: 58
      },
      fuelNotes: "15 gal estimated for 6hr trip",
      safetyNotes: "VHF Channel 16, EPIRB active",
      planB: "Shallow water halibut (40-60ft) if conditions worsen",
      confidence: 0.87
    };
  },

  async analyzeSonar(request) {
    await new Promise(resolve => setTimeout(resolve, 2000));

    const mockResponses = [
      {
        depth: 85,
        density: 'high',
        schoolWidth: 'wide',
        confidence: 0.92,
        recommendation: "Strong school detected! Drop lines now at 80-90ft.",
        detectedObjects: {
          fishArches: 8,
          bottomStructure: true,
          thermocline: 75
        }
      },
      {
        depth: 45,
        density: 'medium',
        schoolWidth: 'narrow',
        confidence: 0.78,
        recommendation: "Medium activity. Try slow trolling through area.",
        detectedObjects: {
          fishArches: 3,
          bottomStructure: false
        }
      }
    ];

    return mockResponses[Math.floor(Math.random() * mockResponses.length)];
  },

  async analyzeFreshness(request) {
    await new Promise(resolve => setTimeout(resolve, 1500));

    const mockResponses = [
      {
        bleeding: 95,
        iceContact: 88,
        bruising: 92,
        overall: 92,
        grade: 'A',
        nextAction: "Excellent! Continue current handling. Move to ice storage.",
        timestamp: new Date().toISOString(),
        marketValue: {
          estimatedPrice: 12.50,
          qualityFactors: ["Excellent bleeding", "Good ice contact", "Minimal bruising"]
        }
      },
      {
        bleeding: 78,
        iceContact: 65,
        bruising: 85,
        overall: 76,
        grade: 'B',
        nextAction: "Good bleeding. Improve ice contact - add more ice around gills.",
        timestamp: new Date().toISOString(),
        marketValue: {
          estimatedPrice: 9.75,
          qualityFactors: ["Good bleeding", "Fair ice contact", "Minor bruising"]
        }
      }
    ];

    return mockResponses[Math.floor(Math.random() * mockResponses.length)];
  }
};

export const getApiService = () => {
  return process.env.NODE_ENV === 'development' ? mockApiService : apiService;
};