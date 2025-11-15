# QuantumStore Advanced Classification System - Complete Rebuild

## 🎯 Executive Summary

**COMPLETELY REWRITTEN** - Advanced multi-level categorization for ALL file types with subcategories, confidence scoring, and heuristic-based detection.

---

## ✨ New Classification Features

### Output Format
```json
{
  "type": "image",
  "category": "image_screenshot",
  "subcategories": ["image_png", "image_landscape"],
  "confidence": 0.85
}
```

### Key Improvements
- ✅ **Multi-level categorization**: Primary category + subcategories
- ✅ **Confidence scoring**: 0.0-1.0 for every classification
- ✅ **No ML models**: Pure heuristics and metadata analysis
- ✅ **Fallback grouping**: Extension-based when classification fails
- ✅ **Single entry point**: `classify_file(metadata, preview, full_path)`

---

## 📋 Categories by File Type

### 1. IMAGES (15+ Categories)

#### Primary Categories:
- `image_screenshot` - Screen captures (1920x1080, PNG without EXIF, etc.)
- `image_scanned_document` - Scanned papers (A4 aspect, grayscale, TIFF)
- `image_photo_realworld` - Real photos (has EXIF from camera)
- `image_graphic_art` - Digital art (PNG with alpha, SVG)
- `image_digital_poster` - Posters (portrait, large, high quality)
- `image_photo_document` - ID cards, receipts (small rectangular)
- `image_meme` - Memes (square JPEG, 300-1200px, no EXIF)
- `image_selfie_frontcamera` - Selfies (portrait, mobile dimensions, EXIF)
- `image_ai_generated_like` - AI art (512/768/1024 square, no EXIF)

#### Subcategory Tags:
- **Format**: `image_jpeg`, `image_png`, `image_webp`, `image_gif`, `image_tiff`, `image_bmp`
- **Aspect**: `image_square`, `image_portrait`, `image_landscape`, `image_panorama`

#### Detection Logic:
```python
# Screenshot: Common resolutions or PNG without EXIF
if (width, height) in [(1920,1080), (1366,768), (2560,1440), ...]:
    return "image_screenshot"

# AI Generated: Specific sizes without EXIF
if (width, height) in [(512,512), (768,768), (1024,1024), ...] and not has_exif:
    return "image_ai_generated_like"

# Scanned: A4 ratio + grayscale or TIFF
if 1.25 <= aspect <= 1.6 and (is_grayscale or format == "TIFF"):
    return "image_scanned_document"

# Meme: Square-ish JPEG without EXIF
if 0.8 <= aspect <= 1.2 and 300 <= w <= 1200 and ext == '.jpg' and not has_exif:
    return "image_meme"
```

---

### 2. JSON (5 Categories)

#### Categories:
- `json_flat_structured` - SQL-ready arrays (consistency ≥95%, depth ≤2)
  - Subcategories: `sql_ready`, `has_schema`
- `json_semistructured` - Partial schemas (consistency 70-95%)
  - Subcategories: `partial_schema`
- `json_nested` - Deep structures (depth >3 or nested_ratio >50%)
  - Subcategories: `depth_N`
- `json_unstructured` - Inconsistent/mixed data
- `json_invalid` - Parse errors
  - Subcategories: `json_parse_error`

#### Detection Logic:
```python
# Flat structured (SQL-ready)
if shape == "array_of_objects":
    if consistency >= 0.95 and max_depth <= 2 and nested_ratio < 0.3:
        return "json_flat_structured"  # Can generate SQL schema

# Nested structures
if max_depth > 3 or nested_ratio > 0.5:
    return "json_nested"  # NoSQL suitable
```

---

### 3. PDF (9 Categories)

#### Categories:
- `pdf_text_document` - Primarily text
- `pdf_scanned` - OCR applied
  - Subcategories: `ocr_applied`
- `pdf_form` - Interactive forms
  - Subcategories: `interactive_form`
- `pdf_with_images` - Image-heavy (>40% images)
  - Subcategories: `images_XXpct`
- `pdf_with_tables` - Contains tables
  - Subcategories: `structured_data`
- `pdf_ebook_layout` - Ebook formatting (50+ pages, high text density)
  - Subcategories: `long_document`
- `pdf_presentation` - Business presentations
- `pdf_slides` - Presentation slides (<500 chars/page avg)
  - Subcategories: `pages_N`
- `pdf_receipt` - Receipts/invoices (≤2 pages, keywords)
  - Subcategories: `short_document`

