from models.schemas import PlanRequest, PlanResponse
from services.marine_service import MarineService

class PlanningService:
    def __init__(self):
        self.marine_service = MarineService()

    async def create_plan(self, request: PlanRequest) -> PlanResponse:
        # Get marine conditions for the location
        conditions = await self.marine_service.get_conditions(
            request.location.lat,
            request.location.lng
        )

        # For MVP, return a mock plan based on conditions
        # In production, this would use ML models and real data
        return PlanResponse(
            target_species="Rockfish, Lingcod",
            depth_band="80-120 ft",
            time_window="Dawn + 2hrs (5:30-7:30 AM)",
            area_hint="North reef structure, 2nm offshore",
            conditions=conditions,
            fuel_notes="15 gal estimated for 6hr trip",
            safety_notes="VHF Channel 16, EPIRB active",
            plan_b="Shallow water halibut (40-60ft) if conditions worsen",
            confidence=0.87
        )