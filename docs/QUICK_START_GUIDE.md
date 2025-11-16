# Quantum Store - Quick Start Guide (1 Hour Study)

**Goal:** Understand this codebase in under 1 hour for a quiz

---

## 🎯 What Is This Application?

**Quantum Store** is a **smart file storage and analysis system** that:
1. **Uploads** files (images, PDFs, JSON, text, videos)
2. **Analyzes** them using AI processors
3. **Categorizes** them automatically (40+ categories)
4. **Stores** metadata in JSON files
5. **Displays** them in a React dashboard

**Architecture:** React Frontend → FastAPI Backend → Python Processors → JSON Storage

---

## 📁 File Structure (What's Where)

```
Quantum-Store/
├── frontend/          → React UI (what users see)
│   ├── index.html     → Entry point
│   ├── js/
│   │   ├── Dashboard.js   → Home page with stats
│   │   ├── Files.js       → File browser with search
│   │   ├── Upload.js      → Drag & drop uploader
│   │   ├── PreviewModal.js → File preview popup
│   │   └── api.js         → API communication
│   └── css/styles.css → Styling
│
├── backend/           → Python server (brains)
│   ├── app.py         → FastAPI server (17 endpoints)
│   ├── classifier.py  → Smart categorization (40+ types)
│   ├── processors/    → File analyzers
│   │   ├── image_processor.py  → Color, quality, phash
│   │   ├── pdf_processor.py    → Text + OCR
│   │   ├── json_processor.py   → Schema detection
│   │   ├── text_processor.py   → TF-IDF, readability
│   │   └── video_processor.py  → Duration, resolution
│   ├── storage/
│   │   └── store.py   → Save/load JSON files
│   └── utils/
│       ├── file_utils.py    → File type detection
│       ├── serializers.py   → JSON conversion
│       └── metrics.py       → Math (similarity, distance)
│
└── data/              → Where files are stored
    ├── raw/uploads/          → Original files
    └── processed/metadata/   → Analysis results (JSON)
```

---

## 🔄 How Data Flows (Upload Process)

```
User uploads file
    ↓
Frontend: Upload.js sends to API
    ↓
Backend: app.py receives file
    ↓
1. Save file → data/raw/uploads/
    ↓
2. Detect type → file_utils.detect_file_type_comprehensive()
    ↓
3. Run processor → ImageProcessor/PDFProcessor/JSONProcessor/etc.
    ↓
4. Classify → classifier.py (determines category like "images_screenshot")
    ↓
5. Save metadata → store.save_metadata() → data/processed/metadata/{id}.json
    ↓
6. Update indices → phash_index.json, tfidf_index.json
    ↓
Frontend: Display success
```

---

## 💻 Key Backend Components

### 1. **app.py** - The Server (718 lines)
**What it does:** Handles HTTP requests

**Key Endpoints:**
- `POST /upload` - Upload single file
- `POST /upload/batch` - Upload multiple files
- `GET /files` - List all files
- `GET /file/{id}` - Get file metadata
- `GET /file/{id}/preview` - Get preview image
- `POST /analyze/json` - Analyze JSON file
- `GET /groups` - Get categorized groups

**Important Function:**
```python
save_analysis_with_classification(file_id, file_type, analysis, filename, file_size)
```
- Combines processor output + classifier category
- Saves to JSON file
- Updates indices

---

### 2. **classifier.py** - The Brain (974 lines)
**What it does:** Categorizes files into 40+ types

**Main Method:**
```python
classifier.classify_file(file_path, file_type, analysis)
```

**Categories by Type:**

**Images (15 categories):**
- `images_screenshot` - Screenshots (high edge density, rectangular regions)
- `images_scanned_document` - Scanned paper (high brightness, text-like)
- `images_photo` - Regular photos
- `images_meme` - Memes (text on image)
- `images_selfie` - Selfies (portrait with face)
- `images_ai_generated` - AI art (smooth, unrealistic colors)
- `images_graphic_art` - Posters, designs
- etc.

**PDFs (9 categories):**
- `pdfs_text_document` - Normal text PDFs
- `pdfs_scanned` - Scanned PDFs (OCR used)
- `pdfs_form` - Forms (structured fields)
- `pdfs_with_images` - PDFs with photos
- `pdfs_ebook` - Books (many pages, small file)
- etc.

**JSON (5 categories):**
- `json_flat_structured` - Simple key-value
- `json_nested` - Deep objects
- `json_array_of_objects` - Database-like
- etc.

