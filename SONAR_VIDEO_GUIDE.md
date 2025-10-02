# 🎣 Sonar Assist - Video Upload Guide

## Your Vision: Upload Video → Get Analysis ✅

**This is now complete!** Upload a sonar video and get:
- Frame-by-frame fish detection
- Annotated video with bounding boxes
- Key moments with recommendations
- Summary statistics

---

## 🚀 Quick Start (2 Minutes)

### Step 1: Install Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

### Step 2: Start Backend

```bash
cd backend
python3 main.py
```

Backend runs at `http://localhost:8000`

### Step 3: Test It!

```bash
# From project root
python3 test_video_upload.py path/to/your/sonar_video.mp4
```

---

## 📹 How to Use

### Method 1: Python Test Script (Easiest)

```bash
python3 test_video_upload.py my_fishing_video.mp4
```

**Output:**
```
🎣 Testing Sonar Video Analysis
📹 Video: my_fishing_video.mp4
📊 Uploading to backend...

✅ Analysis Complete!

📊 Summary:
  Total frames: 450
  Frames with fish: 127
  Total detections: 243
  Avg detections/frame: 0.54

🎯 Key Moments:
  1. Frame 145 (4.8s):
     Large, tight school around 44 feet. Drop to 44 and hold.
  2. Frame 289 (9.6s):
     School near 36 feet. Dense density.

📹 Videos:
  Analyzed: http://localhost:8000/uploads/videos/analyzed_my_fishing_video.mp4
```

### Method 2: curl (Command Line)

```bash
curl -X POST "http://localhost:8000/api/sonar/analyze-video" \
  -F "video=@my_video.mp4" \
  | python3 -m json.tool
```

### Method 3: Python Requests

```python
import requests

with open("sonar_video.mp4", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/sonar/analyze-video",
        files={"video": f}
    )

result = response.json()
print(f"Found {result['summary']['total_detections']} fish!")
print(f"Watch analyzed video: {result['analyzed_video_url']}")
```

### Method 4: Web Browser (Simple HTML)

Create `upload_test.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Sonar Video Analyzer</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; }
        button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
        video { margin-top: 20px; }
        #status { margin: 20px 0; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🎣 Sonar Video Analyzer</h1>
    <input type="file" id="videoInput" accept="video/*">
    <button onclick="uploadVideo()">Analyze Video</button>
    <div id="status"></div>
    <div id="result"></div>

    <script>
    async function uploadVideo() {
        const file = document.getElementById('videoInput').files[0];
        if (!file) {
            alert('Please select a video file');
            return;
        }

        const formData = new FormData();
        formData.append('video', file);

        document.getElementById('status').innerHTML = '⏳ Analyzing... (this may take a minute)';
        document.getElementById('result').innerHTML = '';

        try {
            const response = await fetch('http://localhost:8000/api/sonar/analyze-video', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            document.getElementById('status').innerHTML = '✅ Analysis Complete!';
            document.getElementById('result').innerHTML = `
                <h2>Results</h2>
                <p><strong>Total Detections:</strong> ${result.summary.total_detections}</p>
                <p><strong>Frames with Fish:</strong> ${result.summary.frames_with_fish} / ${result.summary.total_frames}</p>

                <h3>Analyzed Video</h3>
                <video controls width="600">
                    <source src="http://localhost:8000${result.analyzed_video_url}" type="video/mp4">
                </video>

                <h3>Key Moments</h3>
                <ul>
                    ${result.key_moments.map(m =>
                        `<li><strong>${m.timestamp.toFixed(1)}s</strong>: ${m.recommendation}</li>`
                    ).join('')}
                </ul>
            `;
        } catch (error) {
            document.getElementById('status').innerHTML = '❌ Error: ' + error.message;
        }
    }
    </script>
</body>
</html>
```

Open `upload_test.html` in your browser!

---

## 🎨 What You Get

### 1. Analyzed Video with Overlays

