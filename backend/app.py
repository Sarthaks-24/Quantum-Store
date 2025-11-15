from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional, Dict, Any
import os
import uuid
from datetime import datetime
import traceback
import sys
import base64
from PIL import Image
import io

from processors.json_processor import JSONProcessor
from processors.text_processor import TextProcessor
from processors.image_processor import ImageProcessor
from processors.pdf_processor import PDFProcessor
from processors.video_processor import VideoProcessor
from rules.rules import RuleEngine
from storage.store import LocalStore
from utils.file_utils import get_file_type, save_uploaded_file, save_upload_file, clean_filename
from utils.serializers import sanitize_for_json
from classifier import classify_file  # NEW: Unified classifier
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Maximum request body size: 1GB
MAX_UPLOAD_SIZE = 1 * 1024 * 1024 * 1024  # 1GB in bytes (1,073,741,824)
MAX_UPLOAD_SIZE_MB = MAX_UPLOAD_SIZE / (1024 * 1024)

class LimitUploadSize(BaseHTTPMiddleware):
    """Middleware to enforce 1GB upload size limit on all POST requests."""
    
    async def dispatch(self, request: Request, call_next):
        if request.method == 'POST':
            content_length = request.headers.get('content-length')
            if content_length:
                size_bytes = int(content_length)
                if size_bytes > MAX_UPLOAD_SIZE:
                    size_mb = size_bytes / (1024 * 1024)
                    print(f"[UPLOAD_LIMIT] Rejecting request: size = {size_bytes:,} bytes ({size_mb:.2f} MB)")
                    print(f"[UPLOAD_LIMIT] Maximum allowed: {MAX_UPLOAD_SIZE:,} bytes ({MAX_UPLOAD_SIZE_MB:.0f} MB)")
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Upload exceeds 1GB limit",
                            "max_size_bytes": MAX_UPLOAD_SIZE,
                            "max_size_mb": MAX_UPLOAD_SIZE_MB,
                            "received_size_bytes": size_bytes,
                            "received_size_mb": size_mb
                        }
                    )
        return await call_next(request)

app = FastAPI(title="QuantumStore", description="Local-First File Intelligence Engine")

# Add request body size limit middleware
app.add_middleware(LimitUploadSize)

# Add request body size limit (500MB max)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = LocalStore()
json_processor = JSONProcessor()
text_processor = TextProcessor()
image_processor = ImageProcessor()
pdf_processor = PDFProcessor()
video_processor = VideoProcessor()
rule_engine = RuleEngine()

