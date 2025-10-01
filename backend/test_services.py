#!/usr/bin/env python3
"""
Debug script to test marine and planning services with Santa Monica location
"""
import asyncio
import os
from dotenv import load_dotenv
from services.marine_service import MarineService
from services.planning_service import PlanningService
from models.schemas import PlanRequest, LocationModel

# Load environment variables
load_dotenv()

async def test_services():
    """Test marine and planning services with Santa Monica coordinates"""

    # Santa Monica, CA coordinates
    SANTA_MONICA_LAT = 34.0195
    SANTA_MONICA_LNG = -118.4912

    print("=" * 60)
    print("LEVIATHAN - Service Debug Test")
    print("=" * 60)
    print(f"Location: Santa Monica, CA")
    print(f"   Latitude: {SANTA_MONICA_LAT}")
    print(f"   Longitude: {SANTA_MONICA_LNG}")
    print()

    # Test Marine Service
    print("=" * 60)
    print("Testing Marine Service")
    print("=" * 60)

    marine_service = MarineService()

    try:
        print("Fetching real-time marine conditions...")
        conditions = await marine_service.get_conditions(SANTA_MONICA_LAT, SANTA_MONICA_LNG)

        print("\nMarine Conditions Retrieved:")
        print(f"   Wind: {conditions.wind_speed} mph from {conditions.wind_direction}")
        print(f"   Wave Height: {conditions.wave_height} ft")
        print(f"   Water Temperature: {conditions.temperature}°F")
        print(f"   Tide: {conditions.tide}")
        print(f"   Lunar Phase: {conditions.lunar}")
        print()

    except Exception as e:
        print(f"\nError fetching marine conditions: {str(e)}")
        return

    # Test Planning Service
    print("=" * 60)
    print("Testing Planning Service")
    print("=" * 60)

    planning_service = PlanningService()

    try:
        print("Generating intelligent fishing plan with Gemini AI...")
        print()

        request = PlanRequest(
            location=LocationModel(lat=SANTA_MONICA_LAT, lng=SANTA_MONICA_LNG),
            target_species=["Halibut", "Calico Bass"],
            trip_duration=6
        )

        plan = await planning_service.create_plan(request)

        print("Fishing Plan Generated:")
        print()
        print(f"   Target Species: {plan.target_species}")
        print(f"   Depth Band: {plan.depth_band}")
        print(f"   Time Window: {plan.time_window}")
        print(f"   Area Hint: {plan.area_hint}")
        print(f"   Fuel Notes: {plan.fuel_notes}")
        print(f"   Safety Notes: {plan.safety_notes}")
        print(f"   Plan B: {plan.plan_b}")
        print(f"   Confidence: {plan.confidence:.2%}")
        print()

        print("   Current Conditions Used:")
        print(f"      Wind: {plan.conditions.wind_speed} mph {plan.conditions.wind_direction}")
        print(f"      Waves: {plan.conditions.wave_height} ft")
        print(f"      Temp: {plan.conditions.temperature}°F")
        print(f"      Tide: {plan.conditions.tide}")
        print(f"      Moon: {plan.conditions.lunar}")
        print()

    except Exception as e:
        print(f"\nError generating plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    print("=" * 60)
    print("All Services Working!")
    print("=" * 60)

if __name__ == "__main__":
    # Check for API key
    if not os.getenv('GEMINI_API_KEY'):
        print("ERROR: GEMINI_API_KEY not found in environment")
        print("   Please add it to backend/.env file")
        exit(1)

    asyncio.run(test_services())
