# Classifier - Quick Reference (THE MOST IMPORTANT FILE!)

## What It Does
**Categorizes files into 40+ specific types** using heuristic rules

## Main Function
```python
classifier = AdvancedClassifier()
result = classifier.classify_file(file_path, file_type, analysis)
```

**Returns:**
```json
{
  "content_category": "images_screenshot",
  "confidence": 0.85,
  "reasoning": ["High edge density (0.42)", "Rectangular regions detected"]
}
```

## The Big Picture
```
Processor → Returns analysis (colors, text, schema, etc.)
    ↓
Classifier → Uses analysis + heuristics → Returns category
    ↓
Storage → Saves category in metadata
```

## 40+ Categories (By Type)

### **Images (15 categories)**
```python
"images_screenshot"        # Desktop/mobile screenshots
"images_scanned_document"  # Scanned paper
"images_photo"             # Regular photos
"images_meme"              # Memes (text on image)
"images_selfie"            # Selfies (portrait with face)
"images_ai_generated"      # AI art (DALL-E, Midjourney)
"images_poster"            # Posters, flyers
"images_graphic_art"       # Illustrations, designs
"images_logo"              # Logos
"images_photo_document"    # Photo of document
"images_portrait"          # Portrait orientation
"images_landscape"         # Landscape orientation
"images_graphics"          # Generic graphics
"images_photos"            # Generic photos
"images_other"             # Unknown
```

### **PDFs (9 categories)**
```python
"pdfs_text_document"       # Normal text PDFs
"pdfs_scanned"             # Scanned paper (OCR used)
"pdfs_form"                # Forms with fields
"pdfs_with_images"         # PDFs with photos
"pdfs_with_tables"         # Spreadsheet-like
"pdfs_ebook"               # Books (many pages)
"pdfs_presentation"        # Slides
"pdfs_slides"              # Presentation slides
"pdfs_receipt"             # Receipts
```

### **JSON (5 categories)**
```python
"json_flat_structured"     # Simple {"key": "value"}
"json_nested"              # Deep objects (3+ levels)
"json_array_of_objects"    # Database-like [{}, {}]
"json_semistructured"      # Mixed types
"json_invalid"             # Malformed
```

### **Text (6 categories)**
```python
"text_code"                # Python, JavaScript, etc.
"text_markdown"            # .md files
"text_csv"                 # CSV data
"text_xml"                 # XML data
"text_log"                 # Log files
"text_document"            # Generic text
```

### **Video (5 categories)**
```python
"videos_youtube_like"      # Horizontal, medium-long
"videos_screen_recording"  # High FPS, desktop resolution
"videos_portrait"          # Vertical (TikTok)
"videos_landscape"         # Horizontal
"videos_camera_clip"       # Short camera videos
```

### **Audio (5 categories)**
```python
"audio_music"              # Music files
"audio_voice_note"         # Voice recordings
"audio_whatsapp_voice"     # WhatsApp voice messages
"audio_podcast"            # Podcast episodes
"audio_recording"          # Generic recordings
```

## How It Works (Decision Tree)

### **Image Classification**

```python
def _classify_image(self, analysis, file_path):
    image_analysis = analysis.get("image", {})
    
    # Get metrics from processor
    quality = image_analysis.get("quality", {})
    edge_density = quality.get("edge_density", 0)
    brightness = quality.get("brightness", 0)
    
    category_info = image_analysis.get("category", {})
    basic_category = category_info.get("category", "unknown")
    
    # HEURISTIC RULES
    
    # 1. Screenshot detection
    if self._is_screenshot(image_analysis):
        return {
            "content_category": "images_screenshot",
            "confidence": 0.85,
            "reasoning": ["High edge density", "Rectangular regions"]
        }
    
    # 2. Scanned document detection
    elif self._is_scanned_document(image_analysis):
        return {
            "content_category": "images_scanned_document",
            "confidence": 0.80,
            "reasoning": ["High brightness", "Text-like patterns"]
        }
    
    # 3. Meme detection
    elif self._is_meme(image_analysis):
        return {
            "content_category": "images_meme",
            "confidence": 0.75,
            "reasoning": ["Text overlay detected"]
        }
    
    # ... (continues for all 15 categories)
```

### **Screenshot Detection (Example Heuristic)**