**How It Works:**
1. Receives analysis from processor
2. Checks heuristics (rules):
   - Is brightness > 200? → Might be screenshot
   - Is edge density > 0.3? → Has lots of lines
   - Does it have faces? → Portrait/selfie
3. Returns category + confidence (0-1)

---

### 3. **Processors** - File Analyzers

#### **image_processor.py** (300+ lines)
**What it does:** Analyzes images deeply

**Main Method:**
```python
analyzer.analyze(file_path) → dict
```

**Returns:**
```json
{
  "dimensions": {"width": 1920, "height": 1080},
  "format": "PNG",
  "dominant_colors": [
    {"rgb": [255, 0, 0], "hex": "#ff0000", "percentage": 35.2}
  ],
  "quality": {
    "brightness": 128.5,
    "sharpness": 1250.3,
    "edge_density": 0.42
  },
  "phash": "a1b2c3d4e5f6g7h8",  // For similarity
  "category": {
    "category": "screenshot",
    "confidence": 0.85
  }
}
```

**Key Algorithms:**
- **K-means clustering** → Find 5 dominant colors
- **Laplacian variance** → Measure sharpness
- **Canny edge detection** → Count edges
- **Perceptual hashing** → Compare similar images

---

#### **pdf_processor.py** (347 lines)
**What it does:** Extracts text from PDFs (with OCR for scanned ones)

**Main Method:**
```python
processor.analyze(file_path) → dict
```

**Process:**
1. Open PDF with PyMuPDF (fitz)
2. Try to extract text from each page
3. If text < 30 chars → **Trigger OCR** (PaddleOCR)
4. Generate preview image from page 1
5. Count images, detect forms

**Returns:**
```json
{
  "page_count": 5,
  "text": "Full extracted text...",
  "is_scanned": true,
  "has_ocr": true,
  "preview": "base64_image_string",
  "image_count": 3
}
```

---

#### **json_processor.py** (800 lines)
**What it does:** Analyzes JSON structure (handles huge files with streaming)

**Main Methods:**
```python
processor.analyze(file_path) → dict
```

**Smart Features:**
- **Large file (>5MB)?** → Uses streaming (ijson library)
- **Small file?** → Loads entire JSON
- **Arrays?** → Samples first 50 records (not all!)
- **Schema detection** → Auto-infers field types

**Returns:**
```json
{
  "record_count": 10000,
  "sampled_count": 50,
  "schema": {
    "user_id": {"type": "int", "nullable": false},
    "name": {"type": "string", "nullable": false},
    "email": {"type": "string", "nullable": true}
  },
  "samples": [/* first 50 records */],
  "statistics": {
    "user_id": {"min": 1, "max": 10000, "avg": 5000}
  }
}
```

---

#### **text_processor.py** (250 lines)
**What it does:** Analyzes text files (readability, keywords)

**Returns:**
```json
{
  "char_count": 5000,
  "word_count": 800,
  "line_count": 120,
  "tokens": {
    "unique": 450,
    "top_20": [
      {"token": "python", "count": 50, "frequency": 0.0625}
    ]
  },
  "readability": {
    "score": 65.3,
    "level": "standard"
  }
}
```

**Readability Levels:**
- 90-100: Very easy
- 60-70: Standard
- 0-30: Very difficult (technical docs)

---

#### **video_processor.py** (162 lines)
**What it does:** Extracts video metadata

**Uses OpenCV to get:**
- Duration (seconds)
- Resolution (width x height)
- FPS (frames per second)
- Frame count

---

### 4. **store.py** - Storage Layer (392 lines)
**What it does:** Saves/loads files as JSON

**Directory Structure:**
```
data/
├── raw/uploads/           → Original files
│   └── {file_id}.pdf
├── processed/
│   ├── metadata/          → Analysis results
│   │   └── {file_id}.json
│   ├── schemas/           → JSON schemas
│   └── groups/            → Category indices
└── cache/
    ├── phash_index.json   → Image similarity index
    └── tfidf_index.json   → Text similarity index
```

**Main Methods:**
```python
store.save_metadata(file_id, metadata)  # Save analysis
store.get_metadata(file_id)             # Load analysis
store.get_all_files()                   # List all files
store.add_file_to_group(category, file_id)  # Categorize
```

