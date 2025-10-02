# 🎣 Sonar Assist - Real-Time Fishing Copilot

A real-time screen-watching fishing copilot that uses computer vision and AI to analyze sonar displays, detect fish schools, and provide voice recommendations to anglers.

## Features

- **Real-Time Screen Capture**: Watches a selected region of your screen where sonar video plays
- **Classical CV Detection**: Fast fish/school detection using OpenCV (adaptive thresholding, morphology, contour analysis)
- **Groq Vision AI**: Optional refinement using Groq's free-tier vision model to distinguish schools from debris/thermoclines
- **Depth Calibration**: Click two depth ticks to map pixels to feet
- **Fish Metrics**:
  - Density classification (sparse/moderate/dense)
  - School size estimation (small/medium/large)
  - Tightness/compactness scoring
  - Centroid tracking with velocity
- **Voice Cues**: Low-latency ElevenLabs TTS for actionable recommendations
  - "Large, tight school around 44 feet. Drop to 44 and hold."
  - "School near 36 to 38 feet. Troll through 37 feet."
- **Smart Debouncing**: Prevents repetitive announcements
- **On-Screen Overlay**: Visual feedback with bounding boxes, depth lines, and recommendations

## Requirements

- Python 3.10+
- OpenCV
- Screen capture library (mss)
- Optional: Groq API key (free tier)
- Optional: ElevenLabs API key
- Optional: ffmpeg (for audio playback)

## Installation

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Additional for audio playback:**

```bash
pip install simpleaudio
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download ffmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

### 2. Configure API Keys

Create or update `.env` file in `backend/` directory:

```bash
# AI Service API Keys
GEMINI_API_KEY=your_gemini_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Model Configuration
GEMINI_MODEL=gemini-2.5-flash-lite
ELEVENLABS_MODEL=eleven_multilingual_v2
ELEVENLABS_VOICE_ID=pqHfZKP75CvOlQylNhV4
```

### 3. Choosing a Groq Free-Tier Model

Sonar Assist uses Groq's vision models to refine detections. The default model is:

- **Model ID**: `llama-3.2-90b-vision-preview`
- **Endpoint**: `https://api.groq.com/openai/v1/chat/completions`

To use a different model:

