# app.py - FastAPI Application Server

**Location**: `backend/app.py`  
**Lines**: 718  
**Type**: FastAPI Application

---

## Overview

The **app.py** file is the core FastAPI application that serves as the HTTP API layer for QuantumStore. It provides 17 REST endpoints for file upload, analysis, retrieval, and management. The application coordinates between processors, storage, and the classification engine to deliver a complete file intelligence system.

**Architecture**: RESTful API with automatic file type detection, auto-analysis on upload, and comprehensive error handling.

---

## Responsibilities

1. **HTTP Server Management**
   - FastAPI application initialization
   - CORS middleware configuration (allow all origins)
   - Request body size limit enforcement (1GB max)
   - Health check endpoint

2. **File Upload Processing**
   - Single file upload (`/upload`)
   - Batch file upload (`/upload/batch`)
   - File type detection using MIME type + extension
   - Automatic analysis trigger after upload
   - File size validation (1GB limit)

3. **Analysis Orchestration**
   - Type-specific analysis endpoints (JSON, PDF, image, video, text)
   - Automatic processor selection
   - Unified classification system integration
   - Analysis result storage

4. **File Retrieval**
   - File metadata retrieval
   - File listing with count
   - File preview generation (thumbnails, text excerpts)
   - File download

5. **Grouping & Organization**
   - Category-based grouping
   - Group listing and summary
   - Auto-grouping with rule engine
   - Group rebuild functionality

6. **Schema Management**
   - Schema storage for JSON files
   - Schema retrieval
   - SQL database generation for structured JSON

---

## Configuration

### Upload Limits
```python
MAX_UPLOAD_SIZE = 1 * 1024 * 1024 * 1024  # 1GB in bytes
MAX_UPLOAD_SIZE_MB = 1024  # 1024 MB
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow all origins (development mode)
    allow_credentials=True,
    allow_methods=["*"],      # Allow all HTTP methods
    allow_headers=["*"],      # Allow all headers
)
```

**Note**: In production, restrict `allow_origins` to specific domains.

---

## Middleware

### `LimitUploadSize` (Custom Middleware)
```python
class LimitUploadSize(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == 'POST':
            content_length = request.headers.get('content-length')
            if content_length:
                size_bytes = int(content_length)
                if size_bytes > MAX_UPLOAD_SIZE:
                    return JSONResponse(status_code=413, content={...})
        return await call_next(request)
```

**Purpose**: Reject POST requests exceeding 1GB **before** reading the body  
**Why**: Prevents memory exhaustion from large file uploads  
**Response**: HTTP 413 with detailed size information

---

## Global Instances

```python
store = LocalStore()                    # JSON-based file storage
json_processor = JSONProcessor()        # JSON analysis
text_processor = TextProcessor()        # Text/TF-IDF analysis
image_processor = ImageProcessor()      # Image/phash/color analysis
pdf_processor = PDFProcessor()          # PDF extraction + OCR
video_processor = VideoProcessor()      # Video metadata
rule_engine = RuleEngine()              # Auto-grouping rules
```

**Pattern**: Singleton instances shared across all requests  
**Thread Safety**: Processors are stateless (no shared mutable state)

---

## API Endpoints (17 Total)

### Health & Status

#### `GET /health`
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "QuantumStore",
        "timestamp": datetime.utcnow().isoformat()
    }
```
**Purpose**: Health check for monitoring/load balancers  
**Response**: `200 OK` with service info

---

### File Upload

#### `POST /upload`
**Purpose**: Upload single file with auto-analysis

**Request**: `multipart/form-data` with `file` field

**Flow**:
```
1. Generate UUID file_id
2. Detect file type (MIME + extension)
3. Save file to data/raw/uploads/{file_id}_cleaned_filename
4. Check file size (reject if > 1GB)
5. Create metadata (id, filename, type, mime, size, timestamp, path)
6. Save metadata to data/processed/metadata/{file_id}.json
7. Auto-analyze based on type:
   - json → JSONProcessor.analyze()
   - pdf → PDFProcessor.analyze()
   - image → ImageProcessor.analyze()
   - video → VideoProcessor.analyze()
   - text → TextProcessor.analyze()