```python
def _is_screenshot(self, analysis):
    quality = analysis.get("quality", {})
    edge_density = quality.get("edge_density", 0)
    dimensions = analysis.get("dimensions", {})
    width = dimensions.get("width", 0)
    height = dimensions.get("height", 0)
    
    # RULES:
    # 1. High edge density (lots of UI elements)
    # 2. Common screen resolutions
    # 3. Sharp image (not blurry)
    
    common_resolutions = [
        (1920, 1080), (1366, 768), (1440, 900),
        (1280, 720), (1080, 1920)  # Mobile portrait
    ]
    
    is_common_resolution = (width, height) in common_resolutions
    is_sharp = quality.get("sharpness", 0) > 800
    has_ui_elements = edge_density > 0.3
    
    return (is_common_resolution and has_ui_elements) or \
           (is_sharp and edge_density > 0.4)
```

**Logic:**
- High edge density (0.3+) → Lots of rectangles/lines (UI elements)
- Common resolution (1920x1080, etc.) → Screen size
- Sharp → Not camera photo (usually blurry)

### **Scanned Document Detection**

```python
def _is_scanned_document(self, analysis):
    quality = analysis.get("quality", {})
    brightness = quality.get("brightness", 0)
    
    dominant_colors = analysis.get("dominant_colors", [])
    
    # RULES:
    # 1. High brightness (white paper)
    # 2. Low color variety (mostly white/black/gray)
    # 3. Text-like edge patterns
    
    is_bright = brightness > 200
    
    # Check if mostly grayscale
    is_grayscale = True
    for color in dominant_colors[:3]:  # Top 3 colors
        rgb = color.get("rgb", [0, 0, 0])
        r, g, b = rgb
        # If R ≈ G ≈ B, it's grayscale
        if abs(r - g) > 30 or abs(g - b) > 30:
            is_grayscale = False
            break
    
    return is_bright and is_grayscale
```

### **PDF Classification**

```python
def _classify_pdf(self, analysis, file_path):
    pdf_analysis = analysis.get("pdf", {})
    
    page_count = pdf_analysis.get("page_count", 0)
    is_scanned = pdf_analysis.get("is_scanned", False)
    has_forms = pdf_analysis.get("has_forms", False)
    image_count = pdf_analysis.get("image_count", 0)
    image_ratio = pdf_analysis.get("image_ratio", 0)
    text_length = pdf_analysis.get("text_length", 0)
    
    # PRIORITY ORDER (first match wins)
    
    # 1. Scanned PDFs
    if is_scanned:
        return "pdfs_scanned", 0.90
    
    # 2. Forms
    elif has_forms:
        return "pdfs_form", 0.85
    
    # 3. PDFs with many images
    elif image_ratio > 0.3:
        return "pdfs_with_images", 0.80
    
    # 4. Ebooks (many pages, mostly text)
    elif page_count > 100 and text_length > 50000:
        return "pdfs_ebook", 0.85
    
    # 5. Presentations (few pages, many images)
    elif page_count < 50 and image_ratio > 0.5:
        return "pdfs_presentation", 0.80
    
    # 6. Receipts (small file, 1-2 pages)
    elif page_count <= 2 and text_length < 2000:
        return "pdfs_receipt", 0.75
    
    # 7. Default: text document
    else:
        return "pdfs_text_document", 0.70
```

### **JSON Classification**

```python
def _classify_json(self, analysis, file_path):
    json_analysis = analysis.get("json", {})
    
    schema = json_analysis.get("schema", {})
    record_count = json_analysis.get("record_count", 0)
    
    # Calculate nesting depth
    nesting_depth = self._calculate_max_nesting(schema)
    
    # RULES:
    
    # 1. Flat structured (depth = 1)
    if nesting_depth <= 1 and record_count == 0:
        return "json_flat_structured", 0.85
    
    # 2. Nested (depth >= 3)
    elif nesting_depth >= 3:
        return "json_nested", 0.90
    
    # 3. Array of objects (database-like)
    elif record_count > 0:
        return "json_array_of_objects", 0.85
    
    # 4. Semistructured (mixed)
    else:
        return "json_semistructured", 0.60
```

### **Video Classification**

```python
def _classify_video(self, analysis, file_path):
    video_analysis = analysis.get("video", {})
    
    duration = video_analysis.get("duration_seconds", 0)
    width = video_analysis.get("width", 0)
    height = video_analysis.get("height", 0)
    fps = video_analysis.get("fps", 0)
    
    aspect_ratio = width / height if height > 0 else 1.0
    
    # RULES:
    
    # 1. Portrait (vertical)
    if aspect_ratio < 0.8:
        return "videos_portrait", 0.90
    
    # 2. Screen recording (60fps, desktop resolution)
    elif fps >= 50 and width >= 1280:
        return "videos_screen_recording", 0.85
    
    # 3. YouTube-like (horizontal, medium-long)
    elif aspect_ratio > 1.5 and duration > 300:
        return "videos_youtube_like", 0.80
    
    # 4. Short camera clip
    elif duration < 60:
        return "videos_camera_clip", 0.75
    
    # 5. Default: landscape
    else:
        return "videos_landscape", 0.70
```

