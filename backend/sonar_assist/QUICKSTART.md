# 🚀 Sonar Assist - 5-Minute Quickstart

## What is this?

A real-time AI fishing copilot that **watches your screen**, detects fish on sonar displays, and **speaks recommendations** to you.

**Example output**: *"Large, tight school around 44 feet. Drop to 44 and hold."*

## Installation (2 minutes)

```bash
# 1. Install Python dependencies
cd backend
pip install -r requirements.txt

# 2. (Optional) Install audio support
# macOS:
brew install ffmpeg

# Linux:
sudo apt install ffmpeg

# 3. Add API keys to .env file
nano .env
```

Add these lines to `.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

## Running (1 minute)

```bash
cd backend/sonar_assist
python app.py
```

**Or use the convenience script:**
```bash
./run_sonar_assist.sh
```

## First-Time Setup (2 minutes)

### Step 1: Select Screen Region
1. Press `R` when prompted
2. Drag a rectangle around your sonar display
3. Press ENTER to confirm

### Step 2: Calibrate Depth (Optional)
1. When asked, type `y` or press `C`
2. Click on the **top** depth tick mark (e.g., 0 ft marker)
3. Click on the **bottom** depth tick mark (e.g., 100 ft marker)
4. Enter the actual depth values in feet
5. Done! Calibration is saved.

### Step 3: Watch It Work!
- The app will now watch your sonar display in real-time
- You'll see colored boxes around fish schools
- You'll hear voice recommendations (if ElevenLabs configured)
- If no voice, check the console for text recommendations

## Controls

| Key | Action |
|-----|--------|
| `R` | Select new screen region |
| `C` | Re-calibrate depth |
| `P` | Pause/Resume |
| `O` | Toggle overlay on/off |
| `Q` | Quit |

## Without API Keys?

**It still works!** Just without AI refinement and voice:

- ✅ Fish detection (classical CV)
- ✅ Depth mapping
- ✅ Visual overlay
- ✅ Text recommendations to console
- ❌ No Groq vision refinement
- ❌ No voice output (prints to console instead)

## Testing Your Setup

```bash
cd tests
python test_metrics.py
python test_calibration.py
```

If tests pass, you're good to go!

## Troubleshooting in 30 Seconds

### "No detections showing up"
```bash
# Edit config/default.yaml and reduce thresholds:
cv:
  area_min: 20     # Was: 40
  bin_c: -8        # Was: -5
```

### "Voice not working"
```bash
# 1. Check API key in .env
# 2. Install audio:
pip install simpleaudio
brew install ffmpeg  # or apt install ffmpeg
```

### "Groq errors"
```bash
# Disable Groq in config/default.yaml:
groq:
  use_groq: false
```

### "Performance issues"
```bash
# Reduce FPS in config/default.yaml:
capture:
  target_fps: 10   # Was: 15
```

## Use Cases

### 1. YouTube Sonar Video
1. Open any sonar video on YouTube
2. Run Sonar Assist
3. Select the video player region
4. Get real-time analysis as video plays

### 2. Live Sonar Display
1. Connect fishfinder to screen (HDMI, app, etc.)
2. Run Sonar Assist
3. Select the sonar window
4. Get real-time fishing recommendations

### 3. Review Old Footage
1. Open recorded sonar sessions
2. Run Sonar Assist on playback
3. Analyze past trips

## What Gets Detected?

- 🟢 **Green boxes** = Dense schools (high confidence)
- 🟡 **Yellow boxes** = Moderate density
- 🟠 **Orange boxes** = Sparse marks
- Horizontal lines show depth in feet
- Labels show: depth | size | density

## Example Recommendations

- *"Large, tight school around 44 feet. Drop to 44 and hold."*
- *"School near 36 to 38 feet. Troll through 37 feet."*
- *"Small mark at 22 feet. Worth checking."*
- *"Likely thermocline band - ignore for now."*

## Architecture (For Developers)

```
Screen → CV Detection → Clustering → [Groq AI] → Decision → Voice
         (OpenCV)                    (Optional)            (ElevenLabs)
```

## Full Documentation

- **User Guide**: `README.md` (in this directory)
- **Implementation Guide**: `../../SONAR_ASSIST_GUIDE.md` (project root)
- **Config Reference**: `config/default.yaml` (commented)

## Quick Tips

1. **Good ROI selection**: Make sure selected region is stable and only contains sonar
2. **Calibrate accurately**: Click precisely on depth tick marks
3. **Adjust thresholds**: Every sonar display is different - tune in config file
4. **Start simple**: Try without API keys first, add them later
5. **Check console**: Detailed logs explain what's happening

## Need Help?

1. Run tests: `python tests/test_metrics.py`
2. Check console for error messages
3. Try CV-only mode (disable Groq)
4. Review full README.md
5. Check that ROI is stable and correct

---

**That's it! You're ready to fish smarter.** 🎣

*Press `R` to select your sonar, press `C` to calibrate, and let the AI guide you to the fish!*
