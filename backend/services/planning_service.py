import os
import json
import re
from datetime import datetime
import google.generativeai as genai
from models.schemas import PlanRequest, PlanResponse
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

        try:
            # Generate intelligent plan using Gemini
            plan_data = await self._generate_intelligent_plan(request, conditions)

            return PlanResponse(
                target_species=plan_data['target_species'],
                depth_band=plan_data['depth_band'],
                time_window=plan_data['time_window'],
                area_hint=plan_data['area_hint'],
                conditions=conditions,
                fuel_notes=plan_data['fuel_notes'],
                safety_notes=plan_data['safety_notes'],
                plan_b=plan_data['plan_b'],
                confidence=plan_data['confidence']
            )

        except Exception as e:
            print(f"Error generating plan: {str(e)}")
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
                confidence=0.75
            )

    async def _generate_intelligent_plan(self, request: PlanRequest, conditions) -> dict:
        """Use Gemini to generate an intelligent fishing plan based on conditions"""

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