- **Green boxes** = Dense schools (high confidence)
- **Yellow boxes** = Moderate density
- **Orange boxes** = Sparse marks
- **Depth labels** = "44ft | large | dense"
- **Recommendations** = Overlaid text with fishing advice

### 2. JSON Response

```json
{
  "success": true,
  "video_url": "/uploads/videos/original.mp4",
  "analyzed_video_url": "/uploads/videos/analyzed_original.mp4",
  "summary": {
    "total_frames": 450,
    "frames_with_fish": 127,
    "total_detections": 243,
    "avg_detections_per_frame": 0.54
  },
  "key_moments": [
    {
      "frame": 145,
      "timestamp": 4.8,
      "recommendation": "Large, tight school around 44 feet. Drop to 44 and hold."
    }
  ],
  "all_detections": [
    {
      "frame": 1,
      "timestamp": 0.033,
      "detections": [...],
      "recommendation": "..."
    }
  ]
}
```

---

## 🔧 Configuration

Edit `backend/sonar_assist/config/default.yaml` to tune detection:

```yaml
cv:
  area_min: 40          # Minimum fish size (pixels²)
  area_max: 20000       # Maximum detection size
  density_thr: 140.0    # Brightness threshold
  tightness_thr: 0.70   # How compact schools must be

groq:
  use_groq: true        # Enable AI refinement
  sample_rate_hz: 1     # How often to query Groq (1 = once/sec)

speech:
  min_confidence: 0.6   # Minimum confidence to report
```

**Too sensitive?** Increase `area_min` and `density_thr`

**Missing fish?** Decrease `area_min` and `bin_c: -10`

---

## 🏗️ Architecture

```
Upload Video (MP4/AVI/MOV)
        ↓
   Save to disk
        ↓
   Extract frames (OpenCV)
        ↓
   For each frame:
     ├─ Preprocess (grayscale, CLAHE)
     ├─ Detect fish (thresholding, contours)
     ├─ Calculate metrics (density, size, depth)
     ├─ Optional: Groq AI refinement
     └─ Generate recommendation
        ↓
   Annotate frames
        ↓
   Encode to MP4
        ↓
   Return results + video URL
```

---

## 📊 Performance

| Video Length | Processing Time | Notes |
|--------------|-----------------|-------|
| 30 seconds   | ~15-30 seconds  | Quick analysis |
| 2 minutes    | ~1-2 minutes    | Standard |
| 10 minutes   | ~5-10 minutes   | Full session |

**Processing ratio: ~1:1** (1 min video = 1 min processing)

---

## 🎓 Example Recommendations

What the AI says:

- **Dense school**: *"Large, tight school around 44 feet. Drop to 44 and hold."*
- **Moderate**: *"School near 36 feet. Dense density."*
- **Small mark**: *"Small mark at 22 feet."*
- **Thermocline**: *"Likely thermocline band - ignore for now."* (with Groq enabled)

---

## 🐛 Troubleshooting

### Backend won't start

```bash
cd backend
pip3 install -r requirements.txt
python3 main.py
```

### "No fish detected" but there are fish

Edit `backend/sonar_assist/config/default.yaml`:

```yaml
cv:
  area_min: 20      # Lower = more sensitive
  bin_c: -10        # More negative = more detections
```

### Video upload fails

- Check video format (MP4 recommended)
- Ensure video isn't corrupted
- Check file size (< 500MB recommended)

### Slow processing

- Normal! Video analysis takes time
- Disable Groq: Set `groq.use_groq: false` in config
- Process shorter clips

---

## 🔌 API Reference

### POST `/api/sonar/analyze-video`

**Upload and analyze sonar video**

**Request:**
- `video`: Video file (multipart/form-data)

