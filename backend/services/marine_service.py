import asyncio
import random
from models.schemas import MarineConditions

class MarineService:
    async def get_conditions(self, lat: float, lng: float) -> MarineConditions:
        # Simulate API call delay
        await asyncio.sleep(0.1)

        # For MVP, return mock marine conditions
        # In production, this would integrate with NOAA, weather APIs, etc.
        return MarineConditions(
            wind_speed=random.uniform(5, 15),
            wind_direction=random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
            wave_height=random.uniform(1, 4),
            tide=random.choice(["Rising", "Falling", "High", "Low"]),
            lunar=random.choice(["New moon", "Waxing crescent", "First quarter", "Waxing gibbous", "Full moon", "Waning gibbous", "Last quarter", "Waning crescent"]),
            temperature=random.uniform(50, 70)
        )