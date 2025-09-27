# LEVIATHAN - Fishing Copilot

**Bringing big insights for small crews**

LEVIATHAN is a comprehensive fishing assistant web application designed for small boats and solo skippers. It provides AI-powered insights for trip planning, sonar analysis, and fish freshness assessment to maximize catch value and trip efficiency.

## Features

### Pre-Departure Planner
- Marine weather, tide, current, and lunar data integration
- Target species and depth recommendations
- Optimal time window suggestions
- Area hints and backup plans
- Fuel and safety planning

### Sonar Assist with TTS
- Upload sonar screenshots for AI analysis
- Real-time fish detection and school assessment
- Audio cues via Text-to-Speech
- Depth, density, and school size analysis
- Actionable fishing recommendations

### Freshness QA
- Camera-based fish freshness assessment
- Bleeding, ice contact, and bruising evaluation
- Market grade scoring (A-D)
- Next action recommendations
- Trip-long freshness tracking

### Additional Features
- **Offline-first design** - Works without internet connection
- **Trip logging** - Automatic catch and condition logging
- **Local storage** - All data stored locally for privacy
- **Mobile-optimized** - Designed for phone use on deck
- **Progressive Web App** - Install like a native app

## Tech Stack
- **Frontend**: React 18 with JavaScript
- **Backend**: Python FastAPI
- **UI**: Custom CSS with responsive design
- **Storage**: Browser localStorage for offline functionality
- **PWA**: Service Worker for offline capabilities
- **APIs**: Web Speech API for TTS, Camera API for image capture

## Getting Started

### Prerequisites
- Node.js 16+
- Python 3.8+
- npm or yarn
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd sushi-glitch
```

2. Install all dependencies:
```bash
npm run install-all
```

3. Start both frontend and backend:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
sushi-glitch/
├── frontend/                    # React JavaScript app
│   ├── public/
│   │   ├── manifest.json       # PWA manifest
│   │   └── sw.js              # Service worker
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── PlanCard.js    # Trip planning interface
│   │   │   ├── SonarAssist.js # Sonar analysis interface
│   │   │   └── FreshnessQA.js # Freshness assessment interface
│   │   ├── services/          # Service layer
│   │   │   ├── api.js         # API service with mock data
│   │   │   ├── storage.js     # Local storage management
│   │   │   └── serviceWorker.js # PWA service worker registration
│   │   ├── App.js             # Main application component
│   │   └── index.js           # Application entry point
├── backend/                     # Python FastAPI backend
│   ├── models/
│   │   └── schemas.py          # Pydantic data models
│   ├── services/               # Business logic services
│   │   ├── planning_service.py # Trip planning logic
│   │   ├── sonar_service.py    # Sonar analysis service
│   │   ├── freshness_service.py # Freshness assessment service
│   │   ├── trip_service.py     # Trip management service
│   │   └── marine_service.py   # Marine conditions service
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   └── .env.example           # Environment configuration
└── package.json               # Root package with scripts
```

## Backend Implementation Guide

### Core Services Architecture

The backend is built with FastAPI and follows a modular service architecture. Each service handles specific functionality:

#### 1. Planning Service (`planning_service.py`)
**Purpose**: Generate fishing plans based on marine conditions and user preferences

**Key Functions**:
```python
async def create_plan(self, request: PlanRequest) -> PlanResponse:
    # Integrates with marine service to get conditions
    # Returns optimized fishing plan with:
    # - Target species recommendations
    # - Optimal depth bands
    # - Best time windows
    # - Area suggestions
    # - Fuel estimates
    # - Safety notes
    # - Backup plans
```

**Frontend Connection**: Called when user needs a fishing plan in the Plan Card component

#### 2. Sonar Service (`sonar_service.py`)
**Purpose**: Analyze sonar screenshots using computer vision

**Key Functions**:
```python
async def analyze_sonar(self, request: SonarRequest) -> SonarResponse:
    # Processes base64 encoded sonar images
    # Returns fish detection analysis:
    # - School depth and density
    # - Fish arch count
    # - Bottom structure detection
    # - Confidence scores
    # - Actionable recommendations
```

**Frontend Connection**: Processes images uploaded in Sonar Assist component, returns spoken recommendations

#### 3. Freshness Service (`freshness_service.py`)
**Purpose**: Assess fish freshness using on-device computer vision

**Key Functions**:
```python
async def analyze_freshness(self, request: FreshnessRequest) -> FreshnessResponse:
    # Analyzes fish photos for freshness indicators:
    # - Bleeding completeness (0-100%)
    # - Ice contact quality (0-100%)
    # - Bruising assessment (0-100%)
    # - Overall grade (A-D)
    # - Market value estimates
    # - Next action recommendations
```

**Frontend Connection**: Processes camera captures in Freshness QA component

#### 4. Trip Service (`trip_service.py`)
**Purpose**: Manage trip logging and catch records

**Key Functions**:
```python
async def start_trip(self, request: TripStartRequest) -> TripLog
async def add_catch(self, trip_id: str, catch: CatchCreateRequest) -> CatchRecord
async def end_trip(self, trip_id: str) -> TripLog
async def get_trips(self) -> List[TripLog]
```

**Frontend Connection**: Manages trip state across all components

