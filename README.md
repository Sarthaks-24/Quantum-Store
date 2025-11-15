# QuantumStore - File Intelligence Engine

**Local-first file storage with advanced AI-powered classification and analytics.**

Modern dashboard UI built with React + Tailwind CSS + Framer Motion + Recharts, integrated with FastAPI backend featuring multi-level file classification.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![React](https://img.shields.io/badge/React-18.2-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)
![Python](https://img.shields.io/badge/Python-3.8+-3776ab)

---

## 🚀 Quick Start (Unified Dev Environment)

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- pip

### One-Command Setup

```bash
# 1. Install all dependencies (frontend + backend)
npm run install:all

# 2. Start both frontend and backend simultaneously
npm run dev
```

This will launch:
- **Frontend** at `http://localhost:3000` (Vite dev server)
- **Backend API** at `http://localhost:8000` (FastAPI)

Both services run concurrently with live reload enabled.

---

## 📋 Manual Setup (Alternative)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## 🎨 Features

### Frontend Dashboard
- **Modern Glassmorphic UI** - Soft gradients, blur effects, smooth animations
- **Real-time Analytics** - File stats, type distribution charts, activity graphs
- **Advanced File Preview** - Modal with metadata, classification details, download
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Offline Support** - Graceful fallback to mock data when API unavailable

### Backend Classification
- **40+ File Categories** - Images, PDFs, JSON, Audio, Video with subcategories
- **Multi-level Classification** - Primary category + subcategories + confidence score
- **Advanced Detection**:
  - **Images**: Screenshots, AI-generated, memes, scanned docs (15+ types)
  - **PDFs**: Forms, receipts, ebooks, slides (9 types)
  - **JSON**: SQL-ready, nested, flat structured (5 types)
  - **Audio**: WhatsApp voice, podcasts, music (5 types)
  - **Video**: Screen recordings, portrait/landscape, YouTube-like (5 types)
- **No ML Models** - Pure heuristics (EXIF, resolution, aspect ratio, keywords)

---

## 📁 Project Structure

```
quantumstore/
├── frontend/                    # React + Vite frontend
│   ├── src/
│   │   ├── components/
│   │   │   └── ui/
│   │   │       ├── Dashboard.jsx       # Main dashboard
│   │   │       └── PreviewModal.jsx    # File preview modal
│   │   ├── styles/
│   │   │   └── globals.css            # Tailwind + custom styles
│   │   ├── mocks/
│   │   │   └── dashboard.json         # Fallback data
│   │   ├── api.js                     # Backend API integration
│   │   ├── App.jsx                    # Router setup
│   │   └── main.jsx                   # Entry point
│   ├── tests/
│   │   └── Dashboard.test.jsx         # Component tests
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── backend/                     # FastAPI backend
│   ├── classifier.py            # Advanced classification system
│   ├── app.py                   # API endpoints
│   ├── processors/              # File analysis modules
│   │   ├── image_processor.py
│   │   ├── pdf_processor.py
│   │   ├── json_processor.py
│   │   ├── video_processor.py
│   │   └── text_processor.py
│   ├── storage/
│   │   └── store.py             # File storage
│   └── requirements.txt
│
├── package.json                 # Root package (unified dev)
├── .env.example                 # Environment variables template
└── README.md
```

---

## 🛠️ Technology Stack

### Frontend
- **React 18.2** - UI library
- **Tailwind CSS 3.4** - Utility-first styling
- **Framer Motion 10** - Animation library
- **Recharts 2.10** - Chart components
- **Lucide React** - Icon library
- **React Router DOM 6** - Client-side routing
- **Vite 5** - Build tool

### Backend
- **FastAPI** - Modern Python web framework
- **PyPDF2** - PDF processing
- **Pillow** - Image analysis
- **OpenCV** - Video processing
- **scikit-learn** - Color clustering

---

## 🎯 API Endpoints

### File Management
```
GET  /files                    # List all files (with optional ?limit=N)
GET  /files/{id}/preview       # Get file preview/metadata
GET  /files/{id}/download      # Download file
POST /upload                   # Upload single file
POST /upload/folder            # Upload folder
POST /upload/batch             # Batch upload
```

### Analysis
```
POST /analyze/json             # Analyze JSON structure
POST /analyze/pdf              # Analyze PDF content
POST /analyze/image            # Analyze image
POST /analyze/video            # Analyze video
POST /analyze/text             # Analyze text file
```

### Classification
All files are automatically classified on upload using the advanced classifier:

```json
{
  "type": "image",
  "category": "image_screenshot",
  "subcategories": ["image_png", "image_landscape"],
  "confidence": 0.85
}
```

---

## 🎨 UI Theme

### Custom Tailwind Tokens

```javascript
colors: {
  'bg-gradient-start': '#0f172a',  // Dark blue
  'bg-gradient-end': '#071033',    // Darker blue
  'accent-indigo': '#7c3aed',      // Primary accent
  'accent-teal': '#06b6d4',        // Secondary accent
}

shadows: {
  'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
  'glow-indigo': '0 0 20px rgba(124, 58, 237, 0.5)',
  'glow-teal': '0 0 20px rgba(6, 182, 212, 0.5)',
}
```

### Glassmorphism
All cards use the `.glass-card` utility class:
- `bg-white/5` - Semi-transparent background
- `backdrop-blur-glass` - 4px blur
- `border border-white/10` - Subtle border
- `shadow-glass` - Soft shadow

---

## 🧪 Testing

### Run Frontend Tests

```bash
cd frontend
npm test
```

Tests cover:
- Dashboard stat card rendering
- API integration with mocked responses
- Empty state handling
- File preview modal

---

## 📊 Classification Examples

### Image Screenshot
```javascript
{
  type: "image",
  category: "image_screenshot",
  subcategories: ["image_png", "image_landscape"],
  confidence: 0.85
}
// Detection: 1920x1080 PNG without EXIF
```

### JSON SQL-Ready
```javascript
{
  type: "json",
  category: "json_flat_structured",
  subcategories: ["sql_ready", "has_schema"],
  confidence: 0.95
}
// Detection: Array of objects, 95%+ consistency, depth ≤2
```

### PDF Receipt
```javascript
{
  type: "pdf",
  category: "pdf_receipt",
  subcategories: ["short_document"],
  confidence: 0.85
}
// Detection: ≤2 pages + keywords (total, tax, receipt)
```

---

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit values:
```env
VITE_API_URL=http://localhost:8000
VITE_PORT=3000
BACKEND_PORT=8000
```

### Ports
- Frontend: `3000` (Vite dev server)
- Backend: `8000` (FastAPI)
- Vite proxies `/api/*` requests to backend

---

## 📦 Build for Production

### Frontend
```bash
cd frontend
npm run build
# Output: frontend/dist/
```

### Backend
```bash
cd backend
# Deploy using: gunicorn, uvicorn, Docker, etc.
```

---

## 🐛 Troubleshooting

### "API unavailable" in Dashboard
- **Cause**: Backend not running
- **Fix**: Run `npm run dev` to start both services

### Blank dashboard
- **Cause**: No files uploaded yet
- **Fix**: Upload files via UI or API

### Classification confidence low
- **Cause**: Missing metadata (e.g., no EXIF, ambiguous structure)
- **Expected**: Fallback to extension-based grouping

---

## ✅ QA Checklist

- [ ] Both frontend and backend start with `npm run dev`
- [ ] Dashboard loads at `http://localhost:3000/dashboard`
- [ ] API responds at `http://localhost:8000/health`
- [ ] File upload works via UI
- [ ] Preview modal opens on file click
- [ ] Download button works
- [ ] Charts render with data
- [ ] Classification shows subcategories
- [ ] Responsive on mobile
- [ ] Tests pass: `cd frontend && npm test`

---

## 📚 Documentation

- [Advanced Classification System](./ADVANCED_CLASSIFICATION_SYSTEM.md)
- [Classification Rebuild Summary](./CLASSIFICATION_REBUILD_SUMMARY.md)
- API Swagger Docs: `http://localhost:8000/docs`

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- Tailwind CSS team for the amazing framework
- Framer Motion for smooth animations
- Recharts for beautiful charts
- FastAPI for the modern Python framework

---

**Built with ❤️ using React + FastAPI**