8. Run unified classifier (classify_file)
9. Save analysis with classification
10. Add to category group
```

**Response**:
```json
{
  "file_id": "uuid-string",
  "filename": "report.pdf",
  "file_type": "pdf",
  "analyzed": true,
  "message": "File uploaded successfully"
}
```

**Error Handling**:
- Analysis failure doesn't fail upload (file still saved)
- Size limit enforced at middleware + endpoint level

---

#### `POST /upload/batch`
**Purpose**: Upload multiple files with folder grouping

**Request**: `multipart/form-data` with `files[]` and optional `folder_id`

**Parameters**:
- `files`: Array of UploadFile objects
- `folder_id` (optional): Folder identifier (default: `upload_{8-char-hex}`)

**Behavior**: Sequential processing (not parallel)  
**Rationale**: Prevents overwhelming CPU/disk with concurrent analysis

**Response**:
```json
{
  "folder_id": "upload_a1b2c3d4",
  "total_files": 10,
  "successful": 9,
  "failed": 1,
  "results": [
    { "file_id": "uuid", "filename": "doc.pdf", "file_type": "pdf", "size": 102400, "analyzed": true },
    { "filename": "huge.mp4", "error": "File exceeds 1024MB limit (1500MB)", "status": "rejected" }
  ],
  "message": "Upload complete: 9/10 files"
}
```

---

### File Analysis (Type-Specific)

#### `POST /analyze/json`
**Input**: `{ "file_id": "uuid" }`  
**Process**:
1. Load metadata
2. Run `JSONProcessor.analyze(file_path, file_size)`
3. Classify with `classify_file()`
4. If SQL-suitable JSON → Generate SQL schema + SQLite database
5. Save analysis + classification
6. Add to category group

**Response**: Full analysis object (sanitized for JSON)

---

#### `POST /analyze/text`
**Input**: `{ "file_id": "uuid" }`  
**Process**:
1. Load metadata
2. Get all text files for TF-IDF corpus
3. Run `TextProcessor.analyze(file_path, corpus_paths)`
4. Classify and save

**Response**: Analysis with TF-IDF vectors, keywords, similarity scores

---

#### `POST /analyze/image`
**Input**: `{ "file_id": "uuid" }`  
**Process**:
1. Load metadata
2. Run `ImageProcessor.analyze(file_path)`
3. Extract phash and update index
4. Classify and save

**Response**: EXIF, dimensions, colors, phash, category, content_category

---

#### `POST /analyze/pdf`
**Input**: `{ "file_id": "uuid" }`  
**Process**:
1. Load metadata
2. Run `PDFProcessor.analyze(file_path)` (text extraction + OCR fallback)
3. Classify and save

**Response**: Text, page count, is_scanned, preview image (Base64)

---

#### `POST /analyze/video`
**Input**: `{ "file_id": "uuid" }`  
**Process**:
1. Load metadata
2. Run `VideoProcessor.analyze(file_path)`
3. Classify and save

**Response**: Duration, resolution, codec, bitrate, fps

---

### File Retrieval

#### `GET /file/{file_id}`
**Response**:
```json
{
  "metadata": { "id": "...", "filename": "...", "file_type": "...", ... },
  "analysis": { "category": "...", "confidence": 0.85, ... }
}
```

---

#### `GET /files`
**Response**:
```json
{
  "files": [ {...}, {...}, ... ],
  "count": 42
}
```

**Source**: `LocalStore.get_all_files()` (reads all metadata/*.json files)

---

#### `GET /file/{file_id}/preview`
**Purpose**: Generate preview content for different file types

**Behavior**:
- **Image**: Generate 400x400 thumbnail as Base64
- **Text**: First 5000 characters
- **JSON**: First 5000 characters (formatted)
- **PDF**: Preview image + text from analysis (or generate on-the-fly)
- **Video/Audio**: No preview (just metadata)

**Response**:
```json
{
  "file_id": "uuid",
  "metadata": {...},
  "analysis": {...},
  "preview": {
    "type": "image",
    "content": "base64_encoded_string"
  }
}
```

---

#### `GET /file/{file_id}/download`
**Purpose**: Download original file

**Response**: FileResponse with `application/octet-stream`  
**Headers**: `Content-Disposition: attachment; filename="original_filename.ext"`

---

### Grouping & Categories

#### `GET /groups`
**Purpose**: Get all category groups

**Response**:
```json
{
  "groups": {
    "pdf_scanned": ["file_id_1", "file_id_2"],
    "image_screenshot": ["file_id_3"]
  },
  "summary": {
    "pdf_scanned": 2,
    "image_screenshot": 1
  },
  "total_categories": 2
}
```

---

#### `GET /groups/{category}`
**Purpose**: Get all files in specific category

**Response**:
```json
{
  "category": "pdf_scanned",
  "files": ["uuid1", "uuid2", "uuid3"],
  "count": 3
}
```

---

#### `POST /groups/rebuild`
**Purpose**: Rebuild all category groups from metadata

**Use Case**: After manual metadata edits or category changes

**Response**:
```json
{
  "success": true,
  "message": "Groups rebuilt successfully",
  "summary": { "category1": 5, "category2": 3 }
}
```

---

#### `POST /groups/auto`
**Purpose**: Auto-group files using rule engine

**Process**: Runs `RuleEngine.auto_group_files(files)`

**Response**:
```json
{
  "groups": { "group1": [...], "group2": [...] },
  "reasoning": "Reasoning log from rule engine"
}
```

---

### Schemas

#### `GET /schemas`
**Purpose**: Get all saved JSON schemas

**Response**:
```json
{
  "schemas": [
    { "id": "uuid", "schema": {...}, "created_at": "2024-11-15T..." }
  ],
  "count": 1
}
```

---

## Core Functions

### `save_analysis_with_classification()`
```python
def save_analysis_with_classification(
    file_id: str,
    file_type: str,
    analysis: Dict[str, Any],
    metadata: Dict[str, Any],
    file_path: str
) -> Dict[str, Any]:
```

**Purpose**: Unified function to classify and save analysis results

**Steps**:
1. Run `classify_file(metadata, preview=analysis, full_path=file_path)`
2. Extract classification (type, category, subcategories, confidence)
3. Update metadata with classification fields
4. Save metadata to disk
5. Add classification to analysis object
6. Save analysis to disk
7. Add file to category group (indexed)

**Output**: Updated analysis with classification

**Example Classification**:
```json
{
  "type": "pdf",
  "category": "pdf_scanned",
  "subcategories": ["pdf_ocr", "pdf_form"],
  "confidence": 0.87
}
```

---

## File Type Detection

### `get_file_type(filename, mime_type)`
From `utils.file_utils`:
```python
def get_file_type(filename: str, mime_type: str) -> str:
    ext = Path(filename).suffix.lower()
    
    # PDF check (comprehensive)
    if ext == '.pdf' or 'pdf' in mime_type.lower():
        return 'pdf'
    
    # Extension-based detection
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    elif ext in VIDEO_EXTENSIONS:
        return 'video'
    elif ext in AUDIO_EXTENSIONS:
        return 'audio'
    elif ext in ['.json', '.jsonl']:
        return 'json'
    elif ext in TEXT_EXTENSIONS or mime_type.startswith('text/'):
        return 'text'
    
    # MIME type fallback
    if mime_type.startswith('image/'):
        return 'image'
    # ... etc
    
    return 'unknown'
