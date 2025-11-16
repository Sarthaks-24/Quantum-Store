# QUIZ CHEAT SHEET - Quantum Store

**Study this for 15 minutes before your quiz!** ⏰

---

## 🎯 What Is Quantum Store?

**Smart file storage system** with automatic categorization into 40+ types

**Tech Stack:**
- Frontend: React 18.2 + Vite 5
- Backend: FastAPI (Python)
- Storage: JSON files
- Processing: OpenCV, PyMuPDF, PaddleOCR, scikit-learn

---

## 📊 Key Numbers (MEMORIZE!)

| Metric | Value |
|--------|-------|
| Total categories | 40+ |
| Image categories | 15 |
| PDF categories | 9 |
| JSON categories | 5 |
| API endpoints | 17 |
| Upload limit | 1GB |
| Search debounce | 300ms |
| OCR trigger | < 30 chars |
| JSON streaming threshold | 5MB |
| JSON sample size | 50 records |
| OCR page limit | 5 pages |
| Preview width | 400px |
| K-means clusters | 5 colors |
| Top keywords | 20 |

---

## 🔄 Upload Flow (7 Steps)

```
1. Frontend sends file → POST /upload
2. Backend saves → data/raw/uploads/{id}.ext
3. Detect type → detect_file_type_comprehensive()
   (magic bytes → extension → MIME)
4. Process file → ImageProcessor/PDFProcessor/etc.
5. Classify → classifier.classify_file() → category
6. Save metadata → data/processed/metadata/{id}.json
7. Update indices → phash_index.json, tfidf_index.json
```

---

## 🗂️ File Structure

```
Quantum-Store/
├── frontend/                      React app
│   ├── js/
│   │   ├── Dashboard.js          Stats + recent files
│   │   ├── Files.js              Search + filter + sort
│   │   ├── Upload.js             Drag & drop
│   │   ├── PreviewModal.js       Zoom + pan + analytics
│   │   └── api.js                API communication
│
├── backend/                       Python server
│   ├── app.py                    FastAPI (17 endpoints)
│   ├── classifier.py             40+ categories (974 lines)
│   ├── processors/
│   │   ├── image_processor.py   Color + quality + phash
│   │   ├── pdf_processor.py     Text + OCR
│   │   ├── json_processor.py    Schema + streaming
│   │   ├── text_processor.py    TF-IDF + readability
│   │   └── video_processor.py   Metadata
│   ├── storage/store.py          JSON save/load
│   └── utils/
│       ├── file_utils.py        Type detection
│       ├── serializers.py       JSON conversion
│       └── metrics.py           Similarity math
│
└── data/                          Storage
    ├── raw/uploads/              Original files
    ├── processed/metadata/       Analysis (JSON)
    └── cache/                    Indices (phash, tfidf)
```

---

## 🔍 File Type Detection (3 Methods)

**Priority order:**

1. **Magic bytes** (file header)
   - `%PDF` → PDF
   - `\xff\xd8\xff` → JPEG
   - `\x89PNG` → PNG
   - `{` or `[` → JSON

2. **File extension**
   - `.json`, `.pdf`, `.png`, `.txt`, `.mp4`

3. **MIME type**
   - `application/pdf`, `image/png`, `text/plain`

**Function:** `detect_file_type_comprehensive(filename, mime_type, file_bytes)`

**Returns:** `"json"`, `"pdf"`, `"image"`, `"text"`, `"video"`, `"unknown"`

---

## 🎨 Image Processor

**Library:** PIL (Pillow), imagehash, OpenCV, scikit-learn

**What it extracts:**
- Dimensions, format, EXIF
- 5 dominant colors (K-means clustering)
- Quality: brightness (0-255), sharpness (Laplacian), edge density (Canny)
- Perceptual hash (phash) for similarity
- RGB histograms (16-bin)

**Performance:**
- Small (<1MP): 100-200ms
- Medium (1-5MP): 200-500ms
- Large (>10MP): 500ms-2s

**Key algorithms:**
- **K-means:** Clusters pixels into 5 colors
- **Laplacian:** Measures sharpness (high = sharp)
- **Canny edge detection:** Counts edges
- **Perceptual hash:** 16-char hex for similarity

---

## 📄 PDF Processor

**Library:** PyMuPDF (fitz), PaddleOCR

**What it extracts:**
- Page count, metadata (author, title, dates)
- Text from all pages
- **Auto OCR** if text < 30 chars
- Preview image (page 1, 400px width)
- Image count, form detection

**OCR:**
- **Trigger:** text_length < 30 characters
- **Library:** PaddleOCR
- **Page limit:** First 5 pages only
- **Time:** 2-5 seconds per page

**Performance:**
- Text PDF (5 pages): 200ms
- Scanned PDF (1 page with OCR): 3s

---

## 📊 JSON Processor

**Library:** ijson (streaming), json (regular)