## Confidence Scores

**Scale:** 0.0 (no confidence) to 1.0 (100% sure)

**Typical ranges:**
- **0.90-1.0:** Very confident (exact match, e.g., is_scanned=True)
- **0.80-0.89:** Confident (strong heuristics match)
- **0.70-0.79:** Moderate (some heuristics match)
- **0.50-0.69:** Low (fallback/guess)
- **< 0.50:** Very uncertain (use "other")

## File Type Detection (Before Classification)

```python
def _detect_type(self, file_path):
    """Detects broad file type (image, pdf, json, text, video)"""
    from backend.utils.file_utils import detect_file_type_comprehensive
    
    # Read first 512 bytes for magic byte detection
    with open(file_path, 'rb') as f:
        file_bytes = f.read(512)
    
    file_type = detect_file_type_comprehensive(
        filename=file_path,
        mime_type=None,
        file_bytes=file_bytes
    )
    
    return file_type  # "image", "pdf", "json", "text", "video"
```

## Extension Type Mapping

Fallback if detection fails:
```python
EXTENSION_TYPE_MAP = {
    "jpg": "image", "jpeg": "image", "png": "image", "gif": "image",
    "pdf": "pdf",
    "json": "json",
    "txt": "text", "md": "text", "csv": "text",
    "mp4": "video", "avi": "video", "mov": "video",
    "mp3": "audio", "wav": "audio", "ogg": "audio",
    # ... 50+ extensions total
}
```

## Complete Flow

```
1. User uploads file
    ↓
2. detect_file_type_comprehensive()
   → Returns: "image", "pdf", "json", "text", "video"
    ↓
3. Run appropriate processor
   → ImageProcessor / PDFProcessor / JSONProcessor / etc.
   → Returns analysis (colors, text, schema, etc.)
    ↓
4. classify_file(file_path, file_type, analysis)
   → Runs heuristic rules
   → Returns specific category (e.g., "images_screenshot")
    ↓
5. Save to metadata
   → content_category: "images_screenshot"
   → confidence: 0.85
```

## Example: Classifying a Screenshot

```python
# 1. Upload "screenshot.png"

# 2. File type detection
file_type = "image"  # From magic bytes \x89PNG

# 3. Image processor runs
analysis = {
  "dimensions": {"width": 1920, "height": 1080},
  "quality": {
    "edge_density": 0.42,  # High!
    "brightness": 150,
    "sharpness": 1200
  },
  "category": {"category": "screenshot", "confidence": 0.85}
}

# 4. Classifier runs
if edge_density > 0.3 and (1920, 1080) in common_resolutions:
    category = "images_screenshot"
    confidence = 0.85

# 5. Save
metadata = {
  "content_category": "images_screenshot",
  "confidence": 0.85
}
```

## Performance
- **Time:** 1-10ms (just logic, no processing)
- **Depends on:** Analysis from processor (already done)

## Limitations
1. **Heuristics not perfect** (85-90% accuracy)
2. **No machine learning** (rule-based only)
3. **Hard-coded thresholds** (edge_density > 0.3, etc.)
4. **Can't detect all types** (e.g., can't tell real vs AI selfie perfectly)
5. **Confidence is estimate** (not statistically validated)

## Quiz Tips (MEMORIZE THESE!)

### Key Numbers
- **Total categories:** 40+
- **Image categories:** 15
- **PDF categories:** 9
- **JSON categories:** 5
- **Screenshot edge density threshold:** > 0.3
- **Scanned document brightness threshold:** > 200
- **Ebook page count threshold:** > 100
- **Portrait aspect ratio threshold:** < 0.8
- **Confidence ranges:** 0.5 (guess) to 1.0 (certain)

### Key Heuristics
- **Screenshot:** High edge density + common resolution
- **Scanned doc:** High brightness + grayscale
- **Meme:** Text overlay on image
- **Ebook:** Many pages (>100) + lots of text
- **Form PDF:** has_forms = True
- **Portrait video:** aspect_ratio < 0.8
- **Nested JSON:** nesting_depth >= 3

### Most Important Categories
- **Images:** screenshot, photo, scanned_document, meme
- **PDFs:** text_document, scanned, form, ebook
- **JSON:** flat, nested, array_of_objects
- **Text:** code, markdown, csv, document
- **Video:** portrait, landscape, youtube_like

**This is the brain of the system!** 🧠