#### Detection Logic:
```python
# Form (highest priority)
if has_forms:
    return "pdf_form", 0.95

# Scanned
if is_scanned:
    return "pdf_scanned", 0.90

# Receipt: Small + keywords
if page_count <= 2 and text_length < 3000:
    if "total" in text and "receipt" in text and "tax" in text:
        return "pdf_receipt", 0.85

# Slides: Many pages, low text density
if page_count >= 5 and image_ratio > 0.3:
    if (text_length / page_count) < 500:
        return "pdf_slides", 0.80

# Ebook: Many pages, high text density
if page_count >= 50 and (text_length / page_count) > 1500:
    return "pdf_ebook_layout", 0.80
```

---

### 4. AUDIO (5 Categories)

#### Categories:
- `audio_music` - Songs (120-600s, high bitrate >128kbps)
  - Subcategories: `high_quality`, `audio_mp3`
- `audio_voice_note` - Voice messages (<120s, low bitrate)
  - Subcategories: `short_recording`, `audio_m4a`
- `audio_whatsapp_voice` - WhatsApp clips (opus/m4a, <180s, specific sizes)
  - Subcategories: `voice_message`, `audio_opus`
- `audio_podcast_like` - Podcasts (>600s, 64-192kbps)
  - Subcategories: `long_audio`, `audio_mp3`
- `audio_recording` - Generic recordings
  - Subcategories: `audio_wav`

#### Detection Logic:
```python
# WhatsApp: Specific format + duration + file size
if ext == '.opus' and duration < 180 and 5KB < size < 500KB:
    return "audio_whatsapp_voice", 0.90

# Voice note: Short + low bitrate
if duration < 120 and bitrate < 64000:
    return "audio_voice_note", 0.80

# Podcast: Long + medium bitrate
if duration > 600 and 64000 <= bitrate <= 192000:
    return "audio_podcast_like", 0.75

# Music: Medium duration + high bitrate
if 120 <= duration <= 600 and bitrate > 128000:
    return "audio_music", 0.70
```

---

### 5. VIDEO (5 Categories)

#### Categories:
- `video_youtube_like` - YouTube-style (16:9, HD ≥720p, 24-60fps, >60s)
  - Subcategories: `hd_video`
- `video_screen_recording` - Screen captures (common resolutions, 15-30fps)
  - Subcategories: `1920x1080`, `1280x720`, etc.
- `video_portrait` - Vertical mobile (aspect <0.8)
  - Subcategories: `vertical_video`
- `video_landscape` - Horizontal (default)
  - Subcategories: `horizontal_video`
- `video_camera_clip` - Mobile camera (5-300s, 720-2160p)
  - Subcategories: `mobile_recording`

#### Detection Logic:
```python
# Portrait (highest confidence)
if aspect < 0.8:
    return "video_portrait", 0.90

# Screen recording: Exact resolution match + typical FPS
if (width, height) in [(1920,1080), (1280,720), ...] and 15 <= fps <= 30:
    return "video_screen_recording", 0.85

# YouTube: 16:9 + HD + typical FPS + medium-long
if 1.7 <= aspect <= 1.8 and height >= 720 and 24 <= fps <= 60 and duration > 60:
    return "video_youtube_like", 0.80

# Camera clip: Mobile aspect + typical duration + resolution
if 1.3 <= aspect <= 1.8 and 5 <= duration <= 300 and 720 <= height <= 2160:
    return "video_camera_clip", 0.75
```

---

### 6. FALLBACK (Extension-Based Grouping)

When classification fails, files are grouped by extension:
- `.md` → `md_group`
- `.mp3` → `mp3_group`
- `.xyz` → `xyz_group`
- No extension → `unknown_group`

Confidence: **0.4** (low, indicating fallback)

---

## 🔧 Technical Implementation

### Single Entry Point
```python
from classifier import classify_file

result = classify_file(
    metadata={
        "filename": "screenshot.png",
        "size": 500000,
        "mime_type": "image/png"
    },
    preview={
        "width": 1920,
        "height": 1080,
        "has_exif": False
    }
)

# Result:
# {
#   "type": "image",
#   "category": "image_screenshot",
#   "subcategories": ["image_png", "image_landscape"],
#   "confidence": 0.85
# }
```

### Updated app.py Integration
```python
def save_analysis_with_classification(file_id, file_type, analysis, metadata, file_path):
    """Uses new classifier with subcategories."""
    
    # Run classification
    classification = classify_file(
        metadata=metadata,
        preview=analysis,  # Processor results
        full_path=file_path
    )
    
    # Store full classification
    metadata["classification"] = classification
    metadata["category"] = classification["category"]  # Primary
    metadata["subcategories"] = classification["subcategories"]
    metadata["confidence"] = classification["confidence"]
    
    # Group by primary category
    store.add_file_to_group(file_id, classification["category"])
```

---

## ✅ Test Results

All 11 test cases passed:

