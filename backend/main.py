from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

from services.planning_service import PlanningService
from services.sonar_service import SonarService
from services.freshness_service import FreshnessService
from services.trip_service import TripService
from services.marine_service import MarineService
from models.schemas import *

load_dotenv()

app = FastAPI(title="LEVIATHAN API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

planning_service = PlanningService()
sonar_service = SonarService()
freshness_service = FreshnessService()
trip_service = TripService()
marine_service = MarineService()

@app.get("/")
async def root():
    return {"message": "LEVIATHAN API - Bringing big insights for small crews"}

@app.post("/api/plan", response_model=PlanResponse)
async def create_plan(request: PlanRequest):
    try:
        return await planning_service.create_plan(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sonar/analyze", response_model=SonarResponse)
async def analyze_sonar(request: SonarRequest):
    try:
        return await sonar_service.analyze_sonar(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/freshness/analyze", response_model=FreshnessResponse)
async def analyze_freshness(request: FreshnessRequest):
    try:
        return await freshness_service.analyze_freshness(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conditions", response_model=MarineConditions)
async def get_marine_conditions(lat: float, lng: float):
    try:
        return await marine_service.get_conditions(lat, lng)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trips", response_model=TripLog)
async def start_trip(request: TripStartRequest):
    try:
        return await trip_service.start_trip(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trips", response_model=list[TripLog])
async def get_trips():
    try:
        return await trip_service.get_trips()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trips/{trip_id}", response_model=TripLog)
async def get_trip(trip_id: str):
    try:
        return await trip_service.get_trip(trip_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Trip not found")

@app.patch("/api/trips/{trip_id}", response_model=TripLog)
async def update_trip(trip_id: str, updates: TripUpdateRequest):
    try:
        return await trip_service.update_trip(trip_id, updates)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Trip not found")

@app.post("/api/trips/{trip_id}/end", response_model=TripLog)
async def end_trip(trip_id: str):
    try:
        return await trip_service.end_trip(trip_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Trip not found")

@app.post("/api/trips/{trip_id}/catches", response_model=CatchRecord)
async def add_catch(trip_id: str, catch_record: CatchCreateRequest):
    try:
        return await trip_service.add_catch(trip_id, catch_record)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Trip not found")

@app.post("/api/upload")
async def upload_image(image: UploadFile = File(...)):
    try:
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, image.filename)
        content = await image.read()

        with open(file_path, "wb") as f:
            f.write(content)

        return {"url": f"/uploads/{image.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)