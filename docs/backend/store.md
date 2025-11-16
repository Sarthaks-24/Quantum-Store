# store.py - LocalStore JSON Storage System

**Location**: `backend/storage/store.py`  
**Lines**: 392  
**Type**: Storage Layer (JSON-based)

---

## Overview

The **LocalStore** class provides a JSON-based file storage system for QuantumStore. It manages metadata, analysis results, schemas, category groups, and cache indices using a hierarchical directory structure with JSON files.

**Design Philosophy**: Local-first, file-based storage with no database dependencies. Every file's metadata is a standalone JSON file indexed by UUID.

---

## Responsibilities

1. **Metadata Management**
   - Save/load file metadata (filename, type, size, timestamps, path)
   - Update metadata with classification and analysis results

2. **Analysis Storage**
   - Save type-specific analysis results within metadata
   - Retrieve analysis by file ID

3. **Schema Management**
   - Save JSON schemas with UUID
   - Retrieve schemas by ID
   - List all schemas

4. **Category Grouping**
   - Add files to category groups (indexed)
   - Retrieve files by category
   - Rebuild groups from metadata
   - List all groups with summaries

5. **Cache Indices**
   - Maintain phash index for image similarity
   - Maintain TF-IDF index for text similarity

6. **File Listing**
   - Get all files with metadata
   - Filter files by type/category

---

## Directory Structure

```
data/                           # Base path (configurable)
├── processed/
│   ├── metadata/              # File metadata (one JSON per file)
│   │   ├── uuid1.json
│   │   ├── uuid2.json
│   │   └── ...
│   ├── schemas/               # JSON schemas
│   │   ├── schema_uuid1.json
│   │   └── ...
│   └── groups/                # Category groups (index files)
│       ├── pdf_scanned.json
│       ├── image_screenshot.json
│       └── ...
├── cache/                     # Similarity indices
│   ├── phash_index.json      # Image perceptual hashes
│   └── tfidf_index.json      # Text TF-IDF vectors
└── raw/
    └── uploads/               # Original uploaded files
        ├── uuid1_filename.pdf
        ├── uuid2_image.jpg
        └── ...
```

---

## Initialization

### `__init__(base_path: str = None)`
```python
def __init__(self, base_path: str = None):
    if base_path is None:
        # Default: project_root/data
        storage_dir = os.path.dirname(os.path.abspath(__file__))  # backend/storage
        backend_dir = os.path.dirname(storage_dir)  # backend
        root_dir = os.path.dirname(backend_dir)  # project root
        base_path = os.path.join(root_dir, "data")
    
    self.base_path = base_path
    self.metadata_path = os.path.join(base_path, "processed", "metadata")
    self.schemas_path = os.path.join(base_path, "processed", "schemas")
    self.groups_path = os.path.join(base_path, "processed", "groups")
    self.cache_path = os.path.join(base_path, "cache")
    self.uploads_path = os.path.join(base_path, "raw", "uploads")
    
    self._ensure_directories()
    self._init_indices()
```

**Auto-detection**: Resolves base_path relative to `store.py` location  
**Custom path**: Can be overridden for testing or alternate storage

---

### `_ensure_directories()`
```python
def _ensure_directories(self):
    os.makedirs(self.metadata_path, exist_ok=True)
    os.makedirs(self.schemas_path, exist_ok=True)
    os.makedirs(self.groups_path, exist_ok=True)
    os.makedirs(self.cache_path, exist_ok=True)
    os.makedirs(self.uploads_path, exist_ok=True)
```

**Purpose**: Create directory structure if missing  
**When**: Every LocalStore initialization (idempotent)

---

### `_init_indices()`
```python
def _init_indices(self):
    self.phash_index_path = os.path.join(self.cache_path, "phash_index.json")
    self.tfidf_index_path = os.path.join(self.cache_path, "tfidf_index.json")
    
    if not os.path.exists(self.phash_index_path):
        self._save_json(self.phash_index_path, {})
    
    if not os.path.exists(self.tfidf_index_path):
        self._save_json(self.tfidf_index_path, {})
```

**Purpose**: Initialize empty index files if they don't exist

---

## Metadata Operations

