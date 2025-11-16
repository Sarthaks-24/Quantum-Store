# image_processor.py - Image Analysis & Classification

**Location**: `backend/processors/image_processor.py`  
**Lines**: 300+  
**Type**: Processor Module

---

## Overview

The **ImageProcessor** analyzes image files to extract comprehensive metadata including dimensions, color profiles, quality metrics, perceptual hashes, and content categorization. It uses computer vision techniques (OpenCV, PIL, scikit-learn) to provide detailed insights about images.

**Key Features**:
- EXIF metadata extraction
- Dominant color detection (K-means clustering)
- Quality metrics (brightness, sharpness, edge density)
- Perceptual hashing (phash) for similarity detection
- Color histograms (16-bin RGB)
- Heuristic-based categorization (logo, screenshot, photo, graphic)
- Content category classification for Layer 2 grouping

---

## Responsibilities

1. **Basic Information**
   - Image dimensions (width × height)
   - Format (PNG, JPEG, GIF, etc.)
   - Color mode (RGB, RGBA, L, etc.)
   - Aspect ratio calculation
   - Alpha channel detection
   - EXIF metadata presence

2. **Color Analysis**
   - Extract 5 dominant colors using K-means clustering
   - Calculate color variance
   - Detect grayscale images
   - Generate RGB hex codes

3. **Quality Metrics**
   - Brightness (mean pixel intensity)
   - Sharpness (Laplacian variance)
   - Edge density (Canny edge detection)

4. **Similarity Indexing**
   - Calculate perceptual hash (phash) for duplicate detection
   - 64-bit hash comparing structural similarity

5. **Categorization**
   - Heuristic-based classification (logo, screenshot, photo, graphic)
   - Content category for Layer 2 grouping (portrait, landscape, screenshot, graphics)
   - Confidence scoring (0.0-1.0)

---

## Class Structure

### `ImageProcessor()`
```python
class ImageProcessor:
    def __init__(self):
        self.reasoning_log = []
```

**Instance Variables**:
- `reasoning_log`: List of timestamped reasoning steps

---

## Core Methods

### `analyze(file_path: str) -> Dict[str, Any]`
```python
def analyze(self, file_path: str) -> Dict[str, Any]:
    self.reasoning_log = []
    self.log_reasoning("Starting image analysis")
    
    try:
        img = Image.open(file_path)
        img_array = np.array(img)
    except Exception as e:
        return {"error": f"Failed to load image: {str(e)}"}
    
    basic_info = self._get_basic_info(img, file_path)
    colors = self._analyze_colors(img_array)
    quality_metrics = self._analyze_quality(img_array)
    phash = self._calculate_phash(img)
    histogram = self._calculate_histogram(img_array)
    category = self._categorize_image(img, img_array, basic_info, colors, quality_metrics)
    content_category = self._determine_content_category(img, basic_info, category)
    
    return {
        **basic_info,
        "colors": colors,
        "quality": quality_metrics,
        "phash": phash,
        "histogram": histogram,
        "category": category,
        "content_category": content_category,
        "reasoning_log": self.reasoning_log
    }
```

**Flow**:
1. Reset reasoning log
2. Load image (PIL + NumPy array)
3. Extract basic info (dimensions, format, EXIF)
4. Analyze colors (K-means clustering)
5. Calculate quality metrics (brightness, sharpness, edges)
6. Generate perceptual hash
7. Calculate RGB histograms
8. Categorize using heuristics
9. Determine content category
10. Return complete analysis

**Output Example**:
```json
{
  "format": "PNG",
  "mode": "RGBA",
  "width": 1920,
  "height": 1080,
  "aspect_ratio": 1.777,
  "has_alpha": true,
  "has_exif": false,
  "file_size": 524288,
  "colors": {
    "dominant_colors": [
      {"rgb": [255, 87, 51], "hex": "#ff5733", "percentage": 0.35},
      {"rgb": [51, 255, 87], "hex": "#33ff57", "percentage": 0.25}
    ],
    "color_variance": 2456.78,
    "is_grayscale": false
  },
  "quality": {
    "brightness": 128.5,
    "sharpness": 1250.3,
    "edge_density": 0.12
  },
  "phash": "8f7e6d5c4b3a2918",
  "histogram": {
    "red": [12, 45, 78, ...],
    "green": [23, 56, 89, ...],
    "blue": [34, 67, 90, ...]
  },
  "category": {
    "category": "screenshot",
    "confidence": 0.85,
    "reasons": ["High sharpness and edge density", "No EXIF metadata"]
  },
  "content_category": "images_screenshot",
  "reasoning_log": [
    "[2024-11-15T10:30:00.123456] Starting image analysis",
    "[2024-11-15T10:30:00.234567] Image: 1920x1080, format=PNG, ...",
    ...
  ]
}
```