**Metadata Format:**
```json
{
  "id": "abc-123",
  "filename": "report.pdf",
  "file_type": "pdf",
  "file_size": 524288,
  "upload_date": "2024-01-15T10:30:00",
  "analysis": {
    "pdf": {/* PDF analysis */}
  },
  "content_category": "pdfs_text_document"
}
```

---

### 5. **Utilities**

#### **file_utils.py**
**Key Function:**
```python
detect_file_type_comprehensive(filename, mime_type, file_bytes)
```

**Detection Methods (in order):**
1. **Magic bytes** (file header):
   - `%PDF` → PDF
   - `\xff\xd8\xff` → JPEG
   - `\x89PNG` → PNG
2. **File extension**: `.json`, `.pdf`, `.txt`
3. **MIME type**: `application/pdf`, `image/png`

**Returns:** `"json"`, `"pdf"`, `"image"`, `"text"`, `"video"`, `"unknown"`

---

#### **serializers.py**
**Purpose:** Convert Python objects to JSON safely

**Problem:** NumPy arrays, Decimals can't be serialized directly

**Solution:**
```python
sanitize_for_json(data)
```
- Decimal → float
- numpy.int64 → int
- numpy.ndarray → list
- datetime → ISO string

---

#### **metrics.py**
**Purpose:** Mathematical similarity calculations

**Key Functions:**
```python
cosine_similarity(vec1, vec2) → 0.0 to 1.0
jaccard_similarity(set1, set2) → 0.0 to 1.0
hamming_distance(str1, str2) → integer
```

**Used for:**
- Comparing image phashes (Hamming distance)
- Comparing text TF-IDF vectors (Cosine similarity)

---

## 🎨 Frontend Components

### 1. **Dashboard.js** - Home Page
**What it shows:**
- Total files count
- Total storage used
- File type distribution chart
- Recent 5 files

**How it loads data:**
```javascript
useEffect(() => {
  Promise.all([
    fetchSummary(),      // Get stats
    fetchRecentFiles(),  // Get recent 5
    fetchFiles()         // Get all files
  ]).then(/* update state */)
}, [])
```

---

### 2. **Files.js** - File Browser
**Features:**
- **Search** with 300ms debounce
- **Filter** by type (image/pdf/json/text/video)
- **Filter** by date range
- **Filter** by size
- **Sort** by name/date/size (asc/desc)

**Search Debouncing:**
```javascript
const debouncedSearch = useCallback(
  debounce((term) => setSearchTerm(term), 300),
  []
)
```
Why? Typing "react" = 5 searches → With debounce = 1 search (300ms after last keystroke)

---

### 3. **Upload.js** - File Uploader
**Features:**
- Drag & drop zone
- File selection button
- Batch upload (sequential, not parallel)
- Progress tracking per file

**Why sequential?**
- Backend processes files one-by-one
- Easier to track progress
- Avoids server overload

---

### 4. **PreviewModal.js** - File Preview
**Features:**
- Image zoom/pan (mouse wheel, drag)
- Touch support (pinch-to-zoom)
- Text preview (expandable)
- Analytics tab
- Navigate between files (Previous/Next)

**Zoom Logic:**
```javascript
const handleWheel = (e) => {
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  setZoom(prevZoom => Math.min(Math.max(prevZoom * delta, 0.5), 5))
}
```
- Scroll down → 0.9× (zoom out)
- Scroll up → 1.1× (zoom in)
- Min: 0.5×, Max: 5×

---

### 5. **api.js** - Backend Communication
**Key Functions:**
```javascript
uploadFile(file, onProgress)           // Upload with progress
fetchFiles()                           // Get all files
fetchFilePreview(fileId)               // Get preview
fetchFileAnalytics(fileId)             // Get analysis
```

**Timeout Handling:**
```javascript
const fetchWithTimeout = (url, options = {}, timeout = 30000) => {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Timeout')), timeout)
    )
  ])
}
```

---

## 🧠 Key Concepts to Remember

### 1. **File Type Detection (3 Methods)**
1. Magic bytes (most reliable)
2. File extension
3. MIME type

### 2. **Processing Pipeline**
```
Upload → Detect Type → Process → Classify → Save → Index
```

### 3. **Categories (40+)**
- **Images:** screenshot, photo, meme, selfie, AI-generated, graphic_art
- **PDFs:** text_doc, scanned, form, ebook, presentation
- **JSON:** flat, nested, array_of_objects, semistructured
- **Text:** code, markdown, csv, document
- **Video:** youtube_like, screen_recording, portrait, landscape

