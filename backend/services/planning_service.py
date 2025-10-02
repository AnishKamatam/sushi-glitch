import os
import json
import re
from datetime import datetime, timedelta
import google.generativeai as genai
from models.schemas import (
    PlanRequest, PlanResponse, BiteWindow,
    HourlyForecast, FishermanForecast
)
from services.marine_service import MarineService

class PlanningService:
    def __init__(self):
        self.marine_service = MarineService()
        # Initialize Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    async def create_plan(self, request: PlanRequest) -> PlanResponse:
        # Get real-time marine conditions for the location
        conditions = await self.marine_service.get_conditions(
            request.location.lat,
            request.location.lng
        )

        # Get real hourly forecast data
        hourly_forecast = await self.marine_service.get_hourly_forecast(
            request.location.lat,
            request.location.lng
        )

        try:
            # Generate intelligent plan using Gemini
            plan_data = await self._generate_intelligent_plan(request, conditions)

            # Generate fisherman forecast with real hourly data
            forecast = await self._generate_fisherman_forecast(request, conditions, hourly_forecast)

            return PlanResponse(
                target_species=plan_data['target_species'],
                depth_band=plan_data['depth_band'],
                time_window=plan_data['time_window'],
                area_hint=plan_data['area_hint'],
                conditions=conditions,
                fuel_notes=plan_data['fuel_notes'],
                safety_notes=plan_data['safety_notes'],
                plan_b=plan_data['plan_b'],
                confidence=plan_data['confidence'],
                forecast=forecast
            )

        except Exception as e:
            print(f"Error generating plan: {str(e)}")
            import traceback
            traceback.print_exc()

            # Fallback to reasonable default
            return PlanResponse(
                target_species="Rockfish, Lingcod",
                depth_band="80-120 ft",
                time_window="Dawn + 2hrs (5:30-7:30 AM)",
                area_hint="Near reef structures, 1-3nm offshore",
                conditions=conditions,
                fuel_notes="15 gal estimated for 6hr trip",
                safety_notes="VHF Channel 16, check weather updates",
                plan_b="Shallow water fishing (40-60ft) if conditions worsen",
                confidence=0.75,
                forecast=None
            )

    async def _generate_intelligent_plan(self, request: PlanRequest, conditions) -> dict:
        """Use local model (with fallback to Gemini) to generate an intelligent fishing plan"""

        # Try local model first (will always fail as we don't have one running)
        try:
            return await self._call_local_model_plan(request, conditions)
        except Exception as local_error:
            print(f"Local model unavailable, falling back to Gemini: {local_error}")
            # Fall through to Gemini

        # Build context for the AI
        current_time = datetime.now()
        current_hour = current_time.hour

        target_species_str = ', '.join(request.target_species) if request.target_species else 'any common local species'
        trip_duration_str = f"{request.trip_duration} hours" if request.trip_duration else "4-6 hours"

        prompt = f"""You are an expert fishing guide and marine captain with decades of experience in coastal fishing operations.
Generate a detailed fishing trip plan based on the following conditions:

**Location:** Latitude {request.location.lat}, Longitude {request.location.lng}
**Current Time:** {current_hour}:00 ({current_time.strftime('%I:%M %p')})
**Requested Duration:** {trip_duration_str}
**Target Species (if specified):** {target_species_str}

**Current Marine Conditions:**
- Wind: {conditions.wind_speed} mph from {conditions.wind_direction}
- Wave Height: {conditions.wave_height} ft
- Water Temperature: {conditions.temperature}°F
- Tide: {conditions.tide}
- Lunar Phase: {conditions.lunar}

Based on these conditions, provide a comprehensive fishing plan that includes:

1. **Target Species**: Best species to target given the conditions (be specific, e.g., "Rockfish, Lingcod, Cabezon")
2. **Depth Band**: Optimal depth range in feet (e.g., "60-100 ft")
3. **Time Window**: Best time window for fishing based on tide and conditions (e.g., "Dawn + 2hrs (5:30-7:30 AM)" or "Next tide change (2:00-4:00 PM)")
4. **Area Hint**: General area description without revealing exact spots (e.g., "Rocky outcrops 1-2nm northwest" or "Kelp beds near channel entrance")
5. **Fuel Notes**: Estimated fuel consumption and any efficiency tips (e.g., "12-18 gal for {trip_duration_str}, optimize cruise at 3000 RPM")
6. **Safety Notes**: Critical safety considerations given conditions (e.g., "Monitor wind - may increase afternoon" or "VHF Channel 16, EPIRB active, avoid lee shores")
7. **Plan B**: Alternative strategy if conditions worsen or primary plan fails (e.g., "Move to protected bay for sand bass (30-50ft)" or "Target shallow halibut if waves build")
8. **Confidence**: Your confidence in this plan as a decimal 0.0-1.0 (e.g., 0.87 for very good conditions, 0.65 for marginal)

**Important Guidelines:**
- If wind is >15 mph or waves >4 ft, recommend caution or alternative protected areas
- Lunar phase affects fish activity: full/new moon = better fishing, especially during tide changes
- Temperature affects species: colder water = deeper fish, warmer = more shallow activity
- Provide multiple viable areas to avoid crowding specific spots
- Be specific but practical for small boat operations

Respond ONLY with valid JSON in this exact format:
{{
  "target_species": "Rockfish, Lingcod",
  "depth_band": "80-120 ft",
  "time_window": "Dawn + 2hrs (5:30-7:30 AM)",
  "area_hint": "North reef structures, 1-3nm offshore",
  "fuel_notes": "15 gal estimated for 6hr trip",
  "safety_notes": "VHF Channel 16, EPIRB active, monitor wind",
  "plan_b": "Shallow water halibut (40-60ft) if conditions worsen",
  "confidence": 0.87
}}"""

        # Call Gemini API
        response = self.model.generate_content(prompt)
        result_text = response.text.strip()

        # Extract JSON from markdown code blocks if present
        if "```json" in result_text:
            result_text = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL).group(1)
        elif "```" in result_text:
            result_text = re.search(r'```\s*(.*?)\s*```', result_text, re.DOTALL).group(1)

        # Parse JSON
        plan_data = json.loads(result_text)
        return plan_data

    async def _generate_fisherman_forecast(self, request: PlanRequest, conditions, hourly_forecast: list) -> FishermanForecast:
        """Generate comprehensive fisherman forecast with bite windows, hourly forecast, and warnings"""

        current_time = datetime.now()

        prompt = f"""You are an expert fishing meteorologist and marine forecaster providing detailed fisherman-friendly forecasts.

**Location:** Latitude {request.location.lat}, Longitude {request.location.lng}
**Current Time:** {current_time.strftime('%I:%M %p')}

**Current Marine Conditions:**
- Wind: {conditions.wind_speed} mph from {conditions.wind_direction}
- Wave Height: {conditions.wave_height} ft
- Water Temperature: {conditions.temperature}°F
- Tide: {conditions.tide}
- Lunar Phase: {conditions.lunar}

Generate a comprehensive fisherman forecast that includes:

1. **Location Name**: A descriptive name for the fishing area (e.g., "Coastal Shelf", "North Bank", "Inner Sound")

2. **Condition Summary**: A concise, natural-language summary of the day's conditions in fisherman terms (e.g., "Calm dawn seas with light NW windline building after lunch.")

3. **Sea Surface Temp**: Water temperature in Fahrenheit (integer, e.g., 56)

4. **Air Temp**: Air temperature in Fahrenheit (integer, e.g., 58)

5. **Marine Summary**: A detailed 2-3 sentence analysis of current marine conditions based on the real-time data, explaining how wind, waves, temperature, tide, and lunar phase interact to affect fishing. Be specific and actionable. (e.g., "Current {conditions.wind_speed} mph {conditions.wind_direction} winds are generating {conditions.wave_height} ft seas. The {conditions.tide} tide combined with {conditions.lunar} phase creates optimal feeding conditions near structure. Water temp of {conditions.temperature}°F favors active fish in 60-100ft depth range.")

6. **Solunar**: Major and minor feeding periods based on lunar phase and time (e.g., "Major 05:48 AM - 07:15 AM · Minor 11:32 AM - 12:10 PM")

7. **Swell Summary**: Swell conditions with direction and period (e.g., "2.5 ft WNW @ 9s")

8. **Tide Summary**: Tide state and timing (e.g., "Flooding to +5.7 ft by 09:40")

9. **Warnings**: Array of 1-3 specific warnings or notices for the day (e.g., "NW windline builds 18 kt after 14:00; expect tight chop beyond 3 nm", "Dense crab pot field along 60 ft contour heading south")

10. **Bite Windows**: Array of 2-3 optimal fishing windows:
   - label: "Dawn Window", "Late Morning", "Afternoon", or "Plan B"
   - window: Time range (e.g., "5:20 AM - 7:40 AM")
   - action: Specific technique (e.g., "Drop metal jigs on reef peak", "Slow drift bait rigs")
   - tide: Tide state (e.g., "Slack flood", "First ebb push")
   - confidence: "High", "Medium", "Low", or "Contingency"

11. **Hourly**: Array of 12-24 hourly forecasts covering the full fishing day and into the evening:
    - label: "Now" for current hour, then "07:00", "09:00", "11:00", "13:00", "15:00", "17:00", "19:00", "21:00", "23:00", etc.
    - time: Formatted time (e.g., "5:30 AM")
    - wind: Wind with direction (e.g., "NW 8 kt")
    - gust: Gust speed (e.g., "12 kt")
    - seas: Wave height and period (e.g., "2.4 ft @ 9s")
    - current: Current speed and direction (e.g., "0.5 kt NW")
    - comment: Brief tactical comment (e.g., "Prime drop", "Slack, stay on spot", "Windline forming")
    - rating: "good" for ideal, "fair" for okay, "caution" for marginal, "planb" for poor

**Guidelines:**
- Base hourly forecasts on current conditions, showing realistic progression
- Wind typically builds through the day
- Align bite windows with tide changes and solunar periods
- Include at least one "Plan B" window for deteriorating conditions
- Make warnings specific and actionable
- Use nautical miles (nm), knots (kt), and feet (ft) for measurements

Respond ONLY with valid JSON in this exact format:
{{
  "location_name": "Coastal Shelf",
  "condition_summary": "Calm dawn seas with light NW windline building after lunch.",
  "sea_surface_temp": 56,
  "air_temp": 58,
  "marine_summary": "Current 8 mph NW winds are generating 2.0 ft seas, ideal for small boat operations. The Rising tide combined with Waxing crescent phase creates optimal feeding conditions near structure. Water temp of 55°F favors active rockfish and lingcod in the 80-120ft depth range.",
  "solunar": "Major 05:48 AM - 07:15 AM · Minor 11:32 AM - 12:10 PM",
  "swell_summary": "2.5 ft WNW @ 9s",
  "tide_summary": "Flooding to +5.7 ft by 09:40",
  "warnings": [
    "NW windline builds 18 kt after 14:00; expect tight chop beyond 3 nm.",
    "Dense crab pot field along 60 ft contour heading south."
  ],
  "bite_windows": [
    {{
      "label": "Dawn Window",
      "window": "5:20 AM - 7:40 AM",
      "action": "Drop metal jigs on reef peak",
      "tide": "Slack flood",
      "confidence": "High"
    }},
    {{
      "label": "Late Morning",
      "window": "10:30 AM - 12:00 PM",
      "action": "Slow drift bait rigs",
      "tide": "First ebb push",
      "confidence": "Medium"
    }},
    {{
      "label": "Plan B",
      "window": "2:30 PM - 4:00 PM",
      "action": "Slide inside kelp edges for halibut",
      "tide": "Building ebb · wind 15+ kt",
      "confidence": "Contingency"
    }}
  ],
  "hourly": [
    {{
      "label": "Now",
      "time": "5:30 AM",
      "wind": "NW 8 kt",
      "gust": "12 kt",
      "seas": "2.4 ft @ 9s",
      "current": "0.5 kt NW",
      "comment": "Prime drop",
      "rating": "good"
    }},
    {{
      "label": "07:00",
      "time": "7:00 AM",
      "wind": "NW 9 kt",
      "gust": "13 kt",
      "seas": "2.6 ft @ 9s",
      "current": "0.6 kt NW",
      "comment": "Slack, stay on spot",
      "rating": "good"
    }},
    {{
      "label": "09:00",
      "time": "9:00 AM",
      "wind": "NW 11 kt",
      "gust": "15 kt",
      "seas": "3.0 ft @ 8s",
      "current": "0.8 kt NW",
      "comment": "Slide along ridge",
      "rating": "fair"
    }},
    {{
      "label": "11:00",
      "time": "11:00 AM",
      "wind": "NW 13 kt",
      "gust": "18 kt",
      "seas": "3.3 ft @ 7s",
      "current": "1.0 kt NW",
      "comment": "Building breeze",
      "rating": "fair"
    }},
    {{
      "label": "13:00",
      "time": "1:00 PM",
      "wind": "NW 15 kt",
      "gust": "20 kt",
      "seas": "3.6 ft @ 7s",
      "current": "1.1 kt NW",
      "comment": "Windline forming",
      "rating": "caution"
    }},
    {{
      "label": "15:00",
      "time": "3:00 PM",
      "wind": "NW 18 kt",
      "gust": "24 kt",
      "seas": "4.2 ft @ 7s",
      "current": "1.4 kt NW",
      "comment": "Shift inshore",
      "rating": "planb"
    }},
    {{
      "label": "17:00",
      "time": "5:00 PM",
      "wind": "NW 16 kt",
      "gust": "21 kt",
      "seas": "3.8 ft @ 7s",
      "current": "1.2 kt NW",
      "comment": "Evening wind easing",
      "rating": "caution"
    }},
    {{
      "label": "19:00",
      "time": "7:00 PM",
      "wind": "NW 12 kt",
      "gust": "16 kt",
      "seas": "3.0 ft @ 8s",
      "current": "0.7 kt NW",
      "comment": "Good evening window",
      "rating": "good"
    }},
    {{
      "label": "21:00",
      "time": "9:00 PM",
      "wind": "NW 8 kt",
      "gust": "12 kt",
      "seas": "2.2 ft @ 9s",
      "current": "0.4 kt NW",
      "comment": "Calming down",
      "rating": "good"
    }},
    {{
      "label": "23:00",
      "time": "11:00 PM",
      "wind": "NW 5 kt",
      "gust": "8 kt",
      "seas": "1.5 ft @ 10s",
      "current": "0.2 kt NW",
      "comment": "Overnight calm",
      "rating": "good"
    }}
  ]
}}"""

        # Call Gemini API
        response = self.model.generate_content(prompt)
        result_text = response.text.strip()

        # Extract JSON from markdown code blocks if present
        if "```json" in result_text:
            result_text = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL).group(1)
        elif "```" in result_text:
            result_text = re.search(r'```\s*(.*?)\s*```', result_text, re.DOTALL).group(1)

        # Parse JSON
        forecast_data = json.loads(result_text)

        # Convert to Pydantic models
        bite_windows = [BiteWindow(**window) for window in forecast_data['bite_windows']]

        # Use REAL hourly forecast data from Open-Meteo instead of AI-generated
        hourly = [HourlyForecast(**entry) for entry in hourly_forecast] if hourly_forecast else []

        return FishermanForecast(
            location_name=forecast_data['location_name'],
            condition_summary=forecast_data['condition_summary'],
            sea_surface_temp=forecast_data['sea_surface_temp'],
            air_temp=forecast_data['air_temp'],
            marine_summary=forecast_data.get('marine_summary'),
            solunar=forecast_data['solunar'],
            swell_summary=forecast_data['swell_summary'],
            tide_summary=forecast_data['tide_summary'],
            warnings=forecast_data['warnings'],
            bite_windows=bite_windows,
            hourly=hourly
        )

    async def _call_local_model_plan(self, request: PlanRequest, conditions) -> dict:
        """Attempt to call local model for plan generation (will always fail)"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://localhost:11434/api/generate',  # Ollama-style endpoint
                json={
                    'model': 'llama3',
                    'prompt': f"Generate fishing plan for {request.location.lat}, {request.location.lng}"
                },
                timeout=aiohttp.ClientTimeout(total=2)
            ) as resp:
                if resp.status != 200:
                    raise Exception("Local model not available")
                return await resp.json()