---

## Analysis Methods

### `_get_basic_info(img: Image.Image, file_path: str) -> Dict[str, Any]`
```python
def _get_basic_info(self, img: Image.Image, file_path: str) -> Dict[str, Any]:
    width, height = img.size
    aspect_ratio = width / height if height > 0 else 0
    
    info = {
        "format": img.format,
        "mode": img.mode,
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "has_alpha": img.mode in ('RGBA', 'LA', 'PA'),
        "file_size": os.path.getsize(file_path)
    }
    
    try:
        exif = img._getexif()
        info["has_exif"] = exif is not None and len(exif) > 0
    except:
        info["has_exif"] = False
    
    self.log_reasoning(
        f"Image: {width}x{height}, format={img.format}, mode={img.mode}, "
        f"alpha={info['has_alpha']}, exif={info['has_exif']}"
    )
    
    return info
```

**Fields**:
- `format`: Image format (PNG, JPEG, GIF, etc.)
- `mode`: Color mode (RGB, RGBA, L for grayscale, etc.)
- `width`, `height`: Dimensions in pixels
- `aspect_ratio`: width ÷ height
- `has_alpha`: True if transparency channel exists
- `file_size`: File size in bytes
- `has_exif`: True if EXIF metadata present

---

### `_analyze_colors(img_array: np.ndarray) -> Dict[str, Any]`
```python
def _analyze_colors(self, img_array: np.ndarray) -> Dict[str, Any]:
    # Handle grayscale
    if len(img_array.shape) == 2:
        self.log_reasoning("Grayscale image detected")
        return {
            "dominant_colors": [],
            "color_variance": float(np.var(img_array)),
            "is_grayscale": True
        }
    
    # Strip alpha channel if present
    if img_array.shape[2] == 4:
        img_rgb = img_array[:, :, :3]
    else:
        img_rgb = img_array
    
    # Reshape to pixel list
    pixels = img_rgb.reshape(-1, 3)
    
    # K-means clustering (5 clusters)
    n_colors = min(5, len(pixels))
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    kmeans.fit(pixels)
    
    colors = kmeans.cluster_centers_
    labels = kmeans.labels_
    counts = np.bincount(labels)
    percentages = counts / len(labels)
    
    # Format dominant colors
    dominant_colors = []
    for i in range(n_colors):
        color = colors[i]
        dominant_colors.append({
            "rgb": [int(c) for c in color],
            "hex": "#{:02x}{:02x}{:02x}".format(int(color[0]), int(color[1]), int(color[2])),
            "percentage": float(percentages[i])
        })
    
    dominant_colors.sort(key=lambda x: x["percentage"], reverse=True)
    
    color_variance = float(np.var(pixels))
    
    self.log_reasoning(
        f"Extracted {n_colors} dominant colors, color_variance={color_variance:.2f}"
    )
    
    return {
        "dominant_colors": dominant_colors,
        "color_variance": color_variance,
        "is_grayscale": False
    }
```

**Algorithm**: K-means clustering with k=5  
**Output**: Top 5 colors sorted by percentage  
**Color Variance**: Total pixel variance (high = many colors, low = uniform)

---

### `_analyze_quality(img_array: np.ndarray) -> Dict[str, Any]`
```python
def _analyze_quality(self, img_array: np.ndarray) -> Dict[str, Any]:
    # Convert to grayscale for analysis
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Brightness: mean pixel intensity (0-255)
    brightness = float(np.mean(gray))
    
    # Sharpness: Laplacian variance
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    sharpness = float(np.var(laplacian))
    
    # Edge density: Canny edge detection
    edges = cv2.Canny(gray, 100, 200)
    edge_density = float(np.sum(edges > 0) / edges.size)
    
    self.log_reasoning(
        f"Quality metrics: brightness={brightness:.1f}, sharpness={sharpness:.1f}, "
        f"edge_density={edge_density:.3f}"
    )
    
    return {
        "brightness": brightness,
        "sharpness": sharpness,
        "edge_density": edge_density
    }
```

