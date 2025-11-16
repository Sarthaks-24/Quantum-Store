# Video Processor - Quick Reference

## What It Does
Extracts metadata from video files (duration, resolution, FPS)

## Main Function
```python
processor = VideoProcessor()
result = processor.analyze(file_path)
```

## Output Example
```json
{
  "type": "video",
  "width": 1920,
  "height": 1080,
  "fps": 30.0,
  "frame_count": 7200,
  "duration_seconds": 240.0,
  "duration_formatted": "4m 0s",
  "file_size": 52428800,
  "content_category": "videos_medium",
  "processed": true
}
```

## Libraries Used
- **OpenCV (cv2):** Video metadata extraction
- **Fallback:** File size-based categorization if OpenCV unavailable

## How It Works

### Step 1: Open Video
```python
import cv2

cap = cv2.VideoCapture(file_path)

if not cap.isOpened():
    return self._fallback_analysis(file_path)
```

### Step 2: Get Properties
```python
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Calculate duration
duration_seconds = frame_count / fps if fps > 0 else 0
```

**Example:**
- Frame count: 7200
- FPS: 30
- Duration: 7200 / 30 = 240 seconds = 4 minutes

### Step 3: Format Duration
```python
def _format_duration(self, seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"
```

**Examples:**
- 45 seconds → "45s"
- 240 seconds → "4m 0s"
- 3661 seconds → "1h 1m 1s"

### Step 4: Categorize Content
```python
def _categorize_video_content(self, duration_seconds, width, height):
    aspect_ratio = width / height if height > 0 else 1.0
    
    # Portrait (mobile video)
    if aspect_ratio < 0.8:
        return "videos_portrait"
    
    # Very long (movies)
    elif duration_seconds > 3600:  # > 1 hour
        return "videos_long"
    
    # Short clips
    elif duration_seconds < 60:  # < 1 minute
        return "videos_short"
    
    # Medium length
    else:
        return "videos_medium"
```

**Categories:**
- `videos_portrait` - Vertical videos (TikTok, Instagram Reels)
- `videos_landscape` - Horizontal videos (YouTube)
- `videos_short` - < 1 minute
- `videos_medium` - 1-60 minutes
- `videos_long` - > 1 hour

## Fallback Analysis (No OpenCV)

If OpenCV not installed:
```python
def _fallback_analysis(self, file_path):
    file_size = os.path.getsize(file_path)
    
    # Estimate category from file size
    # Rough heuristic: larger = longer/higher quality
    if file_size > 500 * 1024 * 1024:  # > 500MB
        content_category = "videos_long"
    elif file_size > 100 * 1024 * 1024:  # > 100MB
        content_category = "videos_medium"
    else:
        content_category = "videos_short"
    
    return {
        "type": "video",
        "file_size": file_size,
        "content_category": content_category,
        "processed": False,
        "error": "OpenCV not available"
    }
```

## Classification Hints

Provides data for classifier:
```python
{
  "duration_seconds": 240,
  "width": 1920,
  "height": 1080,
  "fps": 30,
  "aspect_ratio": 1.78  # 16:9
}
```

**Classifier uses this to decide:**
- `aspect_ratio < 0.8` → `videos_portrait`
- `duration > 600s, resolution > 720p` → `videos_youtube_like`
- `fps = 60, resolution = 1920x1080` → `videos_screen_recording`
- `aspect_ratio = 1.78, duration < 300s` → `videos_camera_clip`

## Performance

| File Size | Time |
|-----------|------|
| 10MB | 50ms |
| 100MB | 100ms |
| 1GB | 150ms |

**Fast!** Only reads metadata, doesn't process frames.

## Example Usage

```python
# In app.py
@app.post("/analyze/video")
async def analyze_video_endpoint(file_id: str):
    metadata = store.get_metadata(file_id)
    file_path = metadata["file_path"]
    
    # Analyze video
    analysis = video_processor.analyze(file_path)
    
    # Classify
    category = classifier.classify_file(
        file_path, 
        "video", 
        {"video": analysis}
    )
    
    # Save
    store.save_metadata(file_id, {...})
```

## Limitations
1. **Requires OpenCV** (optional dependency)
2. **No frame analysis** (no scene detection, object detection)
3. **No thumbnail generation**
4. **No audio analysis**
5. **No codec detection**
6. **Fallback is basic** (just file size)

## Quiz Tips
- **Library:** OpenCV (cv2)
- **Key properties:** width, height, fps, frame_count
- **Duration formula:** frame_count / fps
- **Categories:** portrait, landscape, short, medium, long
- **Aspect ratio threshold:** < 0.8 for portrait
- **Duration thresholds:** < 60s (short), > 3600s (long)
- **Performance:** Fast (50-150ms), only reads metadata