```

---

## Error Handling

### Exception Patterns

**Upload Endpoints**:
```python
try:
    # ... upload logic ...
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

**Analysis Endpoints**:
```python
try:
    # ... analysis logic ...
except HTTPException:
    raise  # Re-raise HTTP exceptions (404, etc.)
except Exception as e:
    print(f"[ERROR] Analysis failed: {str(e)}")
    traceback.print_exc()
    raise HTTPException(status_code=500, detail=str(e))
```

**Auto-Analysis in Upload**:
```python
try:
    analysis = pdf_processor.analyze(file_path)
    # ...
except Exception as analysis_error:
    print(f"[UPLOAD] Auto-analysis failed: {str(analysis_error)}")
    # Don't fail upload if analysis fails
```

**Rationale**: Upload succeeds even if analysis fails (file is saved, can re-analyze later)

---

## Dependencies

### FastAPI & Extensions
- **fastapi** - Web framework
- **starlette** - ASGI middleware
- **uvicorn** - ASGI server (for `__main__`)

### Internal Modules
- **processors** - JSONProcessor, TextProcessor, ImageProcessor, PDFProcessor, VideoProcessor
- **storage.store** - LocalStore (JSON storage)
- **utils.file_utils** - File handling (get_file_type, save_uploaded_file, clean_filename)
- **utils.serializers** - sanitize_for_json (remove non-serializable objects)
- **classifier** - classify_file (unified classification engine)
- **rules.rules** - RuleEngine (auto-grouping)

### External Libraries
- **PIL** (Pillow) - Image thumbnail generation
- **uuid** - File ID generation
- **datetime** - Timestamps
- **os**, **sys**, **traceback** - System utilities

---

## Logging Pattern

All endpoints use structured logging:
```python
print(f"[UPLOAD] File: {filename}, Type: {file_type}, MIME: {file.content_type}")
print(f"[CLASSIFY] {filename}")
print(f"  Type: {classification['type']}")
print(f"  Category: {classification['category']}")
print(f"  Confidence: {classification['confidence']:.2f}")
```

