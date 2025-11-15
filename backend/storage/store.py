import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

class LocalStore:
    def __init__(self, base_path: str = "data"):
        self.base_path = base_path
        self.metadata_path = os.path.join(base_path, "processed", "metadata")
        self.schemas_path = os.path.join(base_path, "processed", "schemas")
        self.cache_path = os.path.join(base_path, "cache")
        self.uploads_path = os.path.join(base_path, "raw", "uploads")
        
        self._ensure_directories()
        self._init_indices()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.metadata_path, exist_ok=True)
        os.makedirs(self.schemas_path, exist_ok=True)
        os.makedirs(self.cache_path, exist_ok=True)
        os.makedirs(self.uploads_path, exist_ok=True)
    
    def _init_indices(self):
        """Initialize cache indices."""
        self.phash_index_path = os.path.join(self.cache_path, "phash_index.json")
        self.tfidf_index_path = os.path.join(self.cache_path, "tfidf_index.json")
        
        if not os.path.exists(self.phash_index_path):
            self._save_json(self.phash_index_path, {})
        
        if not os.path.exists(self.tfidf_index_path):
            self._save_json(self.tfidf_index_path, {})
    
    def save_metadata(self, file_id: str, metadata: Dict[str, Any]) -> bool:
        """Save file metadata."""
        try:
            file_path = os.path.join(self.metadata_path, f"{file_id}.json")
            self._save_json(file_path, metadata)
            return True
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False
    
    def get_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve file metadata."""
        try:
            file_path = os.path.join(self.metadata_path, f"{file_id}.json")
            return self._load_json(file_path)
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return None
    
    def save_analysis(self, file_id: str, analysis_type: str, analysis: Dict[str, Any]) -> bool:
        """Save analysis results for a file."""
        try:
            metadata = self.get_metadata(file_id)
            if not metadata:
                return False
            
            if "analysis" not in metadata:
                metadata["analysis"] = {}
            
            metadata["analysis"][analysis_type] = analysis
            metadata["last_analyzed"] = datetime.utcnow().isoformat()
            
            return self.save_metadata(file_id, metadata)
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return False
    
    def get_analysis(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis results for a file."""
        metadata = self.get_metadata(file_id)
        if metadata:
            return metadata.get("analysis", {})
        return None
    
    def save_schema(self, schema: Dict[str, Any]) -> str:
        """Save a schema and return its ID."""
        try:
            schema_id = str(uuid.uuid4())
            schema_data = {
                "id": schema_id,
                "schema": schema,
                "created_at": datetime.utcnow().isoformat()
            }
            
            file_path = os.path.join(self.schemas_path, f"{schema_id}.json")
            self._save_json(file_path, schema_data)
            
            return schema_id
        except Exception as e:
            print(f"Error saving schema: {e}")
            return ""
    
    def get_schema(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a schema by ID."""
        try:
            file_path = os.path.join(self.schemas_path, f"{schema_id}.json")
            return self._load_json(file_path)
        except Exception as e:
            print(f"Error loading schema: {e}")
            return None
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Retrieve all schemas."""
        schemas = []
        try:
            for filename in os.listdir(self.schemas_path):
                if filename.endswith(".json"):
                    file_path = os.path.join(self.schemas_path, filename)
                    schema = self._load_json(file_path)
                    if schema:
                        schemas.append(schema)
        except Exception as e:
            print(f"Error loading schemas: {e}")
        
        return schemas
    
    def get_all_files(self) -> List[Dict[str, Any]]:
        """Retrieve metadata for all files."""
        files = []
        try:
            for filename in os.listdir(self.metadata_path):
                if filename.endswith(".json"):
                    file_path = os.path.join(self.metadata_path, filename)
                    metadata = self._load_json(file_path)
                    if metadata:
                        files.append(metadata)
        except Exception as e:
            print(f"Error loading files: {e}")
        
        return files
    
    def update_phash_index(self, file_id: str, phash: Optional[str]) -> bool:
        """Update the perceptual hash index."""
        if not phash:
            return False
        
        try:
            index = self._load_json(self.phash_index_path) or {}
            index[file_id] = {
                "phash": phash,
                "updated_at": datetime.utcnow().isoformat()
            }
            self._save_json(self.phash_index_path, index)
            return True
        except Exception as e:
            print(f"Error updating phash index: {e}")
            return False
    
    def get_phash_index(self) -> Dict[str, Any]:
        """Retrieve the perceptual hash index."""
        return self._load_json(self.phash_index_path) or {}
    
    def update_tfidf_index(self, file_id: str, tfidf_data: Dict[str, Any]) -> bool:
        """Update the TF-IDF index."""
        try:
            index = self._load_json(self.tfidf_index_path) or {}
            index[file_id] = {
                "data": tfidf_data,
                "updated_at": datetime.utcnow().isoformat()
            }
            self._save_json(self.tfidf_index_path, index)
            return True
        except Exception as e:
            print(f"Error updating tfidf index: {e}")
            return False
    
    def get_tfidf_index(self) -> Dict[str, Any]:
        """Retrieve the TF-IDF index."""
        return self._load_json(self.tfidf_index_path) or {}
    
    def _save_json(self, file_path: str, data: Dict[str, Any]):
        """Save data to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load data from a JSON file."""
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