#### 5. Marine Service (`marine_service.py`)
**Purpose**: Fetch and process marine environmental data

**Key Functions**:
```python
async def get_conditions(self, lat: float, lng: float) -> MarineConditions:
    # Integrates with marine data APIs (NOAA, weather services)
    # Returns current conditions:
    # - Wind speed/direction
    # - Wave height
    # - Tide state
    # - Lunar phase
    # - Water temperature
```

**Frontend Connection**: Provides environmental data for all planning decisions

### Frontend-Backend Integration

#### API Communication Flow

1. **Frontend API Service** (`frontend/src/services/api.js`):
   ```javascript
   // Calls backend endpoints
   const response = await fetch(`${API_BASE_URL}/api/plan`, {
     method: 'POST',
     body: JSON.stringify(planRequest)
   });
   ```

2. **Backend Endpoints** (`backend/main.py`):
   ```python
   @app.post("/api/plan", response_model=PlanResponse)
   async def create_plan(request: PlanRequest):
       return await planning_service.create_plan(request)
   ```

#### Data Flow Example: Sonar Analysis

1. **User Action**: Uploads sonar image in SonarAssist component
2. **Frontend**: Converts image to base64, sends to `/api/sonar/analyze`
3. **Backend**: SonarService processes image, returns analysis
4. **Frontend**: Displays results, speaks recommendation via TTS
5. **Storage**: Saves reading to localStorage for offline access

### Implementation Steps for Production

#### Phase 1: Replace Mock Services
```python
# Current: Mock data
return {
    "target_species": "Rockfish, Lingcod",
    "confidence": 0.87
}

# Production: Real ML models
model_output = await ml_model.predict(marine_data)
return PlanResponse(**model_output)
```

#### Phase 2: Add Real AI Models

**Sonar Analysis**:
```python
# Use computer vision models (OpenCV, TensorFlow)
async def analyze_sonar_image(self, image_data):
    # Load pre-trained fish detection model
    # Process sonar image for fish arches
    # Return structured analysis
```

**Freshness Assessment**:
```python
# Use lightweight vision models for on-device processing
async def assess_freshness(self, fish_image):
    # Analyze bleeding patterns
    # Detect ice contact areas
    # Assess bruising/damage
    # Calculate market grade
```

#### Phase 3: External API Integration

**Marine Data**:
```python
# Integrate with NOAA, weather services
async def fetch_marine_conditions(self, lat, lng):
    noaa_data = await self.fetch_noaa_api(lat, lng)
    weather_data = await self.fetch_weather_api(lat, lng)
    return self.combine_marine_data(noaa_data, weather_data)
```

### Environment Configuration

Create `.env` file in backend directory:
```env
# API Keys for marine data
NOAA_API_KEY=your_key_here
WEATHER_API_KEY=your_key_here

# Database (for production)
DATABASE_URL=postgresql://user:pass@localhost/leviathan

# ML Model paths
SONAR_MODEL_PATH=/models/sonar_detection.onnx
FRESHNESS_MODEL_PATH=/models/freshness_assessment.onnx
```

### Running the Application

**Development Mode**:
```bash
# Start both frontend and backend
npm run dev

# Or separately:
npm run frontend  # React dev server on :3000
npm run backend   # FastAPI server on :8000
```

**Production Build**:
```bash
# Build frontend
npm run build

# Deploy backend with production ASGI server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

The architecture ensures the frontend can work offline with mock data while the backend provides real AI-powered analysis when connected. All services are designed to be modular and easily replaceable as you implement production ML models.

## Usage

### Trip Planning
1. Navigate to the **Plan Card** tab
2. Review marine conditions and recommendations
3. Note target species, depth bands, and optimal timing
4. Click "Start Trip Log" to begin tracking

### Sonar Analysis
1. Go to the **Sonar Assist** tab
2. Upload a sonar screenshot or capture from camera
3. Wait for AI analysis (2-3 seconds)
4. Listen to audio recommendations
5. Follow depth and positioning guidance

### Freshness Assessment
1. Open the **Freshness QA** tab
2. Use camera to photograph caught fish
3. Review bleeding, ice contact, and bruising scores
4. Follow next action recommendations
5. Track improvement over the trip

## Offline Capabilities

- **Service Worker** caches app resources and API responses
- **Local Storage** maintains trip data and user preferences
- **Background Sync** queues data for upload when online
- **Cache-first strategy** for optimal performance

## Target Users

- Small boat operators (1-4 crew)
- Solo fishing skippers
- Coastal fishing operations
- Recreational fishermen seeking to optimize catches

## Key Performance Indicators

- **Primary**: Auction price premium through improved freshness
- **Secondary**: Catch per unit effort, fuel efficiency, handling defect rate
- **Tracking**: On-device scoring with before/after comparisons

## Development Roadmap

### Phase 1 (Complete)
- Basic app structure and navigation
- Mock data and UI components
- Offline functionality
- Image capture and analysis UI

### Phase 2 (In Progress)
- Real AI models for sonar and freshness analysis
- FastAPI backend integration
- Marine data API connections
- Enhanced trip analytics

### Phase 3 (Future)
- NMEA sonar integration
- Species-specific handling guides
- Market price integration
- Multi-user fleet management

---

**LEVIATHAN** - *Bringing big insights for small crews*