1. Visit [Groq Console](https://console.groq.com/)
2. Check available vision models in your tier
3. Update `backend/sonar_assist/config/default.yaml`:

```yaml
groq:
  use_groq: true
  model_id: "your-preferred-model-id"
  endpoint: "https://api.groq.com/openai/v1/chat/completions"
  sample_rate_hz: 1  # Query frequency (1 Hz = once per second)
```

**Note**: The application works perfectly fine **without** Groq - it will fall back to classical CV only.

## Usage

### Running Sonar Assist

```bash
cd backend/sonar_assist
python app.py
```

### First-Time Setup

1. **Select ROI** (Region of Interest):
   - Press `R` or wait for prompt
   - Drag a rectangle around your sonar display
   - Press ENTER to confirm

2. **Calibrate Depth** (optional but recommended):
   - Press `C` or respond to prompt
   - Click on the **top** depth tick (e.g., 0 ft)
   - Click on the **bottom** depth tick (e.g., 100 ft)
   - Enter the actual depth values in feet
   - Calibration is saved to config

### Keyboard Controls

| Key | Action |
|-----|--------|
| `R` | Select screen region (ROI) |
| `C` | Calibrate depth mapping |
| `P` | Pause/Resume processing |
| `O` | Toggle overlay visibility |
| `Q` | Quit application |

### Output

- **Visual Overlay**:
  - Green boxes = dense schools
  - Yellow boxes = moderate density
  - Orange boxes = sparse marks
  - Horizontal lines show depth
  - Labels show depth (ft), size, and density

- **Voice Cues**: Spoken recommendations via ElevenLabs TTS (if configured)

- **Console Output**: Fallback text cues if TTS unavailable

## Configuration

Edit `backend/sonar_assist/config/default.yaml` to customize:

### Computer Vision Parameters

```yaml
cv:
  area_min: 40              # Minimum detection area (px²)
  area_max: 20000           # Maximum detection area (px²)
  density_thr: 140.0        # Intensity threshold for "dense"
  tightness_thr: 0.70       # Compactness threshold for "tight"
  bin_block: 21             # Adaptive threshold block size
  bin_c: -5                 # Adaptive threshold constant
```

### Speech/TTS Settings

```yaml
speech:
  debounce_sec: 2.5         # Minimum seconds between similar cues
  min_confidence: 0.6       # Minimum confidence to speak
```

### Groq Settings

```yaml
groq:
  use_groq: true            # Enable/disable Groq vision
  sample_rate_hz: 1         # Query frequency (1 = once/second)
  timeout_sec: 10           # API timeout
```

### Decision Thresholds

```yaml
decision:
  large_school_area: 5000   # Area threshold for "large" school
  tight_school_compactness: 0.75  # Compactness for "tight"
```

## Testing

Run unit tests:

```bash
cd backend/sonar_assist/tests

# Test metrics module
python test_metrics.py

# Test calibration module
python test_calibration.py
```

Expected output:
```
============================================================
Running Metrics Module Tests
============================================================

✓ test_detection_creation passed
✓ test_preprocess_frame passed
✓ test_detect_fish passed (found 2 detections)
✓ test_classify_density passed
✓ test_calculate_school_size passed
✓ test_cluster_detections passed

============================================================
✓ All tests passed!
============================================================
```

## Troubleshooting

### No detections appearing

1. **Check ROI**: Make sure selected region covers the sonar display
2. **Check threshold params**: Adjust `bin_block` and `bin_c` in config
3. **Verify preprocessing**: Try different `clahe_clip_limit` values
4. **Inspect frame**: Add `cv2.imwrite("debug.png", frame)` to save captured frames

### Voice not working

1. **Check API key**: Verify `ELEVENLABS_API_KEY` in `.env`
2. **Install audio library**: `pip install simpleaudio`
3. **Install ffmpeg**: Required for MP3→WAV conversion
4. **Fallback**: If TTS fails, cues print to console

### Groq errors

1. **Check API key**: Verify `GROQ_API_KEY` in `.env`
2. **Check model ID**: Ensure model is available in your tier
3. **Disable Groq**: Set `use_groq: false` in config to use CV only
4. **Check rate limits**: Free tier has request limits

### Low FPS / Performance

1. **Reduce target FPS**: Lower `capture.target_fps` in config (default 15)
2. **Reduce Groq frequency**: Lower `groq.sample_rate_hz` (default 1 Hz)
3. **Disable overlay**: Press `O` to turn off visual overlay
4. **Reduce ROI size**: Select smaller screen region

### Calibration issues

1. **Click accurately**: Ensure you click precisely on depth tick marks
2. **Use clear ticks**: Choose top/bottom ticks that are clearly visible
3. **Verify range**: Use `calibrator.get_depth_range()` to check values
4. **Re-calibrate**: Press `C` anytime to re-run calibration

## Architecture

```
backend/sonar_assist/
├── app.py                    # Main application loop
├── calibration.py            # Depth pixel→feet mapping
├── metrics.py                # CV detection & tracking
├── groq_cv.py               # Groq vision model client
├── tts_elevenlabs.py        # ElevenLabs TTS client
├── config/
│   └── default.yaml         # Configuration file
└── tests/
    ├── test_metrics.py      # Metrics unit tests
    └── test_calibration.py  # Calibration unit tests
```

### Data Flow

```
Screen Capture (mss)
    ↓
Preprocessing (grayscale, CLAHE, blur)
    ↓
Classical CV Detection (threshold, morphology, contours)
    ↓
Clustering (merge nearby detections)
    ↓
[Optional] Groq Vision Refinement (sampled at 1 Hz)
    ↓
Tracking (centroid tracker)
    ↓
Metrics Calculation (depth, density, size, tightness)
    ↓
Decision Engine (generate recommendation)
    ↓
TTS Output (ElevenLabs) + Visual Overlay
```

## Graceful Degradation

Sonar Assist works with **zero API keys** configured:

- **No Groq key**: Uses classical CV only
- **No ElevenLabs key**: Prints cues to console
- **No ffmpeg/audio**: Prints cues to console
- **Core functionality** (detection, tracking, overlay) always works

## Performance

- **Target FPS**: 15 Hz (configurable)
- **Groq queries**: 1 Hz (configurable, can be disabled)
- **Typical CPU usage**: 10-20% on modern laptops
- **Latency**: <100ms from detection to voice cue (with good internet)

## Examples

### Example Cues

- **Dense school at depth**:
  *"Large, tight school around 44 feet. Drop to 44 and hold."*

- **Moderate school**:
  *"School near 36 to 38 feet. Troll through 37 feet."*

- **Small mark**:
  *"Small mark at 22 feet. Worth checking."*

- **Thermocline detected** (with Groq):
  *"Likely thermocline band - ignore for now."*

## Contributing

This is a hackathon/MVP project. Contributions welcome!

Potential improvements:
- [ ] Add historical tracking graphs
- [ ] Export detections to CSV/JSON
- [ ] Support for multiple sonar types (side-scan, down-imaging)
- [ ] Mobile app integration
- [ ] Cloud storage for trip logs
- [ ] Species identification integration

## License

MIT License - see main project README

## Support

For issues and questions:
- Check troubleshooting section above
- Review config file comments
- Run unit tests to verify installation
- Check console logs for detailed error messages

---

**Built for LEVIATHAN - Bringing big insights for small crews** 🎣