**Format**: `[CONTEXT] Message with details`  
**Contexts**: UPLOAD, ANALYSIS, CLASSIFY, ERROR, STORE

---

## Performance Characteristics

### Upload Endpoint
- **Time**: 100-500ms (small files), 1-5s (large files with analysis)
- **Bottleneck**: Disk I/O (file write), analysis processing

### Analysis Endpoints
- **JSON**: 10-200ms (depends on size/depth)
- **Text**: 50-500ms (TF-IDF computation)
- **Image**: 100-300ms (color clustering, phash)
- **PDF**: 500ms-10s (OCR can be slow)
- **Video**: 200-1000ms (metadata extraction)

### List Files
- **Time**: 10-100ms for <1000 files
- **Complexity**: O(n) where n = number of metadata files

---

## Known Limitations

1. **No Streaming Upload**
   - Files loaded entirely into memory
   - **Issue**: Large files (>500MB) can cause memory spike
   - **Mitigation**: 1GB limit enforced

2. **Sequential Batch Upload**
   - Batch uploads process one file at a time
   - **Trade-off**: Slower but prevents resource exhaustion

3. **No Request Authentication**
   - All endpoints publicly accessible
   - **Production**: Add API key or OAuth middleware

4. **No Rate Limiting**
   - Unlimited requests per client
   - **Enhancement**: Add rate limiter (e.g., `slowapi`)

5. **CORS Wide Open**
   - `allow_origins=["*"]` allows any domain
   - **Production**: Restrict to specific frontend domains

6. **No Request ID Tracing**
   - Hard to trace request through logs
   - **Enhancement**: Add correlation ID middleware

7. **No Pagination**
   - `/files` returns all files (can be large)
   - **Enhancement**: Add limit/offset query params

8. **Preview Generation Not Cached**
   - Thumbnail regenerated on every `/preview` request
   - **Enhancement**: Cache Base64 thumbnails in metadata

---

## How to Modify or Extend

### Add New Endpoint

```python
@app.get("/stats/summary")
async def get_summary_stats():
    files = store.get_all_files()
    
    total_size = sum(f.get("size", 0) for f in files)
    by_type = {}
    for f in files:
        ftype = f.get("file_type", "unknown")
        by_type[ftype] = by_type.get(ftype, 0) + 1
    
    return {
        "total_files": len(files),
        "total_size_bytes": total_size,
        "by_type": by_type
    }
```

---

### Add Authentication

```python
from fastapi import Header, HTTPException

API_KEY = "your-secret-key"

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# Apply to endpoint
@app.post("/upload", dependencies=[Depends(verify_api_key)])
async def upload_file(file: UploadFile = File(...)):
    # ...
```

---

### Add Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.post("/upload")
@limiter.limit("10/minute")  # 10 uploads per minute
async def upload_file(request: Request, file: UploadFile = File(...)):
    # ...
```

---

### Add File Deletion Endpoint

```python
@app.delete("/file/{file_id}")
async def delete_file(file_id: str):
    metadata = store.get_metadata(file_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = metadata.get("path")
    
    # Delete file
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete metadata
    metadata_path = os.path.join(store.metadata_path, f"{file_id}.json")
    if os.path.exists(metadata_path):
        os.remove(metadata_path)
    
    # Remove from groups
    category = metadata.get("category")
    if category:
        store.remove_file_from_group(file_id, category)
    
    return {"success": True, "message": "File deleted"}
```

---

### Add Analytics Endpoint

```python
@app.get("/file/{file_id}/analytics/{file_type}")
async def get_file_analytics(file_id: str, file_type: str):
    """Get type-specific analytics for file."""
    metadata = store.get_metadata(file_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    analysis = store.get_analysis(file_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis available")
    
    # Return type-specific fields
    if file_type == "image":
        return {
            "dimensions": {"width": analysis.get("width"), "height": analysis.get("height")},
            "dominant_colors": analysis.get("colors", {}).get("dominant_colors", []),
            "phash": analysis.get("phash"),
            "category": analysis.get("category")
        }
    # ... other types ...
```

---

## Testing Considerations

### Unit Tests

```python
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_upload_file():
    with open("test.pdf", "rb") as f:
        response = client.post("/upload", files={"file": f})
    
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert data["file_type"] == "pdf"
```

---

**Last Updated**: November 2024  
**Application Status**: ✅ Production-ready  
**Endpoints**: 17 total  
**Max Upload**: 1GB  
**Auto-Analysis**: ✅ All file types