**Response:**
```json
{
  "success": true,
  "video_url": "/uploads/videos/original.mp4",
  "analyzed_video_url": "/uploads/videos/analyzed_original.mp4",
  "summary": {
    "total_frames": 450,
    "frames_with_fish": 127,
    "total_detections": 243,
    "avg_detections_per_frame": 0.54
  },
  "key_moments": [...],
  "all_detections": [...]
}
```

### GET `/uploads/videos/{filename}`

**Download original or analyzed video**

**Response:** Video file (MP4)

---

## 🌐 Integration Examples

### React Frontend

```typescript
const analyzeSonarVideo = async (file: File) => {
  const formData = new FormData();
  formData.append('video', file);

  const response = await fetch('http://localhost:8000/api/sonar/analyze-video', {
    method: 'POST',
    body: formData,
  });

  return response.json();
};

// In component
const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file) return;

  setLoading(true);
  const result = await analyzeSonarVideo(file);
  setLoading(false);

  setAnalyzedVideoUrl(result.analyzed_video_url);
  setKeyMoments(result.key_moments);
};
```

### Mobile App (React Native)

```typescript
import DocumentPicker from 'react-native-document-picker';

const uploadVideo = async () => {
  const file = await DocumentPicker.pick({
    type: [DocumentPicker.types.video],
  });

  const formData = new FormData();
  formData.append('video', {
    uri: file.uri,
    type: file.type,
    name: file.name,
  });

  const response = await fetch('http://YOUR_SERVER:8000/api/sonar/analyze-video', {
    method: 'POST',
    body: formData,
  });

  const result = await response.json();
  // Show results...
};
```

---

## 📁 File Locations

```
backend/
├── main.py                          # FastAPI with video upload endpoint
├── sonar_assist/
│   ├── video_analyzer.py           # Video analysis engine
│   ├── metrics.py                  # Fish detection logic
│   ├── calibration.py              # Depth mapping
│   ├── groq_cv.py                  # AI refinement
│   └── config/default.yaml         # Configuration
└── uploads/videos/                  # Uploaded & analyzed videos

test_video_upload.py                 # Test script
HOW_TO_USE.md                        # This guide
```

---

## ✅ Complete Workflow Example

```bash
# 1. Start backend
cd backend
python3 main.py &

# 2. Upload a video
python3 ../test_video_upload.py my_fishing_trip.mp4

# Output shows:
# - Summary statistics
# - Key moments with timestamps
# - URL to analyzed video

# 3. Download analyzed video
curl "http://localhost:8000/uploads/videos/analyzed_my_fishing_trip.mp4" \
  -o final_output.mp4

# 4. Watch it!
open final_output.mp4
```

---

## 🎯 Next Steps

Now that video upload works, you can:

1. **Add to your mobile app**
   - Record sonar video
   - Upload to backend
   - View annotated results

2. **Build a video gallery**
   - Store all analyzed videos
   - Show thumbnails
   - Filter by date/location

3. **Create highlights**
   - Extract key moments as clips
   - Share on social media
   - Compare trips

4. **Integrate with trips**
   - Attach videos to trip logs
   - Auto-log catches from video
   - Generate trip reports

---

## 🆘 Need Help?

Check these files:
- **This guide**: `HOW_TO_USE.md`
- **API code**: `backend/main.py` lines 133-197
- **Analysis logic**: `backend/sonar_assist/video_analyzer.py`
- **Configuration**: `backend/sonar_assist/config/default.yaml`
- **Full docs**: `backend/sonar_assist/README.md`

---

## 📝 Summary

✅ **Upload sonar video** → `/api/sonar/analyze-video`

✅ **Automatic frame-by-frame analysis** → Fish detection + metrics

✅ **Get annotated video** → Bounding boxes + recommendations

✅ **Key moments extracted** → Timestamps of best spots

✅ **Statistics provided** → Total fish, frames, averages

**Your original vision is complete!** 🎉

Just upload a video and let the AI analyze it for you.

---

**Built for LEVIATHAN - Bringing big insights for small crews** 🎣
