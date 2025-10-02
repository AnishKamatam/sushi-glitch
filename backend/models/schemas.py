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

class BiteWindow(BaseModel):
    label: str  # e.g., "Dawn Window", "Late Morning", "Plan B"
    window: str  # e.g., "5:20 AM - 7:40 AM"
    action: str  # e.g., "Drop metal jigs on reef peak"
    tide: str  # e.g., "Slack flood"
    confidence: str  # "High", "Medium", "Low", "Contingency"

class HourlyForecast(BaseModel):
    label: str  # e.g., "Now", "07:00"
    time: str  # e.g., "5:30 AM"
    wind: str  # e.g., "NW 8 kt"
    gust: str  # e.g., "12 kt"
    seas: str  # e.g., "2.4 ft @ 9s"
    current: str  # e.g., "0.5 kt NW"
    comment: str  # e.g., "Prime drop"
    rating: str  # "good", "fair", "caution", "planb"
    temperature: Optional[int] = None  # e.g., 60 (Fahrenheit)

class FishermanForecast(BaseModel):
    location_name: str  # e.g., "Coastal Shelf"
    condition_summary: str  # e.g., "Calm dawn seas with light NW windline building after lunch."
    sea_surface_temp: int  # e.g., 56
    air_temp: int  # e.g., 58
    solunar: str  # e.g., "Major 05:48 AM - 07:15 AM · Minor 11:32 AM - 12:10 PM"
    swell_summary: str  # e.g., "2.5 ft WNW @ 9s"
    tide_summary: str  # e.g., "Flooding to +5.7 ft by 09:40"
    warnings: List[str]  # e.g., ["NW windline builds 18 kt after 14:00"]
    marine_summary: Optional[str] = None  # AI-generated analysis of marine conditions
    bite_windows: List[BiteWindow]
    hourly: List[HourlyForecast]

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
    forecast: Optional[FishermanForecast] = None

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