**Metrics**:
- **Brightness**: 0 (dark) to 255 (bright)
- **Sharpness**: Higher = sharper edges (screenshots ~1000+, photos ~100-500)
- **Edge Density**: Ratio of edge pixels (0.0-1.0)

---

### `_calculate_phash(img: Image.Image) -> str`
```python
def _calculate_phash(self, img: Image.Image) -> str:
    phash = str(imagehash.phash(img))
    self.log_reasoning(f"Perceptual hash: {phash}")
    return phash
```

**Algorithm**: Perceptual hashing (imagehash library)  
**Output**: 16-character hexadecimal string  
**Use Case**: Detect duplicate/similar images

---

### `_calculate_histogram(img_array: np.ndarray) -> Dict[str, List[int]]`
```python
def _calculate_histogram(self, img_array: np.ndarray) -> Dict[str, List[int]]:
    if len(img_array.shape) == 2:
        # Grayscale histogram
        hist, _ = np.histogram(img_array, bins=16, range=(0, 256))
        return {"gray": hist.tolist()}
    
    if img_array.shape[2] >= 3:
        # RGB histograms
        hist_r, _ = np.histogram(img_array[:, :, 0], bins=16, range=(0, 256))
        hist_g, _ = np.histogram(img_array[:, :, 1], bins=16, range=(0, 256))
        hist_b, _ = np.histogram(img_array[:, :, 2], bins=16, range=(0, 256))
        
        return {
            "red": hist_r.tolist(),
            "green": hist_g.tolist(),
            "blue": hist_b.tolist()
        }
    
    return {}
```

**Bins**: 16 bins (0-15, 16-31, ..., 240-255)  
**Output**: 16-element arrays per channel

---

## Categorization Methods

### `_categorize_image() -> Dict[str, Any]`
```python
def _categorize_image(
    self,
    img: Image.Image,
    img_array: np.ndarray,
    basic_info: Dict,
    colors: Dict,
    quality: Dict
) -> Dict[str, Any]:
    self.log_reasoning("Applying heuristic-based categorization")
    
    category = "unknown"
    confidence = 0.0
    reasons = []
    
    is_logo = False
    is_screenshot = False
    is_photo = False
    
    # Logo detection
    if basic_info["has_alpha"] and basic_info["format"] == "PNG":
        is_logo = True
        reasons.append("Has transparency (alpha channel)")
    
    if colors.get("color_variance", 0) < 1000:
        is_logo = True
        reasons.append("Low color variance suggests simple graphic")
    
    # Screenshot detection
    if quality["sharpness"] > 1000 and quality["edge_density"] > 0.1:
        is_screenshot = True
        reasons.append("High sharpness and edge density")
    
    # Photo detection
    if basic_info.get("has_exif"):
        is_photo = True
        reasons.append("Contains EXIF metadata (likely from camera)")
    
    if colors.get("color_variance", 0) > 3000:
        is_photo = True
        reasons.append("High color variance suggests natural photo")
    
    # Final category decision
    if is_logo and not is_photo:
        category = "logo"
        confidence = 0.7
    elif is_screenshot and not is_photo:
        category = "screenshot"
        confidence = 0.85
    elif is_photo:
        category = "photo"
        confidence = 0.75
    else:
        category = "graphic"
        confidence = 0.5
    
    self.log_reasoning(f"Categorized as '{category}' with confidence {confidence:.2f}")
    
    return {
        "category": category,
        "confidence": confidence,
        "reasons": reasons
    }
```

**Categories**:
- **logo**: PNG with alpha, low color variance
- **screenshot**: High sharpness, high edge density, no EXIF
- **photo**: Has EXIF or high color variance
- **graphic**: Fallback for other images

---

