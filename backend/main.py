from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from services.planning_service import PlanningService
from services.sonar_service import SonarService
from services.freshness_service import FreshnessService
from services.trip_service import TripService
from services.marine_service import MarineService
from models.schemas import *

# Import video analyzer
import sys
sys.path.append(str(Path(__file__).parent / "sonar_assist"))
from sonar_assist.video_analyzer import VideoSonarAnalyzer

load_dotenv()

app = FastAPI(title="LEVIATHAN API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://dans-day-here-arm.trycloudflare.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

planning_service = PlanningService()
sonar_service = SonarService()
freshness_service = FreshnessService()
trip_service = TripService()
marine_service = MarineService()
video_analyzer = VideoSonarAnalyzer()

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

@app.post("/api/sonar/analyze-video")
async def analyze_sonar_video(video: UploadFile = File(...)):
    """
    Upload and analyze a sonar video.
    Returns frame-by-frame detections and an annotated video.
    """
    try:
        # Validate file type
        if not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")

        # Create upload directory
        upload_dir = "uploads/videos"
        os.makedirs(upload_dir, exist_ok=True)

        # Save uploaded video
        input_path = os.path.join(upload_dir, video.filename)
        content = await video.read()

        with open(input_path, "wb") as f:
            f.write(content)

        # Generate output filename
        output_filename = f"analyzed_{Path(video.filename).stem}.mp4"
        output_path = os.path.join(upload_dir, output_filename)

        # Analyze video
        detections = await video_analyzer.analyze_video(
            video_path=input_path,
            output_path=output_path,
            enable_tts=False,
            enable_groq=True
        )

        # Calculate summary statistics
        frames_with_fish = sum(1 for d in detections if d['detections'])
        total_detections = sum(len(d['detections']) for d in detections)

        # Extract key moments (frames with large schools)
        key_moments = []
        for d in detections:
            if d['recommendation'] and any(keyword in d['recommendation'].lower()
                                          for keyword in ['large', 'tight', 'dense']):
                key_moments.append({
                    'frame': d['frame'],
                    'timestamp': d['timestamp'],
                    'recommendation': d['recommendation']
                })

        return {
            "success": True,
            "video_url": f"/uploads/videos/{video.filename}",
            "analyzed_video_url": f"/uploads/videos/{output_filename}",
            "summary": {
                "total_frames": len(detections),
                "frames_with_fish": frames_with_fish,
                "total_detections": total_detections,
                "avg_detections_per_frame": round(total_detections / len(detections), 2) if detections else 0
            },
            "key_moments": key_moments[:10],  # Top 10 key moments
            "all_detections": detections
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/uploads/videos/{filename}")
async def get_video(filename: str):
    """Serve uploaded or analyzed videos."""
    file_path = f"uploads/videos/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)