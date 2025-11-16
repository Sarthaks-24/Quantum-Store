# QuantumStore - System Architecture Documentation

**Version**: 1.0.0  
**Last Updated**: November 2024  
**Architecture Type**: Local-First File Intelligence System

---

## 🏗️ High-Level Architecture

QuantumStore is a **full-stack local-first file management system** with advanced AI-powered classification. The system consists of three main layers:

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND LAYER                           │
│  React 18 + Vite + Tailwind CSS + Framer Motion            │
│  - Dashboard UI    - File Browser    - Upload Interface    │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/JSON
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND API LAYER                        │
│           FastAPI + Python 3.8+                             │
│  - REST Endpoints  - File Upload  - Analysis Orchestration │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                  PROCESSING & STORAGE LAYER                  │
│  - File Processors - Classifier - LocalStore - Cache        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Technology Stack

### Frontend
- **Framework**: React 18.2 (with Hooks, Memo, Callback optimizations)
- **Build Tool**: Vite 5 (Fast HMR, ESBuild)
- **Styling**: Tailwind CSS 3.4 (Utility-first CSS)
- **Animations**: Framer Motion 10 (Smooth transitions)
- **Charts**: Recharts (Data visualization)
- **Icons**: Lucide React (SVG icon library)
- **Routing**: React Router DOM 6 (Client-side routing)

### Backend
- **Framework**: FastAPI (Modern async Python web framework)
- **File Processing**:
  - PyMuPDF (fitz) - PDF analysis
  - Pillow (PIL) - Image processing
  - pytesseract - OCR text extraction
  - OpenCV (cv2) - Computer vision
  - imagehash - Perceptual hashing
  - scikit-learn - Text analytics (TF-IDF)
- **Storage**: JSON-based file system (LocalStore)

### Development Tools
- **Testing**: Vitest (Frontend unit tests)
- **Package Manager**: npm (Frontend), pip (Backend)
- **Concurrent Execution**: concurrently (Run frontend + backend simultaneously)

---

## 🎯 Core Design Principles

### 1. **Local-First Architecture**
- No cloud dependencies
- All data stored locally in `./data` directory
- No external API calls or database connections
- Privacy-preserving by design

### 2. **Heuristic-Based Classification**
- **Zero ML models** - All classification uses rule-based heuristics
- Fast, deterministic, and explainable
- Based on metadata analysis (EXIF, file structure, content patterns)

### 3. **Processor Pattern**
- Each file type has a dedicated processor
- Processors are independent and swappable
- Common interface: `analyze(file_path) -> Dict[str, Any]`

### 4. **Component-Based Frontend**
- Reusable UI components (StatCard, FileCard, ZoomControls)
- Performance-optimized with React.memo, useCallback, useMemo
- Debounced search and memoized calculations

### 5. **RESTful API Design**
- Clear endpoint structure (`/upload`, `/files`, `/analyze/{type}`)
- Consistent error handling (HTTPException with status codes)
- CORS enabled for local development

---

## 📁 Directory Structure

```
quantumstore/
├── frontend/                      # React frontend application
│   ├── src/
│   │   ├── components/ui/         # UI components
│   │   │   ├── Dashboard.jsx      # Main dashboard with stats
│   │   │   ├── Files.jsx          # File browser with filters
│   │   │   ├── Upload.jsx         # Drag-and-drop uploader
│   │   │   ├── PreviewModal.jsx   # File preview with zoom
│   │   │   └── Layout.jsx         # App shell with sidebar
│   │   ├── api.js                 # Backend API client
│   │   ├── App.jsx                # Root component with routing
│   │   └── styles/globals.css     # Global styles + Tailwind
│   ├── package.json               # Frontend dependencies
│   └── vite.config.js             # Vite configuration
│
├── backend/                       # FastAPI backend
│   ├── app.py                     # Main FastAPI application
│   ├── classifier.py              # Advanced file classifier
│   ├── processors/                # File type processors
│   │   ├── image_processor.py     # Image analysis
│   │   ├── pdf_processor.py       # PDF text extraction + OCR
│   │   ├── json_processor.py      # JSON structure analysis
│   │   ├── text_processor.py      # Text analytics (TF-IDF)
│   │   └── video_processor.py     # Video metadata
│   ├── storage/
│   │   └── store.py               # LocalStore (JSON file storage)
│   ├── rules/
│   │   ├── rules.py               # Rule engine
│   │   └── heuristics.py          # Classification heuristics
│   └── utils/
│       ├── file_utils.py          # File handling utilities
│       ├── serializers.py         # JSON serialization
│       └── metrics.py             # Similarity metrics
│
├── data/                          # Local storage directory
│   ├── raw/uploads/               # Original uploaded files
│   ├── processed/metadata/        # File metadata (JSON)
│   ├── processed/schemas/         # Extracted JSON schemas
│   └── cache/                     # Indices (pHash, TF-IDF)
│
├── docs/                          # **This documentation**
├── package.json                   # Root package (dev scripts)
├── requirements.txt               # Python dependencies
└── .env.example                   # Environment configuration template
```

