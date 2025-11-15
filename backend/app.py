from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
from datetime import datetime
import traceback
import sys

from processors.json_processor import JSONProcessor
from processors.text_processor import TextProcessor
from processors.image_processor import ImageProcessor
from rules.rules import RuleEngine
from storage.store import LocalStore
from utils.file_utils import get_file_type, save_uploaded_file
from utils.serializers import sanitize_for_json

app = FastAPI(title="QuantumStore", description="Local-First File Intelligence Engine")

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
        file_type = get_file_type(file.filename)
        
        file_path = save_uploaded_file(file, file_id)
        
        metadata = {
            "id": file_id,
            "filename": file.filename,
            "file_type": file_type,
            "size": os.path.getsize(file_path),
            "uploaded_at": datetime.utcnow().isoformat(),
            "path": file_path
        }
        
        store.save_metadata(file_id, metadata)
        
        return JSONResponse(content={
            "file_id": file_id,
            "filename": file.filename,
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
            try:
                file_id = str(uuid.uuid4())
                file_type = get_file_type(file.filename)
                
                file_path = save_uploaded_file(file, file_id)
                
                metadata = {
                    "id": file_id,
                    "filename": file.filename,
                    "file_type": file_type,
                    "size": os.path.getsize(file_path),
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
                    print(f"Analysis failed for {file.filename}: {str(analysis_error)}")
                    analysis = {"error": str(analysis_error)}
                
                results.append({
                    "file_id": file_id,
                    "filename": file.filename,
                    "file_type": file_type,
                    "size": metadata["size"],
                    "analyzed": analysis is not None and "error" not in analysis,
                    "analysis_preview": {
                        "type": file_type,
                        "status": "success" if analysis and "error" not in analysis else "failed"
                    } if analysis else None
                })
            except Exception as file_error:
                results.append({
                    "filename": file.filename,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
