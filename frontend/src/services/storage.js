const STORAGE_KEYS = {
  TRIPS: 'leviathan_trips',
  CURRENT_TRIP: 'leviathan_current_trip',
  SETTINGS: 'leviathan_settings',
  FRESHNESS_HISTORY: 'leviathan_freshness_history',
  SONAR_HISTORY: 'leviathan_sonar_history',
};

class StorageService {
  getItem(key, defaultValue) {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error(`Error reading from localStorage for key ${key}:`, error);
      return defaultValue;
    }
  }

  setItem(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error writing to localStorage for key ${key}:`, error);
    }
  }

  removeItem(key) {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error(`Error removing from localStorage for key ${key}:`, error);
    }
  }

  getTrips() {
    return this.getItem(STORAGE_KEYS.TRIPS, []);
  }

  saveTrip(trip) {
    const trips = this.getTrips();
    const existingIndex = trips.findIndex(t => t.id === trip.id);

    if (existingIndex >= 0) {
      trips[existingIndex] = trip;
    } else {
      trips.push(trip);
    }

    this.setItem(STORAGE_KEYS.TRIPS, trips);
  }

  deleteTrip(tripId) {
    const trips = this.getTrips().filter(t => t.id !== tripId);
    this.setItem(STORAGE_KEYS.TRIPS, trips);
  }

  getCurrentTrip() {
    return this.getItem(STORAGE_KEYS.CURRENT_TRIP, null);
  }

  setCurrentTrip(trip) {
    if (trip) {
      this.setItem(STORAGE_KEYS.CURRENT_TRIP, trip);
    } else {
      this.removeItem(STORAGE_KEYS.CURRENT_TRIP);
    }
  }

  startTrip(location) {
    const trip = {
      id: `trip_${Date.now()}`,
      startTime: new Date().toISOString(),
      location,
      catches: [],
      conditions: {
        windSpeed: 0,
        windDirection: 'N',
        waveHeight: 0,
        tide: 'Unknown',
        lunar: 'Unknown',
        temperature: 0
      }
    };

    this.setCurrentTrip(trip);
    this.saveTrip(trip);
    return trip;
  }

  endTrip() {
    const currentTrip = this.getCurrentTrip();
    if (currentTrip) {
      const endedTrip = {
        ...currentTrip,
        endTime: new Date().toISOString()
      };
      this.saveTrip(endedTrip);
      this.setCurrentTrip(null);
      return endedTrip;
    }
    return null;
  }

  addCatch(catchRecord) {
    const currentTrip = this.getCurrentTrip();
    if (!currentTrip) return null;

    const newCatch = {
      ...catchRecord,
      id: `catch_${Date.now()}`
    };

    const updatedTrip = {
      ...currentTrip,
      catches: [...currentTrip.catches, newCatch]
    };

    this.setCurrentTrip(updatedTrip);
    this.saveTrip(updatedTrip);
    return newCatch;
  }

  getSettings() {
    return this.getItem(STORAGE_KEYS.SETTINGS, {
      units: 'imperial',
      autoSave: true,
      ttsEnabled: true,
      offlineMode: false
    });
  }

  saveSettings(settings) {
    this.setItem(STORAGE_KEYS.SETTINGS, settings);
  }

  getFreshnessHistory() {
    return this.getItem(STORAGE_KEYS.FRESHNESS_HISTORY, []);
  }

  saveFreshnessReading(reading) {
    const history = this.getFreshnessHistory();
    history.unshift(reading);

    if (history.length > 50) {
      history.splice(50);
    }

    this.setItem(STORAGE_KEYS.FRESHNESS_HISTORY, history);
  }

  clearFreshnessHistory() {
    this.setItem(STORAGE_KEYS.FRESHNESS_HISTORY, []);
  }

  updateFreshnessReading(id, updates) {
    const history = this.getFreshnessHistory();
    const index = history.findIndex(item => item.id === id);

    if (index === -1) {
      return null;
    }

    const updatedReading = {
      ...history[index],
      ...updates
    };

    history[index] = updatedReading;
    this.setItem(STORAGE_KEYS.FRESHNESS_HISTORY, history);
    return updatedReading;
  }

  appendTripEvent(event) {
    const trip = this.getCurrentTrip();

    if (!trip) {
      return null;
    }

    const newEvent = {
      id: event.id ?? `event_${Date.now()}`,
      ...event
    };

    const updatedTrip = {
      ...trip,
      events: [...(trip.events || []), newEvent]
    };

    this.setCurrentTrip(updatedTrip);
    this.saveTrip(updatedTrip);
    return newEvent;
  }

  getCurrentTripEvents() {
    const trip = this.getCurrentTrip();
    return trip?.events || [];
  }

  getSonarHistory() {
    return this.getItem(STORAGE_KEYS.SONAR_HISTORY, []);
  }

  saveSonarReading(reading) {
    const history = this.getSonarHistory();
    history.unshift(reading);

    if (history.length > 50) {
      history.splice(50);
    }

    this.setItem(STORAGE_KEYS.SONAR_HISTORY, history);
  }

  exportData() {
    const data = {
      trips: this.getTrips(),
      settings: this.getSettings(),
      freshnessHistory: this.getFreshnessHistory(),
      sonarHistory: this.getSonarHistory(),
      exportDate: new Date().toISOString()
    };

    return JSON.stringify(data, null, 2);
  }

  importData(jsonData) {
    try {
      const data = JSON.parse(jsonData);

      if (data.trips) {
        this.setItem(STORAGE_KEYS.TRIPS, data.trips);
      }

      if (data.settings) {
        this.setItem(STORAGE_KEYS.SETTINGS, data.settings);
      }

      if (data.freshnessHistory) {
        this.setItem(STORAGE_KEYS.FRESHNESS_HISTORY, data.freshnessHistory);
      }

      if (data.sonarHistory) {
        this.setItem(STORAGE_KEYS.SONAR_HISTORY, data.sonarHistory);
      }

      return true;
    } catch (error) {
      console.error('Error importing data:', error);
      return false;
    }
  }

  clearAllData() {
    Object.values(STORAGE_KEYS).forEach(key => {
      this.removeItem(key);
    });
  }

  getStorageInfo() {
    const info = {
      totalSize: 0,
      itemCounts: {},
      lastModified: new Date().toISOString()
    };

    Object.entries(STORAGE_KEYS).forEach(([name, key]) => {
      const item = localStorage.getItem(key);
      if (item) {
        info.totalSize += item.length;
        try {
          const parsed = JSON.parse(item);
          info.itemCounts[name] = Array.isArray(parsed) ? parsed.length : 1;
        } catch {
          info.itemCounts[name] = 1;
        }
      } else {
        info.itemCounts[name] = 0;
      }
    });

    return info;
  }
}

export const storageService = new StorageService();