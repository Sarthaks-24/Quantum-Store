from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional, Dict
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
from rules.rules import RuleEngine
from storage.store import LocalStore
from utils.file_utils import get_file_type, save_uploaded_file, save_upload_file, clean_filename
from utils.serializers import sanitize_for_json
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
rule_engine = RuleEngine()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "QuantumStore", "timestamp": datetime.utcnow().isoformat()}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_id = str(uuid.uuid4())
        filename = file.filename  # Store filename before reading
        file_type = get_file_type(filename)
        
        # Save file and immediately check size (safeguard for missing Content-Length)
        file_path = await save_upload_file(file, file_id)
        file_size = os.path.getsize(file_path)
        
        # Secondary size check after file is written
        if file_size > MAX_UPLOAD_SIZE:
            os.remove(file_path)  # Delete oversized file
            size_mb = file_size / (1024 * 1024)
            print(f"[UPLOAD_LIMIT] Rejecting file after upload: {filename} = {file_size:,} bytes ({size_mb:.2f} MB)")
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
        
        metadata = {
            "id": file_id,
            "filename": filename,
            "file_type": file_type,
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

@app.post("/upload/folder")
async def upload_folder(files: List[UploadFile] = File(...)):
    try:
        results = []
        folder_id = str(uuid.uuid4())
        uploaded_at = datetime.utcnow().isoformat()
        
        for file in files:
            filename = None
            try:
                file_id = str(uuid.uuid4())
                filename = file.filename  # Store filename before reading
                file_type = get_file_type(filename)
                
                file_path = await save_upload_file(file, file_id)
                file_size = os.path.getsize(file_path)
                
                # Check individual file size (safeguard)
                if file_size > MAX_UPLOAD_SIZE:
                    os.remove(file_path)
                    size_mb = file_size / (1024 * 1024)
                    print(f"[UPLOAD_LIMIT] Rejecting file in folder upload: {filename} = {file_size:,} bytes ({size_mb:.2f} MB)")
                    results.append({
                        "filename": filename,
                        "error": f"File exceeds 1GB limit ({size_mb:.2f} MB)",
                        "status": "failed"
                    })
                    continue
                
                metadata = {
                    "id": file_id,
                    "filename": filename,
                    "file_type": file_type,
                    "size": file_size,
                    "uploaded_at": uploaded_at,
                    "path": file_path,
                    "folder_id": folder_id
                }
                
                store.save_metadata(file_id, metadata)
                
                # Auto-analyze based on file type
                analysis = None
                try:
                    if file_type == "json":
                        file_size = os.path.getsize(file_path)
                        analysis = json_processor.analyze(file_path, file_size)
                        store.save_analysis(file_id, "json", analysis)
                    elif file_type == "text":
                        all_files = store.get_all_files()
                        corpus_paths = [f["path"] for f in all_files if f.get("file_type") == "text"]
                        analysis = text_processor.analyze(file_path, corpus_paths)
                        store.save_analysis(file_id, "text", analysis)
                    elif file_type == "image":
                        analysis = image_processor.analyze(file_path)
                        store.save_analysis(file_id, "image", analysis)
                        store.update_phash_index(file_id, analysis.get("phash"))
                except Exception as analysis_error:
                    print(f"Analysis failed for {filename}: {str(analysis_error)}")
                    analysis = {"error": str(analysis_error)}
                
                results.append({
                    "file_id": file_id,
                    "filename": filename,
                    "file_type": file_type,
                    "size": metadata["size"],
                    "analyzed": analysis is not None and "error" not in analysis,
                    "analysis_preview": {
                        "type": file_type,
                        "status": "success" if analysis and "error" not in analysis else "failed"
                    } if analysis else None
                })
            except Exception as file_error:
                error_filename = filename if filename else "<unknown>"
                results.append({
                    "filename": error_filename,
                    "error": str(file_error),
                    "status": "failed"
                })
        
        return JSONResponse(content={
            "folder_id": folder_id,
            "total_files": len(files),
            "successful": len([r for r in results if "error" not in r]),
            "failed": len([r for r in results if "error" in r]),
            "results": results,
            "message": f"Processed {len(files)} files from folder"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/batch")
async def upload_batch(files: List[UploadFile] = File(...), folder_id: str = Form(None)):
    """
    Upload multiple files (up to 50 at a time).
    All files are saved to data/raw/uploads/ with the same folder_id prefix.
    """
    try:
        # Generate folder_id if not provided
        if not folder_id:
            folder_id = f"upload_{uuid.uuid4().hex[:8]}"
        
        uploaded_at = datetime.utcnow().isoformat()
        results = []
        
        print(f"\n{'='*70}")
        print(f"[UPLOAD] Starting multi-file upload ({len(files)} files)")
        print(f"[UPLOAD] Folder ID: {folder_id}")
        print(f"{'='*70}\n")
        
        for file in files:
            # Store filename BEFORE reading to avoid losing UploadFile reference
            filename = None
            try:
                # Extract filename while file is still UploadFile
                filename = file.filename
                
                print(f"[UPLOAD] → Uploading {filename}...")
                
                # Read file content
                file_content = await file.read()
                file_size = len(file_content)
                
                if file_size > MAX_UPLOAD_SIZE:
                    size_mb = file_size / (1024 * 1024)
                    print(f"[UPLOAD] → {filename} rejected: {size_mb:.2f} MB exceeds limit")
                    results.append({
                        "filename": filename,
                        "error": f"File exceeds {MAX_UPLOAD_SIZE_MB:.0f}MB limit ({size_mb:.2f}MB)",
                        "status": "rejected"
                    })
                    continue
                
                # Save file with bytes content (filename will be sanitized inside save_uploaded_file)
                file_id = str(uuid.uuid4())
                file_path = save_uploaded_file(file_content, filename, folder_id)
                
                # Get file type
                file_type = get_file_type(file_path)
                
                # Save metadata (consistent with single file and folder upload)
                metadata = {
                    "id": file_id,
                    "filename": filename,
                    "file_type": file_type,
                    "path": file_path,
                    "size": file_size,
                    "uploaded_at": uploaded_at,
                    "folder_id": folder_id
                }
                store.save_metadata(file_id, metadata)
                print(f"[UPLOAD] → {filename} uploaded (ID: {file_id[:8]}...) ... OK")
                
                results.append({
                    "file_id": file_id,
                    "filename": filename,
                    "file_type": file_type,
                    "size": file_size,
                    "analyzed": False  # Analysis will be done separately via /analyze endpoints
                })
                
            except Exception as file_error:
                # Use stored filename or fallback
                error_filename = filename if filename else "<unknown>"
                print(f"[UPLOAD] → {error_filename} failed: {str(file_error)}")
                traceback.print_exc()
                results.append({
                    "filename": error_filename,
                    "error": str(file_error),
                    "status": "failed"
                })
        
        successful = len([r for r in results if "error" not in r and r.get("status") != "rejected"])
        failed = len([r for r in results if "error" in r or r.get("status") == "rejected"])
        
        print(f"[UPLOAD] Completed ({successful}/{len(files)} files)\n")
        
        return JSONResponse(content={
            "folder_id": folder_id,
            "total_files": len(files),
            "successful": successful,
            "failed": failed,
            "results": results,
            "message": f"Upload complete: {successful}/{len(files)} files"
        })
        
    except Exception as e:
        print(f"[UPLOAD] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/json")
async def analyze_json(file_id: str):
    try:
        print(f"\n{'='*60}")
        print(f"[ANALYZE JSON] Starting analysis for file_id: {file_id}")
        print(f"{'='*60}")
        
        # Step 1: Get metadata
        print("[STEP 1] Retrieving metadata...")
        metadata = store.get_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        print(f"  ✓ Metadata retrieved: {metadata.get('filename', 'unknown')}")
        
        file_path = metadata["path"]
        file_size = metadata.get("size", 0)
        print(f"  ✓ File path: {file_path}")
        print(f"  ✓ File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
        
        # Step 2: Analyze JSON
        print("\n[STEP 2] Analyzing JSON file...")
        analysis = json_processor.analyze(file_path, file_size)
        print(f"  ✓ Analysis complete")
        print(f"  - Record count: {analysis.get('record_count', 'N/A')}")
        print(f"  - Is large file: {analysis.get('is_large_file', False)}")
        print(f"  - Has schema: {'schema' in analysis}")
        print(f"  - Has samples: {'samples' in analysis}")
        
        # Debug: Check for problematic types in analysis
        print("\n[DEBUG] Checking analysis for non-serializable types...")
        from decimal import Decimal
        import numpy as np
        
        def check_types(obj, path="root"):
            """Recursively check for problematic types"""
            if isinstance(obj, Decimal):
                print(f"  ⚠ Found Decimal at {path}: {obj}")
            elif isinstance(obj, (np.integer, np.floating)):
                print(f"  ⚠ Found numpy type at {path}: {type(obj).__name__}")
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    check_types(value, f"{path}.{key}")
            elif isinstance(obj, (list, tuple)):
                for i, item in enumerate(obj[:5]):  # Check first 5 items
                    check_types(item, f"{path}[{i}]")
        
        check_types(analysis)
        print("  ✓ Type check complete")
        
        # Step 3: Save analysis
        print("\n[STEP 3] Saving analysis to metadata...")
        store.save_analysis(file_id, "json", analysis)
        print("  ✓ Analysis saved")
        
        # Step 4: Handle schema database for large files
        if analysis.get("is_large_file") and "schema" in analysis:
            print("\n[STEP 4] Creating schema database (large file)...")
            schema = analysis["schema"]
            samples = analysis.get("samples", [])
            print(f"  - Schema fields: {len(schema)}")
            print(f"  - Sample count: {len(samples)}")
            
            # Create schema database
            db_path = os.path.join(store.schemas_path, f"{file_id}.db")
            print(f"  - DB path: {db_path}")
            json_processor.create_schema_database(file_id, schema, samples, db_path)
            print("  ✓ Schema database created")
            
            # Save schema reference
            print("  - Saving schema reference...")
            schema_id = store.save_schema(schema)
            print(f"  ✓ Schema saved with ID: {schema_id}")
            
            # Add database info to metadata
            if schema_id:
                metadata["schema_id"] = schema_id
                metadata["schema_db"] = db_path
                print("  - Updating metadata with schema info...")
                store.save_metadata(file_id, metadata)
                print("  ✓ Metadata updated")
        elif "schema" in analysis:
            print("\n[STEP 4] Saving schema (small file)...")
            # Save schema for small files too
            schema_id = store.save_schema(analysis["schema"])
            if schema_id:
                metadata["schema_id"] = schema_id
                store.save_metadata(file_id, metadata)
                print(f"  ✓ Schema saved with ID: {schema_id}")
        
        print("\n[SUCCESS] Analysis complete, sanitizing for response...")
        # Sanitize analysis before returning to ensure JSON-serializable
        analysis_sanitized = sanitize_for_json(analysis)
        print(f"{'='*60}\n")
        return JSONResponse(content=analysis_sanitized)
        
    except HTTPException:
        raise
    except Exception as e:
        print("\n" + "="*60)
        print("[ERROR] Exception caught in /analyze/json")
        print("="*60)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nFull traceback:")
        print("-"*60)
        traceback.print_exc()
        print("-"*60)
        print("="*60 + "\n")
        
        # Return detailed error
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )
    except Exception as e:
        print("\n[ERROR] Exception in /upload")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={"error": str(e), "traceback": traceback.format_exc()})

@app.post("/analyze/text")
async def analyze_text(file_id: str):
    try:
        metadata = store.get_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = metadata["path"]
        
        all_files = store.get_all_files()
        corpus_paths = [f["path"] for f in all_files if f.get("file_type") == "text"]
        
        analysis = text_processor.analyze(file_path, corpus_paths)
        
        store.save_analysis(file_id, "text", analysis)
        
        analysis_sanitized = sanitize_for_json(analysis)
        return JSONResponse(content=analysis_sanitized)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/image")
async def analyze_image(file_id: str):
    try:
        metadata = store.get_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = metadata["path"]
        
        analysis = image_processor.analyze(file_path)
        
        store.save_analysis(file_id, "image", analysis)
        store.update_phash_index(file_id, analysis.get("phash"))
        
        analysis_sanitized = sanitize_for_json(analysis)
        return JSONResponse(content=analysis_sanitized)
    except Exception as e:
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