---

## 🔄 Data Flow

### File Upload Flow

```
1. USER ACTION
   │
   ├─> Drag & Drop OR Browse Files (Upload.jsx)
   │
2. FRONTEND
   │
   ├─> uploadFiles() in api.js
   ├─> POST /upload/batch with FormData
   │
3. BACKEND API (app.py)
   │
   ├─> Validate file size (1GB limit)
   ├─> Save to data/raw/uploads/{file_id}
   ├─> Store metadata (LocalStore.save_metadata)
   │
4. AUTO-ANALYSIS
   │
   ├─> Detect file type (get_file_type)
   ├─> Route to processor:
   │   ├─> PDFProcessor.analyze()
   │   ├─> ImageProcessor.analyze()
   │   ├─> JSONProcessor.analyze()
   │   ├─> TextProcessor.analyze()
   │   └─> VideoProcessor.analyze()
   │
5. CLASSIFICATION
   │
   ├─> classify_file() in classifier.py
   ├─> Apply heuristics (resolution, EXIF, keywords)
   ├─> Generate confidence score
   ├─> Return { type, category, subcategories, confidence }
   │
6. STORAGE
   │
   ├─> Save analysis to metadata JSON
   ├─> Update cache indices (pHash, TF-IDF)
   │
7. RESPONSE
   │
   └─> Return file_id + analysis results to frontend
```

### File Retrieval Flow

```
1. USER NAVIGATION
   │
   ├─> Click "Files" in sidebar (Layout.jsx)
   │
2. FRONTEND
   │
   ├─> Files.jsx mounts
   ├─> fetchFiles() in api.js
   ├─> GET /files
   │
3. BACKEND API
   │
   ├─> LocalStore.list_files()
   ├─> Load all metadata JSON files
   ├─> Return array of file objects
   │
4. FRONTEND RENDERING
   │
   ├─> Apply filters (type, date, size)
   ├─> Apply sorting (newest, largest, name)
   ├─> Render FileCard components (memoized)
   │
5. FILE PREVIEW
   │
   ├─> User clicks file card
   ├─> PreviewModal opens
   ├─> fetchFilePreview(file_id) → GET /file/{file_id}/preview
   ├─> Fetch analytics → GET /file/{file_id}/analytics/{type}
   │
6. DISPLAY
   │
   └─> Show metadata, preview, analytics with zoom controls
```

---

## 🧠 Classification System

### Multi-Level Classification

Every file receives a **three-level classification**:

```javascript
{
  "type": "image",                    // Primary type
  "category": "image_screenshot",     // Specific category
  "subcategories": [                  // Additional tags
    "image_png",
    "image_landscape"
  ],
  "confidence": 0.87                  // 0.0 - 1.0
}
```

### Classification Heuristics

#### **Images** (15+ categories)
- Screenshot detection: 16:9/16:10 aspect ratio
- AI-generated: Specific dimensions (512x512, 1024x1024)
- Scanned documents: High DPI + text-like patterns
- Memes: Square aspect ratio + low resolution
- Photos: EXIF GPS data or camera info

#### **PDFs** (9 categories)
- Scanned: No text layer detected
- Forms: High occurrence of "Name", "Date", "Signature"
- Receipts: Keywords like "Total", "Tax", "Payment"
- E-books: > 50 pages + chapter-like structure
- Slides: Landscape orientation + bullet points

#### **JSON** (5 categories)
- SQL-ready: Array of objects with consistent schemas
- Flat structured: < 3 nesting levels
- Deeply nested: > 5 nesting levels
- Config files: Keys like "settings", "version"

#### **Audio** (5 categories)
- WhatsApp voice notes: .opus, < 5 minutes
- Podcasts: > 20 minutes
- Music: Standard bitrates (128/320 kbps)

#### **Video** (5 categories)
- Screen recordings: 16:9, no camera shake
- Portrait video: 9:16 aspect ratio
- YouTube-like: 1080p/720p, standard codecs

---

## 🔌 API Endpoints

### Upload Endpoints
- **POST /upload** - Single file upload with auto-analysis
- **POST /upload/batch** - Multiple file upload

### File Management
- **GET /files** - List all files with metadata
- **GET /file/{file_id}** - Get specific file metadata
- **GET /file/{file_id}/preview** - Get file preview data
- **GET /file/{file_id}/download** - Download original file

### Analysis Endpoints
- **POST /analyze/json** - Analyze JSON file
- **POST /analyze/text** - Analyze text file
- **POST /analyze/image** - Analyze image file
- **POST /analyze/pdf** - Analyze PDF file
- **POST /analyze/video** - Analyze video file

### Summary & Groups
- **GET /summary** - Dashboard summary statistics
- **GET /groups** - Get file groups
- **POST /groups/rebuild** - Rebuild file groups
- **POST /groups/auto** - Auto-generate groups

### Health Check
- **GET /health** - API health status

---

## 🎨 Frontend Components