**Smart features:**
- **Streaming** for files > 5MB
- **Sampling:** Only saves first 50 records
- **Schema auto-detection**
- **Type inference:** int, float, string, date, array, object

**How streaming works:**
```python
if file_size > 5MB:
    # Use ijson (doesn't load entire file)
    items = ijson.items(file, 'item')
    for i, item in enumerate(items):
        if i < 50:
            samples.append(item)
        if i >= 1000:
            break
else:
    # Load entire file
    data = json.load(file)
```

**Memory savings:** 100× less for large files

---

## 📝 Text Processor

**Library:** scikit-learn (TF-IDF), regex

**What it extracts:**
- Word count, line count, char count
- Top 20 keywords (stopword filtered)
- Readability score (Flesch Reading Ease)
- TF-IDF vectors (similarity)

**Readability levels:**
- 90-100: Very easy (5th grade)
- 60-70: Standard (8-9th grade)
- 0-30: Very difficult (professional)

**Formula:**
```
score = 206.835 - 1.015 × avg_sentence_length - 84.6 × complex_word_ratio
```

---

## 🎬 Video Processor

**Library:** OpenCV (cv2)

**What it extracts:**
- Width, height, FPS, frame count
- Duration (frame_count / fps)
- File size

**Performance:** 50-150ms (just metadata, no frame processing)

---

## 🧠 Classifier (MOST IMPORTANT!)

**40+ categories across 5 types**

### Image Categories (15)
- `images_screenshot` - High edge density (>0.3) + common resolution
- `images_scanned_document` - High brightness (>200) + grayscale
- `images_photo` - Regular photos
- `images_meme` - Text overlay
- `images_selfie` - Portrait + face
- `images_ai_generated` - Smooth, unrealistic colors
- `images_logo`, `images_poster`, `images_graphic_art`
- `images_portrait` / `images_landscape` / `images_photos` / `images_graphics`

### PDF Categories (9)
- `pdfs_text_document` - Normal text
- `pdfs_scanned` - is_scanned=True
- `pdfs_form` - has_forms=True
- `pdfs_with_images` - image_ratio > 0.3
- `pdfs_ebook` - page_count > 100
- `pdfs_presentation` - image_ratio > 0.5
- `pdfs_receipt` - page_count ≤ 2

### JSON Categories (5)
- `json_flat_structured` - nesting_depth ≤ 1
- `json_nested` - nesting_depth ≥ 3
- `json_array_of_objects` - record_count > 0
- `json_semistructured` - Mixed
- `json_invalid` - Malformed

### Text Categories (6)
- `text_code`, `text_markdown`, `text_csv`, `text_xml`, `text_log`, `text_document`

### Video Categories (5)
- `videos_portrait` - aspect_ratio < 0.8
- `videos_screen_recording` - fps ≥ 50
- `videos_youtube_like` - duration > 300s
- `videos_camera_clip` - duration < 60s
- `videos_landscape` - Default horizontal

---

## 🔑 Key Heuristics (MEMORIZE!)

| Category | Key Rules |
|----------|-----------|
| Screenshot | edge_density > 0.3 + common resolution (1920×1080) |
| Scanned doc | brightness > 200 + grayscale colors |
| Meme | Text overlay detected |
| Ebook | page_count > 100 + text_length > 50000 |
| Form PDF | has_forms = True |
| Scanned PDF | is_scanned = True (auto OCR triggered) |
| Portrait video | aspect_ratio < 0.8 |
| Nested JSON | nesting_depth ≥ 3 |
| Flat JSON | nesting_depth ≤ 1 + record_count = 0 |

---

## 🗄️ Storage (store.py)

**Format:** JSON files

**Structure:**
```
data/
├── raw/uploads/
│   └── {file_id}.ext                Original file
├── processed/
│   ├── metadata/
│   │   └── {file_id}.json          Full analysis
│   ├── schemas/
│   │   └── {schema_id}.json        JSON schemas
│   └── groups/
│       └── {category}.json         Category indices
└── cache/
    ├── phash_index.json            Image similarity
    └── tfidf_index.json            Text similarity
```

**Metadata format:**
```json
{
  "id": "abc-123",
  "filename": "report.pdf",
  "file_type": "pdf",
  "file_size": 524288,
  "upload_date": "2024-01-15T10:30:00Z",
  "content_category": "pdfs_text_document",
  "analysis": {
    "pdf": {/* PDF analysis */}
  }
}
```

**Key methods:**
- `save_metadata(file_id, metadata)`
- `get_metadata(file_id)`
- `get_all_files()`
- `add_file_to_group(category, file_id)`

---

## 🌐 API Endpoints (17 total)

### Upload
- `POST /upload` - Single file
- `POST /upload/batch` - Multiple files

### Analysis
- `POST /analyze/json` - Analyze JSON
- `POST /analyze/text` - Analyze text
- `POST /analyze/image` - Analyze image
- `POST /analyze/pdf` - Analyze PDF
- `POST /analyze/video` - Analyze video