### `_determine_content_category() -> str`
```python
def _determine_content_category(
    self,
    img: Image.Image,
    basic_info: Dict[str, Any],
    category_info: Dict[str, Any]
) -> str:
    width = basic_info.get("width", 0)
    height = basic_info.get("height", 0)
    aspect_ratio = basic_info.get("aspect_ratio", 1.0)
    basic_category = category_info.get("category", "unknown")
    
    # Screenshot detection
    if basic_category == "screenshot":
        return "images_screenshot"
    
    # Graphics/logos
    if basic_category in ["logo", "graphic"]:
        return "images_graphics"
    
    # Photo categorization (portrait vs landscape)
    if basic_category == "photo":
        if aspect_ratio < 0.8:  # Taller than wide
            return "images_portrait"
        else:
            return "images_landscape"
    
    # Fallback
    if aspect_ratio < 0.8:
        return "images_portrait"
    elif basic_info.get("has_exif", False):
        return "images_photos"
    else:
        return "images_graphics"
```

**Content Categories**:
- `images_screenshot`: Detected screenshots
- `images_graphics`: Graphics, logos, illustrations
- `images_portrait`: Vertical photos
- `images_landscape`: Horizontal photos
- `images_photos`: General photos with EXIF

---

## Similarity Methods

### `calculate_similarity(phash1: str, phash2: str) -> float`
```python
def calculate_similarity(self, phash1: str, phash2: str) -> float:
    hash1 = imagehash.hex_to_hash(phash1)
    hash2 = imagehash.hex_to_hash(phash2)
    
    distance = hash1 - hash2  # Hamming distance
    
    similarity = 1 - (distance / 64.0)  # Normalize to 0.0-1.0
    
    return max(0.0, similarity)
```

**Algorithm**: Hamming distance between 64-bit hashes  
**Output**: 0.0 (completely different) to 1.0 (identical)  
**Threshold**: >0.9 = likely duplicate, >0.95 = very similar

---

## Dependencies

### External Libraries
- **PIL** (Pillow) - Image loading, EXIF extraction
- **imagehash** - Perceptual hashing
- **numpy** - Array operations
- **sklearn.cluster.KMeans** - Color clustering
- **cv2** (OpenCV) - Quality metrics (Laplacian, Canny)

### Python Standard Library
- **os** - File size calculation
- **datetime** - Reasoning log timestamps

---

## Performance Characteristics

### Analysis Time
- **Small images** (<1MP): 100-200ms
- **Medium images** (1-5MP): 200-500ms
- **Large images** (>10MP): 500ms-2s

**Bottlenecks**:
- K-means clustering (~50-100ms)
- Canny edge detection (~20-50ms)
- Perceptual hash (~10-20ms)

### Memory Usage
- **Base**: ~10MB (libraries loaded)
- **Per image**: 3× image size in RAM (PIL, NumPy, OpenCV arrays)
- **Example**: 5MP RGB image = 15MB × 3 = 45MB peak

---

## Known Limitations

1. **Basic Categorization**
   - Heuristic-based (not ML)
   - Limited categories (logo, screenshot, photo, graphic)
   - **Enhancement**: Train image classifier (CNN)

2. **No Face Detection**
   - Cannot detect portraits/selfies
   - **Enhancement**: Use OpenCV Haar cascades or dlib

3. **No Text Detection**
   - Cannot identify memes or text-heavy images
   - **Enhancement**: Use pytesseract OCR

4. **Grayscale Color Analysis**
   - No dominant colors for grayscale
   - **Enhancement**: Treat grayscale as shades of gray

5. **Large Image Memory**
   - Entire image loaded into RAM
   - **Enhancement**: Downsample for analysis

---

## How to Modify or Extend

### Add Face Detection
```python
import cv2

def _detect_faces(self, img_array: np.ndarray) -> int:
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    return len(faces)

# In analyze():
face_count = self._detect_faces(img_array)
if face_count > 0:
    category = "photo_people"
```

---

### Add Text Detection
```python
import pytesseract

def _detect_text(self, img_array: np.ndarray) -> bool:
    try:
        text = pytesseract.image_to_string(img_array)
        return len(text.strip()) > 50
    except:
        return False

# In categorize:
if self._detect_text(img_array):
    category = "image_with_text"
```

---

**Last Updated**: November 2024  
**Status**: ✅ Production-ready  
**Categories**: 4 (logo, screenshot, photo, graphic)  
**Content Categories**: 5 (screenshot, graphics, portrait, landscape, photos)
