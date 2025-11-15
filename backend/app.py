from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
from datetime import datetime

from processors.json_processor import JSONProcessor
from processors.text_processor import TextProcessor
from processors.image_processor import ImageProcessor
from rules.rules import RuleEngine
from storage.store import LocalStore
from utils.file_utils import get_file_type, save_uploaded_file

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

@app.post("/analyze/json")
async def analyze_json(file_id: str):
    try:
        metadata = store.get_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = metadata["path"]
        
        analysis = json_processor.analyze(file_path)
        
        store.save_analysis(file_id, "json", analysis)
        
        if "schema" in analysis:
            store.save_schema(analysis["schema"])
        
        return JSONResponse(content=analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        
        return JSONResponse(content=analysis)
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
        
        return JSONResponse(content=analysis)
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