### Retrieval
- `GET /file/{id}` - Get metadata
- `GET /files` - List all files
- `GET /file/{id}/preview` - Get preview
- `GET /file/{id}/download` - Download file

### Grouping
- `GET /groups` - Get all groups
- `GET /groups/{category}` - Get category files
- `POST /groups/rebuild` - Rebuild groups
- `POST /groups/auto` - Auto-group files

### Other
- `GET /health` - Health check
- `GET /schemas` - Get all schemas

---

## 🎨 Frontend Components

### Dashboard.js
- Shows total files, storage, type distribution, recent 5
- Loads data: `Promise.all([fetchSummary(), fetchRecentFiles(), fetchFiles()])`
- **Time:** 300-500ms

### Files.js
- **Search** with 300ms debounce
- **Filter** by type, date, size
- **Sort** by name/date/size (asc/desc)
- **Debouncing saves 90% of API calls**

### Upload.js
- Drag & drop zone
- Batch upload (sequential, not parallel)
- Per-file progress tracking

### PreviewModal.js
- Zoom/pan (mouse wheel: 0.9× zoom out, 1.1× zoom in)
- Range: 0.5× to 5×
- Touch support (pinch-to-zoom)
- Dual tabs: Preview + Analytics
- Navigate: Previous/Next

### api.js
- `fetchWithTimeout()` - 30s/60s timeouts
- `uploadFile()` - With progress callback
- `fetchFiles()` - Get all files
- `fetchFilePreview()` - Get preview

---

## 🧮 Math & Algorithms

### Cosine Similarity
```python
similarity = dot_product(v1, v2) / (magnitude(v1) × magnitude(v2))
```
Range: 0.0 (different) to 1.0 (identical)

### Hamming Distance
```python
distance = sum(c1 != c2 for c1, c2 in zip(str1, str2))
```
Counts differing characters (for phash comparison)

### K-means Clustering
Groups pixels into 5 dominant colors

### TF-IDF
**TF** (Term Frequency): How often word appears in document
**IDF** (Inverse Document Frequency): How rare word is across all documents
**Result:** Important unique words

### Flesch Reading Ease
```
score = 206.835 - 1.015 × avg_sentence_length - 84.6 × complex_word_ratio
```

---

## ⚡ Performance

| Operation | Time |
|-----------|------|
| Upload (small) | 100-500ms |
| Upload (large) | 1-5s |
| Image analysis | 100ms-2s |
| PDF analysis | 200ms-10s (with OCR) |
| JSON analysis | 50ms-5s |
| Text analysis | 10-500ms |
| Video analysis | 50-150ms |
| Classification | 1-10ms |
| Dashboard load | 300-500ms |
| Search debounce | 300ms |

---

## 🚨 Limitations

### Image Processor
- No face detection, no text detection
- Basic categorization only

### PDF Processor
- OCR only first 5 pages
- OCR requires PaddleOCR (500MB)
- No table extraction

### JSON Processor
- Only first 50 samples saved
- Only first 1000 records analyzed
- Requires ijson for streaming

### Text Processor
- English only (stopwords)
- No sentiment analysis
- No entity extraction

### Classifier
- Heuristics not perfect (85-90% accuracy)
- No machine learning
- Hard-coded thresholds

---

## 🎓 Most Likely Quiz Questions

1. **What are the 3 file type detection methods?**
   → Magic bytes, extension, MIME type

2. **What triggers OCR in PDF processing?**
   → text_length < 30 characters

3. **How many categories does the classifier have?**
   → 40+ (15 image, 9 PDF, 5 JSON, 6 text, 5 video, 5 audio)

4. **What is the JSON streaming threshold?**
   → 5MB

5. **What algorithm finds dominant colors in images?**
   → K-means clustering (5 clusters)

6. **What is the search debounce time in Files.js?**
   → 300ms

7. **What heuristic identifies screenshots?**
   → edge_density > 0.3 + common resolution

8. **What library is used for OCR?**
   → PaddleOCR

9. **How many samples does JSON processor save?**
   → 50 records max

10. **What is the upload flow?**
    → Upload → Save → Detect → Process → Classify → Save metadata → Index

---

## 💡 Quick Mnemonics

**File detection:** **M**agic → **E**xtension → **M**IME (MEM)

**Upload flow:** **U**pload → **S**ave → **D**etect → **P**rocess → **C**lassify → **S**ave → **I**ndex (US-DPCSI)

**Image metrics:** **C**olor → **Q**uality → **P**hash → **H**istogram (CQPH)

**PDF steps:** **O**pen → **T**ext → **O**CR → **P**review (OTOP)

**Readability:** **F**lesch **R**eading **E**ase = **FRE**

---

**GOOD LUCK! 🚀**

Print this and review 15 minutes before your quiz!