### 4. **Storage Format**
Everything stored as **JSON files**:
- Metadata: `data/processed/metadata/{id}.json`
- Indices: `data/cache/phash_index.json`, `tfidf_index.json`
- Groups: `data/processed/groups/{category}.json`

### 5. **Image Analysis**
- **Dominant colors:** K-means clustering (5 colors)
- **Quality:** Brightness (0-255), Sharpness (Laplacian), Edges (Canny)
- **Similarity:** Perceptual hash (phash) + Hamming distance

### 6. **PDF Processing**
- Extract text with PyMuPDF
- If text < 30 chars → **Auto OCR** with PaddleOCR
- Generate preview from page 1

### 7. **JSON Processing**
- Small (<5MB): Load entire file
- Large (>5MB): Stream with ijson
- Sample first 50 records (not all 10,000!)
- Auto-detect schema (field types)

### 8. **Search Debouncing**
- Wait 300ms after last keystroke
- Reduces API calls by 90%

---

## 🚀 Quick API Reference

### Upload
```
POST /upload
Body: multipart/form-data with "file" field
Returns: {id, filename, file_type, analysis}
```

### Get Files
```
GET /files
Returns: [{id, filename, file_type, file_size, upload_date, content_category}, ...]
```

### Get Preview
```
GET /file/{id}/preview
Returns: {preview: "base64_image_or_text_excerpt"}
```

### Get Analytics
```
GET /file/{id}
Returns: {metadata with full analysis}
```

### Get Groups
```
GET /groups
Returns: {
  "images_screenshot": ["id1", "id2"],
  "pdfs_text_document": ["id3"],
  ...
}
```

---

## 🎓 Quiz Topics to Focus On

1. **Architecture:** React → FastAPI → Processors → JSON Storage
2. **Upload Flow:** 7 steps (save → detect → process → classify → save metadata → index → respond)
3. **Processors:** What each does (image/pdf/json/text/video)
4. **Classifier:** 40+ categories, how it decides (heuristics)
5. **Storage:** JSON files in `data/processed/metadata/`
6. **Frontend:** Dashboard, Files, Upload, PreviewModal
7. **Key Algorithms:** K-means, phash, TF-IDF, OCR
8. **File Detection:** Magic bytes → Extension → MIME
9. **Debouncing:** 300ms delay for search
10. **API Endpoints:** Upload, files, preview, analytics, groups

---

## 📊 Performance Numbers

- **Upload:** 100ms-5s (depends on file size)
- **Image Analysis:** 100ms-2s (small vs large)
- **PDF Analysis:** 200ms-10s (with OCR)
- **JSON Analysis:** 50ms-5s (streaming for large)
- **Dashboard Load:** 300-500ms
- **Search Debounce:** 300ms

---

## 🔍 Common Patterns

### Backend Pattern
```python
# 1. Receive file
# 2. Save to disk
file_path = save_upload_file(file, file_id)

# 3. Detect type
file_type = detect_file_type_comprehensive(filename, mime, bytes)

# 4. Process
if file_type == "image":
    analysis = image_processor.analyze(file_path)
elif file_type == "pdf":
    analysis = pdf_processor.analyze(file_path)

# 5. Classify
category = classifier.classify_file(file_path, file_type, analysis)

# 6. Save metadata
store.save_metadata(file_id, {...})

# 7. Update indices
store.update_phash_index() or store.update_tfidf_index()
```

### Frontend Pattern
```javascript
// 1. User action
// 2. API call
const response = await api.uploadFile(file)

// 3. Update state
setFiles([...files, response])

// 4. Re-render
```

---

## ✅ Study Checklist (30 min each)

**Part 1: Backend (30 min)**
- [ ] Understand upload flow (app.py)
- [ ] Know 5 processors (what each does)
- [ ] Understand classifier categories
- [ ] Know storage structure (JSON files)

**Part 2: Frontend (30 min)**
- [ ] Understand Dashboard (stats display)
- [ ] Understand Files (search, filter, sort)
- [ ] Understand Upload (drag & drop, batch)
- [ ] Understand PreviewModal (zoom, pan, tabs)

---

## 🎯 Most Important Files (Read These First)

1. **docs/ARCHITECTURE.md** - System overview
2. **backend/app.py** - Main server (17 endpoints)
3. **backend/classifier.py** - Categorization logic
4. **backend/processors/image_processor.py** - Image analysis
5. **frontend/js/Dashboard.js** - UI entry point

---

**Good luck with your quiz! 🚀**
