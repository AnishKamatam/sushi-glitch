import asyncio
from typing import List, Optional
from datetime import datetime
from models.schemas import (
    TripLog, TripStartRequest, TripUpdateRequest,
    CatchRecord, CatchCreateRequest, MarineConditions, LocationModel
)

class TripService:
    def __init__(self):
        # In-memory storage for MVP
        # In production, this would use a database
        self.trips: List[TripLog] = []
        self.trip_counter = 0

    async def start_trip(self, request: TripStartRequest) -> TripLog:
        self.trip_counter += 1
        trip_id = f"trip_{self.trip_counter}_{int(datetime.now().timestamp())}"

        trip = TripLog(
            id=trip_id,
            start_time=request.start_time,
            location=request.location,
            catches=[],
            conditions=MarineConditions(
                wind_speed=0,
                wind_direction='N',
                wave_height=0,
                tide='Unknown',
                lunar='Unknown',
                temperature=0
            )
        )

        self.trips.append(trip)
        return trip

    async def get_trips(self) -> List[TripLog]:
        return self.trips

    async def get_trip(self, trip_id: str) -> Optional[TripLog]:
        for trip in self.trips:
            if trip.id == trip_id:
                return trip
        return None

    async def update_trip(self, trip_id: str, updates: TripUpdateRequest) -> Optional[TripLog]:
        for i, trip in enumerate(self.trips):
            if trip.id == trip_id:
                # Update trip with new values
                if updates.end_time is not None:
                    trip.end_time = updates.end_time
                if updates.fuel_used is not None:
                    trip.fuel_used = updates.fuel_used
                if updates.notes is not None:
                    trip.notes = updates.notes
                if updates.conditions is not None:
                    trip.conditions = updates.conditions

                self.trips[i] = trip
                return trip
        return None

    async def end_trip(self, trip_id: str) -> Optional[TripLog]:
        for i, trip in enumerate(self.trips):
            if trip.id == trip_id:
                trip.end_time = datetime.now().isoformat()
                self.trips[i] = trip
                return trip
        return None

    async def add_catch(self, trip_id: str, catch_request: CatchCreateRequest) -> Optional[CatchRecord]:
        for i, trip in enumerate(self.trips):
            if trip.id == trip_id:
                catch_id = f"catch_{len(trip.catches) + 1}_{int(datetime.now().timestamp())}"

                catch_record = CatchRecord(
                    id=catch_id,
                    timestamp=catch_request.timestamp,
                    species=catch_request.species,
                    weight=catch_request.weight,
                    length=catch_request.length,
                    depth=catch_request.depth,
                    freshness_score=catch_request.freshness_score,
                    sonar_reading=catch_request.sonar_reading,
                    location=catch_request.location
                )

                trip.catches.append(catch_record)
                self.trips[i] = trip
                return catch_record
        return None