### Component Hierarchy

```
App.jsx (Router)
└── Layout.jsx (Sidebar + Main Area)
    ├── Dashboard.jsx
    │   ├── StatCard (x4)
    │   ├── ChartCard (Weekly Activity)
    │   ├── ChartCard (Type Distribution)
    │   └── FileCard (Recent Uploads x10)
    │
    ├── Files.jsx
    │   ├── Search & Filters
    │   ├── Type Filter Buttons
    │   └── FileCard (Grid of files)
    │
    └── Upload.jsx
        ├── Drop Zone
        ├── File List (Selected)
        └── Upload Progress
```

### Shared Components

- **StatCard** - Metric display (Total Files, Storage Used, etc.)
- **FileCard** - File thumbnail with metadata
- **ZoomControls** - Image/PDF zoom interface
- **PreviewModal** - Full-screen file preview

---

## 💾 Storage Architecture

### LocalStore Structure

```
data/
├── raw/uploads/
│   └── {file_id}.{ext}           # Original files
│
├── processed/metadata/
│   └── {file_id}.json            # File metadata + analysis
│       {
│         "id": "uuid",
│         "filename": "doc.pdf",
│         "file_type": "pdf",
│         "size": 1024000,
│         "uploaded_at": "ISO-8601",
│         "classification": {...},
│         "analysis": {...}
│       }
│
├── processed/schemas/
│   └── {file_id}_schema.json     # Extracted JSON schemas
│
└── cache/
    ├── phash_index.json          # Image perceptual hashes
    └── tfidf_index.json          # Text TF-IDF vectors
```

### Metadata Structure

Each file's metadata is stored as a JSON file with:

- **Core fields**: id, filename, file_type, size, uploaded_at, path
- **Classification**: type, category, subcategories, confidence
- **Analysis** (type-specific):
  - Images: dimensions, format, color_mode, phash, dominant_colors
  - PDFs: page_count, has_text, extracted_text, preview (Base64)
  - JSON: depth, keys, structure, sql_ready
  - Text: word_count, unique_words, top_words, tfidf_vector
  - Video: duration, codec, resolution, fps

---

## 🔐 Security Considerations

### File Upload Security
- **Size Limit**: 1GB per file (enforced by middleware)
- **Extension Validation**: Checked against whitelist
- **MIME Type Verification**: Cross-referenced with extension
- **No Executable Processing**: Binary files stored but not executed

### Data Privacy
- **Local Storage Only**: No external API calls
- **No Telemetry**: No analytics or tracking
- **Sandboxed Processing**: File processors run in isolated context

### CORS Configuration
- **Development**: `allow_origins=["*"]` (localhost only)
- **Production**: Should be configured to specific domains

---

## ⚡ Performance Optimizations

### Frontend
1. **React.memo** - Prevents unnecessary component re-renders
2. **useCallback** - Memoizes event handlers
3. **useMemo** - Caches expensive calculations
4. **Debounced Search** - 300ms delay on search input
5. **Lazy Loading** - (Planned) Code-split routes

### Backend
1. **Async/Await** - FastAPI async endpoints
2. **File Streaming** - Large files not loaded into memory
3. **Cache Indices** - Pre-computed pHash and TF-IDF
4. **Selective Analysis** - Only analyze when requested

### Storage
1. **JSON Files** - Fast read/write for metadata
2. **Index Files** - Quick lookup for duplicates/similarity
3. **No Database Overhead** - Direct file system access

---

## 🐛 Known Limitations

1. **No Concurrent Uploads** - File upload processes sequentially
2. **No Real-Time Sync** - Manual refresh needed after external file changes
3. **No Full-Text Search** - Search only works on filenames
4. **No Cloud Backup** - Local-only storage
5. **Limited Video Analysis** - Metadata only, no frame extraction
6. **No Thumbnail Generation** - PDFs have Base64 preview only

---

## 🚀 Future Enhancements

### Planned Features
- [ ] PostgreSQL/SQLite support for metadata
- [ ] Redis caching for faster queries
- [ ] Full-text search with Elasticsearch
- [ ] WebSocket for real-time updates
- [ ] Thumbnail generation for all file types
- [ ] Duplicate file detection UI
- [ ] Batch file operations (delete, move, tag)
- [ ] Export/import functionality
- [ ] API authentication (JWT tokens)

### Possible Improvements
- [ ] TypeScript migration
- [ ] GraphQL API alternative
- [ ] Mobile-responsive design enhancements
- [ ] Dark/light theme toggle
- [ ] Keyboard shortcuts
- [ ] Accessibility (ARIA labels)

---

## 📚 Related Documentation

- [Frontend Components](./frontend/) - React component documentation
- [Backend API](./backend/) - API endpoint details
- [Processors](./backend/processors/) - File processor documentation
- [Classification System](./backend/classifier.md) - Detailed heuristics
- [Storage System](./backend/store.md) - LocalStore implementation

---

**Last Updated**: November 2024  
**Maintainers**: QuantumStore Development Team