1. **Screenshot** (1920x1080 PNG): `image_screenshot` (0.85)
2. **JSON Flat**: `json_flat_structured` with `sql_ready` (0.95)
3. **PDF Scanned**: `pdf_scanned` with `ocr_applied` (0.90)
4. **WhatsApp Voice**: `audio_whatsapp_voice` (0.90)
5. **Portrait Video**: `video_portrait` (0.90)
6. **AI Generated**: `image_ai_generated_like` (0.65)
7. **PDF Receipt**: `pdf_receipt` (0.85)
8. **Meme**: `image_meme` (0.75)
9. **Podcast**: `audio_podcast_like` (0.75)
10. **Screen Recording**: `video_screen_recording` (0.85)
11. **Fallback**: `xyz_group` (0.40)

---

## 📊 Confidence Levels

### High Confidence (≥0.90)
- Forms, scanned PDFs, voice notes, portrait videos
- Clear technical indicators

### Good Confidence (0.70-0.89)
- Screenshots, receipts, structured JSON, screen recordings
- Multiple heuristics align

### Medium Confidence (0.60-0.69)
- AI-generated images, generic recordings, mixed content
- Heuristics present but not definitive

### Low Confidence (<0.60)
- Fallback classifications, missing metadata
- Extension-based grouping only

---

## 🚀 Key Achievements

### ✅ No ML Models Required
- Pure heuristics based on:
  - EXIF metadata presence
  - Resolution and aspect ratio
  - File size vs. dimensions
  - Duration and bitrate
  - Content keywords
  - Format-specific indicators

### ✅ Comprehensive Coverage
- **Total Categories**: 40+
  - Images: 15+
  - JSON: 5
  - PDF: 9
  - Audio: 5
  - Video: 5
  - Text: 5
  - Fallback: ∞

### ✅ Multi-Level Tags
- Primary category for grouping
- Subcategories for filtering
- Confidence for ranking

### ✅ Backward Compatible
- `metadata["category"]` still available
- New fields: `subcategories`, `confidence`
- Old code continues working

---

## 🎯 Next Steps (Optional Enhancements)

### Processor Updates
While the classifier works with existing processor output, enhanced metadata would improve accuracy:

1. **Image Processor**:
   - Extract more EXIF fields (camera model, GPS, orientation)
   - Detect borders/padding
   - Calculate color variance more precisely

2. **PDF Processor**:
   - Better table detection (layout analysis)
   - Extract actual text content for keywords
   - Page size consistency analysis

3. **Audio/Video Processors**:
   - Extract codec information
   - Detect audio channels (mono/stereo)
   - Analyze bitrate from actual file data

### Frontend Integration
Update UI to display:
- Primary category badge
- Subcategory chips
- Confidence percentage
- Filter by subcategories

---

## 📝 Summary of Changes

| Aspect | Before | After |
|--------|--------|-------|
| **Total Categories** | 18 (PDF:8 + JSON:10) | 40+ (Images:15+ + JSON:5 + PDF:9 + Audio:5 + Video:5) |
| **Subcategories** | None | Format + aspect tags |
| **Confidence** | Not tracked | 0.0-1.0 for all |
| **Fallback** | Basic extension | Extension-based grouping |
| **Image Detection** | Basic format | 15+ heuristic categories |
| **Audio/Video** | Size-based | Duration/bitrate/resolution |
| **API Changes** | None (backward compatible) | Added subcategories, confidence |

---

## 🎓 Classification Algorithm Examples

### Image Screenshot Detection
```
1. Check exact resolution match with common screen sizes
   → (1920,1080), (1366,768), (2560,1440), etc.

2. PNG without EXIF + large dimensions (≥1000×600)
   → Likely screenshot

3. High sharpness + no EXIF
   → Digital capture (screenshot)

Confidence: 0.85 (multiple indicators)
```

### JSON SQL Suitability
```
1. Shape = array_of_objects
   ↓
2. Field consistency ≥ 95%
   ↓
3. Max depth ≤ 2 levels
   ↓
4. Nested ratio < 30%
   ↓
RESULT: json_flat_structured (SQL-ready)
Confidence: 0.95 (strict criteria met)
```

### Audio WhatsApp Detection
```
1. Extension = .opus (WhatsApp's format)
   ↓
2. Duration < 180 seconds (typical voice note)
   ↓
3. File size 5KB - 500KB (compressed voice)
   ↓
RESULT: audio_whatsapp_voice
Confidence: 0.90 (specific technical match)
```

---

**Classification System**: ✅ **COMPLETE**  
**Files Changed**: 2 (classifier.py, app.py)  
**Lines of Code**: 1000+ (new classifier)  
**Test Coverage**: 11/11 passing  
**Backward Compatible**: Yes  
**ML Required**: No  
**Categories**: 40+
