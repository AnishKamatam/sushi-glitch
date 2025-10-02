import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
import math
import requests
from models.schemas import MarineConditions

class MarineService:
    def __init__(self):
        pass  # Open-Meteo doesn't require API key

    def _calculate_lunar_phase(self) -> str:
        """Calculate current lunar phase using astronomical formula"""
        now = datetime.now(timezone.utc)
        # Known new moon reference: Jan 6, 2000
        reference = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
        days_since = (now - reference).total_seconds() / 86400
        synodic_month = 29.53058867  # Average lunar cycle
        phase = (days_since % synodic_month) / synodic_month

        if phase < 0.0625:
            return "New moon"
        elif phase < 0.1875:
            return "Waxing crescent"
        elif phase < 0.3125:
            return "First quarter"
        elif phase < 0.4375:
            return "Waxing gibbous"
        elif phase < 0.5625:
            return "Full moon"
        elif phase < 0.6875:
            return "Waning gibbous"
        elif phase < 0.8125:
            return "Last quarter"
        else:
            return "Waning crescent"

    def _calculate_tide_state(self, lat: float, lng: float) -> str:
        """Simple tide estimation based on lunar position and time"""
        # Simplified tide calculation - in production use NOAA tide API
        now = datetime.now(timezone.utc)
        hours = now.hour + now.minute / 60.0

        # Simplified tidal cycle (2 high tides per day)
        tide_cycle = (hours % 12.4) / 12.4

        if tide_cycle < 0.15 or tide_cycle > 0.85:
            return "High"
        elif 0.35 < tide_cycle < 0.65:
            return "Low"
        elif tide_cycle < 0.35:
            return "Falling"
        else:
            return "Rising"

    async def get_conditions(self, lat: float, lng: float) -> MarineConditions:
        """Fetch real-time marine conditions for the given location"""
        try:
            # Get weather data from OpenWeatherMap
            weather_data = await self._fetch_weather_data(lat, lng)

            # Calculate lunar phase
            lunar_phase = self._calculate_lunar_phase()

            # Calculate tide state
            tide_state = self._calculate_tide_state(lat, lng)

            return MarineConditions(
                wind_speed=weather_data['wind_speed'],
                wind_direction=weather_data['wind_direction'],
                wave_height=weather_data['wave_height'],
                tide=tide_state,
                lunar=lunar_phase,
                temperature=weather_data['temperature']
            )

        except Exception as e:
            print(f"Error fetching marine conditions: {str(e)}")
            # Fallback to reasonable defaults
            return MarineConditions(
                wind_speed=8.0,
                wind_direction="NW",
                wave_height=2.0,
                tide="Unknown",
                lunar=self._calculate_lunar_phase(),
                temperature=55.0
            )

    async def _fetch_weather_data(self, lat: float, lng: float) -> Dict[str, Any]:
        """Fetch weather data from Open-Meteo API (free, no API key required)"""

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': lat,
            'longitude': lng,
            'current': 'temperature_2m,wind_speed_10m,wind_direction_10m',
            'hourly': 'temperature_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m',
            'temperature_unit': 'fahrenheit',
            'wind_speed_unit': 'mph',
            'timezone': 'auto',
            'forecast_days': 1
        }

        # Make request in thread to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.get(url, params=params, timeout=10)
        )
        response.raise_for_status()
        data = response.json()

        # Extract current weather data
        current = data.get('current', {})
        wind_speed = current.get('wind_speed_10m', 0)  # mph
        wind_deg = current.get('wind_direction_10m', 0)  # degrees
        temperature = current.get('temperature_2m', 55)  # Fahrenheit

        # Convert wind degrees to direction
        wind_direction = self._degrees_to_direction(wind_deg)

        # Estimate wave height from wind speed (simplified)
        # Rule of thumb: wave height (ft) ≈ wind speed (knots) / 10
        wind_knots = wind_speed * 0.868976  # mph to knots
        wave_height = max(1.0, wind_knots / 10)  # Minimum 1ft

        return {
            'wind_speed': round(wind_speed, 1),
            'wind_direction': wind_direction,
            'wave_height': round(wave_height, 1),
            'temperature': round(temperature, 1)
        }

    def _degrees_to_direction(self, degrees: float) -> str:
        """Convert wind degrees to cardinal direction"""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = round(degrees / 45) % 8
        return directions[index]

    async def get_hourly_forecast(self, lat: float, lng: float) -> list:
        """Fetch real hourly forecast data from Open-Meteo"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat,
                'longitude': lng,
                'hourly': 'temperature_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m',
                'temperature_unit': 'fahrenheit',
                'wind_speed_unit': 'mph',
                'timezone': 'auto',
                'forecast_days': 2
            }

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, params=params, timeout=10)
            )
            response.raise_for_status()
            data = response.json()

            hourly_data = data.get('hourly', {})
            times = hourly_data.get('time', [])
            temps = hourly_data.get('temperature_2m', [])
            winds = hourly_data.get('wind_speed_10m', [])
            wind_dirs = hourly_data.get('wind_direction_10m', [])
            gusts = hourly_data.get('wind_gusts_10m', [])

            # Get current hour
            now = datetime.now()
            current_hour = now.hour

            # Build hourly forecast array
            forecast = []
            for i in range(min(24, len(times))):
                if i < len(temps) and i < len(winds):
                    hour_time = datetime.fromisoformat(times[i].replace('Z', '+00:00'))

                    # Convert mph to knots for marine use
                    wind_knots = winds[i] * 0.868976
                    gust_knots = gusts[i] * 0.868976 if i < len(gusts) else wind_knots * 1.3

                    # Estimate wave height from wind
                    wave_height = max(1.0, wind_knots / 10)

                    # Estimate current from wind (simplified)
                    current_speed = wind_knots / 15

                    # Determine rating based on conditions
                    rating = "good"
                    if wind_knots > 20 or wave_height > 4:
                        rating = "planb"
                    elif wind_knots > 15 or wave_height > 3:
                        rating = "caution"
                    elif wind_knots > 10:
                        rating = "fair"

                    # Generate tactical comment
                    comment = self._generate_tactical_comment(wind_knots, wave_height, hour_time.hour)

                    forecast.append({
                        'label': 'Now' if i == 0 else hour_time.strftime('%H:%M'),
                        'time': hour_time.strftime('%I:%M %p'),
                        'wind': f"{self._degrees_to_direction(wind_dirs[i])} {int(wind_knots)} kt",
                        'gust': f"{int(gust_knots)} kt",
                        'seas': f"{wave_height:.1f} ft @ 9s",
                        'current': f"{current_speed:.1f} kt {self._degrees_to_direction(wind_dirs[i])}",
                        'comment': comment,
                        'rating': rating,
                        'temperature': int(temps[i])
                    })

            return forecast

        except Exception as e:
            print(f"Error fetching hourly forecast: {str(e)}")
            return []

    def _generate_tactical_comment(self, wind_knots: float, wave_height: float, hour: int) -> str:
        """Generate tactical fishing comment based on conditions"""
        if wind_knots < 8 and wave_height < 2:
            comments = ["Prime drop", "Glassy calm", "Perfect conditions"]
        elif wind_knots < 12 and wave_height < 3:
            comments = ["Good fishing", "Manageable seas", "Slack, stay on spot"]
        elif wind_knots < 15:
            comments = ["Building breeze", "Slide along ridge", "Steady drift"]
        elif wind_knots < 20:
            comments = ["Windline forming", "Getting choppy", "Monitor conditions"]
        else:
            comments = ["Shift inshore", "Seek shelter", "Plan B time"]

        # Add time-based variations
        if 5 <= hour < 8:
            return comments[0] if wind_knots < 12 else "Dawn window closing"
        elif 17 <= hour < 21:
            return "Evening bite" if wind_knots < 12 else "Evening wind easing"
        elif hour >= 21:
            return "Night calm" if wind_knots < 10 else "Overnight conditions"

        return comments[0]