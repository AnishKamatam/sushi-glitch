from pydantic import BaseModel
from typing import Optional, List

class MarineConditions(BaseModel):
    wind_speed: float
    wind_direction: str
    wave_height: float
    tide: str
    lunar: str
    temperature: float

class LocationModel(BaseModel):
    lat: float
    lng: float

class PlanRequest(BaseModel):
    location: LocationModel
    target_species: Optional[List[str]] = None
    trip_duration: Optional[int] = None

class PlanResponse(BaseModel):
    target_species: str
    depth_band: str
    time_window: str
    area_hint: str
    conditions: MarineConditions
    fuel_notes: str
    safety_notes: str
    plan_b: str
    confidence: float

class SonarMetadata(BaseModel):
    depth: Optional[float] = None
    timestamp: Optional[str] = None

class SonarRequest(BaseModel):
    image: str  # base64 encoded image
    sonar_type: Optional[str] = None
    metadata: Optional[SonarMetadata] = None

class DetectedObjects(BaseModel):
    fish_arches: int
    bottom_structure: bool
    thermocline: Optional[float] = None

class SonarResponse(BaseModel):
    depth: float
    density: str  # 'sparse' | 'moderate' | 'dense'
    school_width: str  # e.g., '20 ft'
    confidence: float
    recommendation: str
    detected_objects: DetectedObjects
    # Additional analysis fields
    bottom_type: Optional[str] = None
    bottom_depth: Optional[int] = None
    fish_size: Optional[str] = None
    fish_behavior: Optional[str] = None
    baitfish_present: Optional[bool] = None
    species_guess: Optional[str] = None

class FreshnessRequest(BaseModel):
    image: str  # base64 encoded image
    species: Optional[str] = None
    capture_time: Optional[str] = None

class MarketValue(BaseModel):
    estimated_price: float
    quality_factors: List[str]

class FreshnessResponse(BaseModel):
    bleeding: float
    ice_contact: float
    bruising: float
    overall: float
    grade: str  # 'A' | 'B' | 'C' | 'D'
    next_action: str
    timestamp: str
    market_value: MarketValue

class CatchRecord(BaseModel):
    id: str
    timestamp: str
    species: str
    weight: Optional[float] = None
    length: Optional[float] = None
    depth: float
    freshness_score: Optional[FreshnessResponse] = None
    sonar_reading: Optional[SonarResponse] = None
    location: LocationModel

class CatchCreateRequest(BaseModel):
    timestamp: str
    species: str
    weight: Optional[float] = None
    length: Optional[float] = None
    depth: float
    freshness_score: Optional[FreshnessResponse] = None
    sonar_reading: Optional[SonarResponse] = None
    location: LocationModel

class TripLog(BaseModel):
    id: str
    start_time: str
    end_time: Optional[str] = None
    location: LocationModel
    catches: List[CatchRecord] = []
    conditions: MarineConditions
    fuel_used: Optional[float] = None
    notes: Optional[str] = None

class TripStartRequest(BaseModel):
    start_time: str
    location: LocationModel

class TripUpdateRequest(BaseModel):
    end_time: Optional[str] = None
    fuel_used: Optional[float] = None
    notes: Optional[str] = None
    conditions: Optional[MarineConditions] = None