def save_analysis_with_classification(
    file_id: str,
    file_type: str,
    analysis: Dict[str, Any],
    metadata: Dict[str, Any],
    file_path: str
) -> Dict[str, Any]:
    """
    ADVANCED MULTI-LEVEL CLASSIFICATION - Single entry point.
    Uses new classifier.py with subcategories and confidence scoring.
    
    Args:
        file_id: File identifier
        file_type: Type of file from initial detection
        analysis: Analysis results from processor
        metadata: File metadata
        file_path: Path to file
    
    Returns:
        Updated analysis with classification
    """
    # Run advanced classification with new interface
    classification = classify_file(
        metadata=metadata,
        preview=analysis,  # Pass processor analysis for content-based classification
        full_path=file_path
    )
    
    print(f"[CLASSIFY] {metadata['filename']}")
    print(f"  Type: {classification['type']}")
    print(f"  Category: {classification['category']}")
    print(f"  Subcategories: {', '.join(classification.get('subcategories', []))}")
    print(f"  Confidence: {classification['confidence']:.2f}")
    
    # Store full classification with subcategories
    metadata["classification"] = classification
    metadata["category"] = classification["category"]  # Primary category for grouping
    metadata["subcategories"] = classification.get("subcategories", [])
    metadata["confidence"] = classification["confidence"]
    store.save_metadata(file_id, metadata)
    
    # Add classification to analysis
    analysis["classification"] = classification
    
    # Save analysis
    store.save_analysis(file_id, file_type, analysis)
    
    # Add to group by primary category (idempotent - uses index)
    store.add_file_to_group(file_id, classification["category"])
    
    return analysis

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "QuantumStore", "timestamp": datetime.utcnow().isoformat()}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload single file with normalized detection and categorization."""
    try:
        file_id = str(uuid.uuid4())
        filename = file.filename
        
        # Determine file type with comprehensive PDF detection
        file_type = get_file_type(filename, file.content_type)
        
        print(f"[UPLOAD] File: {filename}, Type: {file_type}, MIME: {file.content_type}")
        
        # Save file and check size
        file_path = await save_upload_file(file, file_id)
        file_size = os.path.getsize(file_path)
        
        # Secondary size check
        if file_size > MAX_UPLOAD_SIZE:
            os.remove(file_path)
            size_mb = file_size / (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "Upload exceeds 1GB limit",
                    "filename": filename,
                    "size_bytes": file_size,
                    "size_mb": size_mb,
                    "max_size_mb": MAX_UPLOAD_SIZE_MB
                }
            )
        
        # Create metadata with MIME type for classifier
        metadata = {
            "id": file_id,
            "filename": filename,
            "file_type": file_type,
            "mime_type": file.content_type,
            "size": file_size,
            "uploaded_at": datetime.utcnow().isoformat(),
            "path": file_path
        }
        
        store.save_metadata(file_id, metadata)
        
        return JSONResponse(content={
            "file_id": file_id,
            "filename": filename,
            "file_type": file_type,
            "message": "File uploaded successfully"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/batch")
async def upload_batch(files: List[UploadFile] = File(...), folder_id: str = Form(None)):
    """Upload multiple files with comprehensive file type detection."""
    try:
        if not folder_id:
            folder_id = f"upload_{uuid.uuid4().hex[:8]}"
        
        uploaded_at = datetime.utcnow().isoformat()
        results = []
        
        print(f"[UPLOAD] Batch upload starting: {len(files)} files, folder: {folder_id}")
        
        for file in files:
            filename = None
            try:
                filename = file.filename
                file_content = await file.read()
                file_size = len(file_content)
                
                if file_size > MAX_UPLOAD_SIZE:
                    size_mb = file_size / (1024 * 1024)
                    results.append({
                        "filename": filename,
                        "error": f"File exceeds {MAX_UPLOAD_SIZE_MB:.0f}MB limit ({size_mb:.2f}MB)",
                        "status": "rejected"
                    })
                    continue
                
                file_id = str(uuid.uuid4())
                file_path = save_uploaded_file(file_content, filename, folder_id)
                
                # Comprehensive file type detection
                file_type = get_file_type(filename, file.content_type)
                
                metadata = {
                    "id": file_id,
                    "filename": filename,
                    "file_type": file_type,
                    "mime_type": file.content_type,
                    "path": file_path,
                    "size": file_size,
                    "uploaded_at": uploaded_at,
                    "folder_id": folder_id
                }
                store.save_metadata(file_id, metadata)
                
                results.append({
                    "file_id": file_id,
                    "filename": filename,
                    "file_type": file_type,
                    "size": file_size,
                    "analyzed": False
                })
                
            except Exception as file_error:
                error_filename = filename if filename else "<unknown>"
                print(f"[UPLOAD] File {error_filename} failed: {str(file_error)}")
                results.append({
                    "filename": error_filename,
                    "error": str(file_error),
                    "status": "failed"
                })
        
        successful = len([r for r in results if "error" not in r and r.get("status") != "rejected"])
        failed = len([r for r in results if "error" in r or r.get("status") == "rejected"])
        
        print(f"[UPLOAD] Batch complete: {successful}/{len(files)} successful")
        
        return JSONResponse(content={
            "folder_id": folder_id,
            "total_files": len(files),
            "successful": successful,
            "failed": failed,
            "results": results,
            "message": f"Upload complete: {successful}/{len(files)} files"
        })
        
    except Exception as e:
        print(f"[UPLOAD] Batch upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/json")
async def analyze_json(file_id: str):
    """Analyze JSON file with deep classification and SQL schema generation."""
    try:
        print(f"[ANALYSIS] JSON analysis starting for {file_id}")
        
        metadata = store.get_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = metadata["path"]
        file_size = metadata.get("size", 0)
        
        # Analyze
        analysis = json_processor.analyze(file_path, file_size)
        
        # Save with unified classification
        analysis = save_analysis_with_classification(file_id, "json", analysis, metadata, file_path)
        
        # Generate SQL schema for SQL-suitable JSON
        content_category = analysis.get("content_category", "")
        if "sql" in content_category.lower() and "schema" in analysis:
            print(f"[ANALYSIS] Generating SQL schema for {content_category}")
            db_path = os.path.join(store.schemas_path, f"{file_id}.db")
            schema = analysis["schema"]
            samples = analysis.get("samples", [])
            
            if json_processor.create_schema_database(file_id, schema, samples, db_path):
                # Save schema reference
                schema_id = store.save_schema(schema)
                if schema_id:
                    metadata["schema_id"] = schema_id
                    metadata["schema_db"] = db_path
                    store.save_metadata(file_id, metadata)
                    print(f"[ANALYSIS] SQL schema saved: {schema_id}")
        
        print(f"[ANALYSIS] JSON analysis complete: {content_category}")
        return JSONResponse(content=sanitize_for_json(analysis))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] JSON analysis failed: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/text")
async def analyze_text(file_id: str):
    """Analyze text file."""
    try:
        print(f"[ANALYSIS] Text analysis starting for {file_id}")
        
        metadata = store.get_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = metadata["path"]
        all_files = store.get_all_files()
        corpus_paths = [f["path"] for f in all_files if f.get("file_type") == "text"]
        
        # Analyze
        analysis = text_processor.analyze(file_path, corpus_paths)
        
        # Save with unified classification
        analysis = save_analysis_with_classification(file_id, "text", analysis, metadata, file_path)
        
        print(f"[ANALYSIS] Text analysis complete for {file_id}")
        return JSONResponse(content=sanitize_for_json(analysis))
        
    except Exception as e:
        print(f"[ERROR] Text analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/image")
async def analyze_image(file_id: str):
    """Analyze image file."""
    try:
        print(f"[ANALYSIS] Image analysis starting for {file_id}")
        
        metadata = store.get_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = metadata["path"]
        
        # Analyze
        analysis = image_processor.analyze(file_path)
        
        # Update pHash index
        if analysis.get("phash"):
            store.update_phash_index(file_id, analysis["phash"])
        
        # Save with unified classification
        analysis = save_analysis_with_classification(file_id, "image", analysis, metadata, file_path)
        
        print(f"[ANALYSIS] Image analysis complete for {file_id}")
        return JSONResponse(content=sanitize_for_json(analysis))
        
    except Exception as e:
        print(f"[ERROR] Image analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/pdf")
async def analyze_pdf(file_id: str):
    """Analyze PDF with comprehensive detection and OCR fallback."""
    try:
        print(f"[ANALYSIS] PDF analysis starting for {file_id}")
        
        metadata = store.get_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = metadata["path"]
        
        # Analyze
        analysis = pdf_processor.analyze(file_path)
        
        # Save with unified classification
        analysis = save_analysis_with_classification(file_id, "pdf", analysis, metadata, file_path)
        
        print(f"[ANALYSIS] PDF analysis complete for {file_id}")
        return JSONResponse(content=sanitize_for_json(analysis))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] PDF analysis failed: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/video")
async def analyze_video(file_id: str):
    """Analyze video file."""
    try:
        print(f"[ANALYSIS] Video analysis starting for {file_id}")
        
        metadata = store.get_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = metadata["path"]
        
        # Analyze
        analysis = video_processor.analyze(file_path)
        
        # Save with unified classification
        analysis = save_analysis_with_classification(file_id, "video", analysis, metadata, file_path)
        
        print(f"[ANALYSIS] Video analysis complete for {file_id}")
        return JSONResponse(content=sanitize_for_json(analysis))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Video analysis failed: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/file/{file_id}")
async def get_file(file_id: str):
    try:
        metadata = store.get_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        analysis = store.get_analysis(file_id)
        
        return JSONResponse(content={
            "metadata": metadata,
            "analysis": analysis
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def get_files():
    try:
        files = store.get_all_files()
        return JSONResponse(content={"files": files, "count": len(files)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/groups")
async def get_groups():
    """Get all category groups with their files."""
    try:
        groups = store.get_all_groups()
        
        # Add count summary
        summary = {
            category: len(files)
            for category, files in groups.items()
        }
        
        return JSONResponse(content={
            "groups": groups,
            "summary": summary,
            "total_categories": len(groups)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/groups/{category}")
async def get_group(category: str):
    """Get all files in a specific category."""
    try:
        files = store.get_group_files(category)
        return JSONResponse(content={
            "category": category,
            "files": files,
            "count": len(files)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/groups/rebuild")
async def rebuild_groups():
    """Rebuild all category groups from metadata."""
    try:
        success = store.rebuild_groups()
        if success:
            groups = store.get_all_groups()
            summary = {
                category: len(files)
                for category, files in groups.items()
            }
            return JSONResponse(content={
                "success": True,
                "message": "Groups rebuilt successfully",
                "summary": summary
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to rebuild groups")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/groups/auto")
async def auto_group():
    try:
        files = store.get_all_files()
        
        groups = rule_engine.auto_group_files(files)
        
        return JSONResponse(content={
            "groups": groups,
            "reasoning": rule_engine.get_last_reasoning_log()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schemas")
async def get_schemas():
    try:
        schemas = store.get_all_schemas()
        return JSONResponse(content={"schemas": schemas, "count": len(schemas)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/file/{file_id}/preview")
async def get_file_preview(file_id: str):
    """Get file preview with metadata and base64 content preview."""
    try:
        # Load metadata
        metadata = store.get_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = metadata.get("path")
        file_type = metadata.get("file_type", "unknown")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Load analysis if available
        analysis = store.get_analysis(file_id)
        
        # Generate preview based on file type
        preview_content = None
        preview_type = None
        
        if file_type == "image":
            # Generate base64 thumbnail for images
            try:
                with Image.open(file_path) as img:
                    # Create thumbnail (max 400x400)
                    img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                    buffer = io.BytesIO()
                    img.save(buffer, format=img.format or 'PNG')
                    preview_content = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    preview_type = "image"
            except Exception as e:
                print(f"Error generating image thumbnail: {e}")
                preview_content = None
        
        elif file_type == "text":
            # Return first 5000 characters of text
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    preview_content = f.read(5000)
                    preview_type = "text"
            except Exception as e:
                print(f"Error reading text file: {e}")
                preview_content = None
        
        elif file_type == "json":
            # Return formatted JSON (first 5000 chars)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(5000)
                    preview_content = content
                    preview_type = "json"
            except Exception as e:
                print(f"Error reading JSON file: {e}")
                preview_content = None
        
        elif file_type == "pdf":
            # For PDFs, return preview image and text from analysis
            preview_type = "pdf"
            preview_data = {}
            
            # If analysis exists, use it; otherwise generate preview on-the-fly
            if analysis and "preview" in analysis:
                preview_data["image"] = analysis["preview"]
                preview_data["text"] = analysis.get("text", "")[:5000]  # First 5000 chars
                preview_data["page_count"] = analysis.get("page_count", 0)
                preview_data["is_scanned"] = analysis.get("is_scanned", False)
            else:
                # Generate preview on-the-fly
                try:
                    pdf_preview = pdf_processor.analyze(file_path)
                    preview_data["image"] = pdf_preview.get("preview", "")
                    preview_data["text"] = pdf_preview.get("text", "")[:5000]
                    preview_data["page_count"] = pdf_preview.get("page_count", 0)
                    preview_data["is_scanned"] = pdf_preview.get("is_scanned", False)
                except Exception as e:
                    print(f"Error generating PDF preview: {e}")
                    preview_data = {}
            
            preview_content = preview_data
        
        elif file_type == "video":
            # For videos, just indicate no preview (don't load full file)
            preview_type = "video"
            preview_content = None
        
        elif file_type == "audio":
            # For audio, just indicate no preview
            preview_type = "audio"
            preview_content = None
        
        else:
            preview_type = "unknown"
            preview_content = None
        
        return JSONResponse(content={
            "file_id": file_id,
            "metadata": metadata,
            "analysis": analysis,
            "preview": {
                "type": preview_type,
                "content": preview_content
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in file preview: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/file/{file_id}/download")
async def download_file(file_id: str):
    """Download the actual file."""
    try:
        metadata = store.get_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = metadata.get("path")
        filename = metadata.get("filename", "download")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in file download: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