### `save_metadata(file_id: str, metadata: Dict[str, Any]) -> bool`
```python
def save_metadata(self, file_id: str, metadata: Dict[str, Any]) -> bool:
    try:
        print(f"[STORE] Saving metadata for file_id: {file_id}")
        file_path = os.path.join(self.metadata_path, f"{file_id}.json")
        
        # Check metadata size
        metadata_json = json.dumps(metadata)
        metadata_size = len(metadata_json.encode('utf-8'))
        print(f"[STORE] Metadata size: {metadata_size:,} bytes ({metadata_size / 1024:.2f} KB)")
        
        if metadata_size > 500 * 1024:  # Warn if > 500KB
            print(f"[STORE] WARNING: Large metadata size ({metadata_size / 1024:.0f} KB)")
        
        self._save_json(file_path, metadata)
        print(f"[STORE] OK Metadata saved successfully")
        return True
    except Exception as e:
        print(f"[STORE] ERROR saving metadata: {e}")
        traceback.print_exc()
        return False
```

**File Path**: `data/processed/metadata/{file_id}.json`  
**Size Warning**: Logs warning if metadata > 500KB (unusually large)  
**Error Handling**: Returns `False` on failure (doesn't raise exception)

**Example Metadata**:
```json
{
  "id": "a4fea9d9-79d8-4a86-b9bf-9a3f2e9d00e9",
  "filename": "report.pdf",
  "file_type": "pdf",
  "mime_type": "application/pdf",
  "size": 1024000,
  "uploaded_at": "2024-11-15T10:30:00.123456",
  "path": "data/raw/uploads/a4fea9d9_report.pdf",
  "classification": {
    "type": "pdf",
    "category": "pdf_scanned",
    "subcategories": ["pdf_ocr", "pdf_form"],
    "confidence": 0.87
  },
  "category": "pdf_scanned",
  "subcategories": ["pdf_ocr", "pdf_form"],
  "confidence": 0.87,
  "analysis": {
    "pdf": {
      "text": "Extracted text...",
      "page_count": 10,
      "is_scanned": true,
      "preview": "base64_encoded_image"
    }
  },
  "last_analyzed": "2024-11-15T10:30:05.789"
}
```

---

### `get_metadata(file_id: str) -> Optional[Dict[str, Any]]`
```python
def get_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
    try:
        file_path = os.path.join(self.metadata_path, f"{file_id}.json")
        return self._load_json(file_path)
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return None
```

**Returns**: Metadata dict or `None` if not found  
**Error Handling**: Logs error and returns None (doesn't raise)

---

### `get_all_files() -> List[Dict[str, Any]]`
```python
def get_all_files(self) -> List[Dict[str, Any]]:
    files = []
    try:
        for filename in os.listdir(self.metadata_path):
            if filename.endswith(".json"):
                file_path = os.path.join(self.metadata_path, filename)
                metadata = self._load_json(file_path)
                if metadata:
                    files.append(metadata)
    except Exception as e:
        print(f"Error getting all files: {e}")
    return files
```

**Complexity**: O(n) where n = number of files  
**Performance**: 10-100ms for <1000 files  
**Note**: Reads all metadata files from disk (no caching)

---

## Analysis Operations

### `save_analysis(file_id: str, analysis_type: str, analysis: Dict[str, Any]) -> bool`
```python
def save_analysis(self, file_id: str, analysis_type: str, analysis: Dict[str, Any]) -> bool:
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
```

**Pattern**: Analysis stored within metadata under `analysis[type]` key  
**Example**:
```json
{
  "id": "uuid",
  "analysis": {
    "pdf": { ... },
    "image": { ... }
  }
}
```

**Multi-Type Support**: Same file can have multiple analysis types (e.g., PDF with image analysis of pages)

---

### `get_analysis(file_id: str) -> Optional[Dict[str, Any]]`
```python
def get_analysis(self, file_id: str) -> Optional[Dict[str, Any]]:
    metadata = self.get_metadata(file_id)
    if metadata:
        return metadata.get("analysis", {})
    return None
```

**Returns**: All analysis results for file, or empty dict if none

---

## Schema Operations

### `save_schema(schema: Dict[str, Any]) -> str`
```python
def save_schema(self, schema: Dict[str, Any]) -> str:
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
```

**Returns**: Schema UUID or empty string on failure  
**Use Case**: Store JSON schemas for SQL-suitable files

---

### `get_schema(schema_id: str) -> Optional[Dict[str, Any]]`
```python
def get_schema(self, schema_id: str) -> Optional[Dict[str, Any]]:
    try:
        file_path = os.path.join(self.schemas_path, f"{schema_id}.json")
        return self._load_json(file_path)
    except Exception as e:
        print(f"Error loading schema: {e}")
        return None
```

---

### `get_all_schemas() -> List[Dict[str, Any]]`
```python
def get_all_schemas(self) -> List[Dict[str, Any]]:
    schemas = []
    try:
        for filename in os.listdir(self.schemas_path):
            if filename.endswith(".json"):
                file_path = os.path.join(self.schemas_path, filename)
                schema = self._load_json(file_path)
                if schema:
                    schemas.append(schema)
    except Exception as e:
        print(f"Error getting all schemas: {e}")
    return schemas
```

---

## Category Grouping

### `add_file_to_group(file_id: str, category: str) -> bool`
```python
def add_file_to_group(self, file_id: str, category: str) -> bool:
    try:
        group_path = os.path.join(self.groups_path, f"{category}.json")
        
        # Load existing group or create new
        if os.path.exists(group_path):
            group_data = self._load_json(group_path)
            files = group_data.get("files", [])
        else:
            files = []
        
        # Add file if not already in group
        if file_id not in files:
            files.append(file_id)
            
            group_data = {
                "category": category,
                "files": files,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self._save_json(group_path, group_data)
        
        return True
    except Exception as e:
        print(f"Error adding file to group: {e}")
        return False
```

**Idempotent**: Adding same file multiple times has no effect  
**Group File**: `data/processed/groups/{category}.json`

**Example Group**:
```json
{
  "category": "pdf_scanned",
  "files": ["uuid1", "uuid2", "uuid3"],
  "updated_at": "2024-11-15T10:35:00.456"
}
```

---

### `get_group_files(category: str) -> List[str]`
```python
def get_group_files(self, category: str) -> List[str]:
    try:
        group_path = os.path.join(self.groups_path, f"{category}.json")
        if os.path.exists(group_path):
            group_data = self._load_json(group_path)
            return group_data.get("files", [])
    except Exception as e:
        print(f"Error getting group files: {e}")
    return []
```

**Returns**: List of file IDs in category  
**Empty List**: If category doesn't exist or error

---

### `get_all_groups() -> Dict[str, List[str]]`
```python
def get_all_groups(self) -> Dict[str, List[str]]:
    groups = {}
    try:
        for filename in os.listdir(self.groups_path):
            if filename.endswith(".json"):
                category = filename.replace(".json", "")
                files = self.get_group_files(category)
                groups[category] = files
    except Exception as e:
        print(f"Error getting all groups: {e}")
    return groups
```

**Returns**: `{ "category1": ["uuid1", "uuid2"], "category2": [...] }`

---

### `rebuild_groups() -> bool`
```python
def rebuild_groups(self) -> bool:
    try:
        # Clear existing groups
        for filename in os.listdir(self.groups_path):
            if filename.endswith(".json"):
                os.remove(os.path.join(self.groups_path, filename))
        
        # Rebuild from metadata
        files = self.get_all_files()
        for file_data in files:
            category = file_data.get("category")
            if category:
                self.add_file_to_group(file_data["id"], category)
        
        return True
    except Exception as e:
        print(f"Error rebuilding groups: {e}")
        return False
```

**Purpose**: Rebuild all group indices from metadata  
**Use Case**: After manual metadata edits or corruption recovery

---

## Cache Index Operations

### `update_phash_index(file_id: str, phash: str) -> bool`
```python
def update_phash_index(self, file_id: str, phash: str) -> bool:
    try:
        index = self._load_json(self.phash_index_path) or {}
        index[file_id] = phash
        self._save_json(self.phash_index_path, index)
        return True
    except Exception as e:
        print(f"Error updating phash index: {e}")
        return False
```

**Index Structure**: `{ "file_uuid": "phash_hex_string" }`  
**Purpose**: Fast image similarity lookups

---

### `get_phash_index() -> Dict[str, str]`
```python
def get_phash_index(self) -> Dict[str, str]:
    try:
        return self._load_json(self.phash_index_path) or {}
    except Exception as e:
        print(f"Error getting phash index: {e}")
        return {}
```

---

### `update_tfidf_index(file_id: str, vector: List[float]) -> bool`
```python
def update_tfidf_index(self, file_id: str, vector: List[float]) -> bool:
    try:
        index = self._load_json(self.tfidf_index_path) or {}
        index[file_id] = vector
        self._save_json(self.tfidf_index_path, index)
        return True
    except Exception as e:
        print(f"Error updating tfidf index: {e}")
        return False
```

**Index Structure**: `{ "file_uuid": [0.1, 0.3, 0.0, ...] }`  
**Purpose**: Fast text similarity computations

---

## Utility Functions

### `_save_json(file_path: str, data: Any) -> None`
```python
def _save_json(self, file_path: str, data: Any):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

**Format**: Pretty-printed JSON (indent=2)  
**Encoding**: UTF-8 with non-ASCII support

---

### `_load_json(file_path: str) -> Optional[Any]`
```python
def _load_json(self, file_path: str) -> Optional[Any]:
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

**Returns**: Parsed JSON or None if file doesn't exist

---

## Known Limitations

1. **No Atomic Writes**
   - Metadata updates not atomic (risk of partial writes)
   - **Enhancement**: Use temp file + rename pattern

2. **No File Locking**
   - Concurrent writes to same file can corrupt data
   - **Issue**: Multiple processes modifying same metadata
   - **Enhancement**: Add file locking (e.g., `fcntl` on Unix)

3. **No Transactions**
   - Multi-file operations (e.g., rebuild_groups) not atomic
   - **Enhancement**: Add transaction log or rollback mechanism

4. **Linear Search**
   - `get_all_files()` reads all metadata (O(n))
   - **Performance**: Slow for >10,000 files
   - **Enhancement**: Add SQLite index or in-memory cache

5. **No Compression**
   - JSON files stored uncompressed
   - **Enhancement**: Use gzip for large metadata/analysis

6. **No Backup**
   - No automatic backup of metadata
   - **Enhancement**: Add versioning (e.g., keep last N versions)

7. **Group Index Can Drift**
   - If metadata category changes but group not updated
   - **Mitigation**: Call `rebuild_groups()` periodically

---

## How to Modify or Extend

### Add File Deletion
```python
def delete_file(self, file_id: str) -> bool:
    try:
        # Delete metadata
        metadata_path = os.path.join(self.metadata_path, f"{file_id}.json")
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
        
        # Remove from all groups
        for category_file in os.listdir(self.groups_path):
            if category_file.endswith(".json"):
                group_path = os.path.join(self.groups_path, category_file)
                group_data = self._load_json(group_path)
                if group_data and file_id in group_data.get("files", []):
                    group_data["files"].remove(file_id)
                    self._save_json(group_path, group_data)
        
        # Remove from indices
        phash_index = self.get_phash_index()
        if file_id in phash_index:
            del phash_index[file_id]
            self._save_json(self.phash_index_path, phash_index)
        
        return True
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False
```

---

### Add Atomic Writes
```python
import tempfile
import shutil

def _save_json_atomic(self, file_path: str, data: Any):
    # Write to temp file first
    temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path))
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename (POSIX) or move (Windows)
        shutil.move(temp_path, file_path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e
```

---

### Add In-Memory Cache
```python
class LocalStore:
    def __init__(self, base_path: str = None):
        # ... existing init ...
        self._metadata_cache = {}  # {file_id: metadata}
        self._cache_enabled = True
    
    def get_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        if self._cache_enabled and file_id in self._metadata_cache:
            return self._metadata_cache[file_id]
        
        metadata = self._load_metadata_from_disk(file_id)
        if metadata and self._cache_enabled:
            self._metadata_cache[file_id] = metadata
        
        return metadata
    
    def save_metadata(self, file_id: str, metadata: Dict[str, Any]) -> bool:
        success = self._save_metadata_to_disk(file_id, metadata)
        if success and self._cache_enabled:
            self._metadata_cache[file_id] = metadata
        return success
```

---

## Testing Considerations

```python
import unittest
import tempfile
import shutil

class TestLocalStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = LocalStore(base_path=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_metadata(self):
        metadata = {
            "id": "test-uuid",
            "filename": "test.pdf",
            "file_type": "pdf"
        }
        
        self.assertTrue(self.store.save_metadata("test-uuid", metadata))
        loaded = self.store.get_metadata("test-uuid")
        
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["filename"], "test.pdf")
```

---

**Last Updated**: November 2024  
**Storage Type**: JSON-based (no database)  
**Status**: ✅ Production-ready  
**Performance**: Suitable for <10,000 files
