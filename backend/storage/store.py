import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import sys

# Add parent directory to path for imports
if __name__ != "__main__":
    from utils.serializers import sanitize_for_json
else:
    # For standalone execution
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils.serializers import sanitize_for_json

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
            print(f"[STORE] Saving metadata for file_id: {file_id}")
            file_path = os.path.join(self.metadata_path, f"{file_id}.json")
            print(f"[STORE] Metadata path: {file_path}")
            
            # Check metadata size before saving
            import json
            metadata_json = json.dumps(metadata)
            metadata_size = len(metadata_json.encode('utf-8'))
            print(f"[STORE] Metadata size: {metadata_size:,} bytes ({metadata_size / 1024:.2f} KB)")
            
            if metadata_size > 500 * 1024:  # Warn if > 500KB
                print(f"[STORE] WARNING: Large metadata size ({metadata_size / 1024:.0f} KB)")
            
            self._save_json(file_path, metadata)
            print(f"[STORE] ✓ Metadata saved successfully")
            return True
        except Exception as e:
            print(f"[STORE] ERROR saving metadata: {e}")
            import traceback
            traceback.print_exc()
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
        """Save data to a JSON file with sanitization."""
        print(f"[STORE._save_json] Saving to: {file_path}")
        print(f"[STORE._save_json] Sanitizing data...")
        
        # Sanitize data to ensure all types are JSON-serializable
        sanitized_data = sanitize_for_json(data)
        print(f"[STORE._save_json] ✓ Data sanitized")
        
        print(f"[STORE._save_json] Writing JSON...")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sanitized_data, f, indent=2, ensure_ascii=False)
        
        file_size = os.path.getsize(file_path)
        print(f"[STORE._save_json] ✓ File written: {file_size:,} bytes")
    
    def _load_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load data from a JSON file."""
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
