# JSON Processing Bug Fixes - Implementation Summary

## Critical Issues Fixed

### 1. ✅ Removed Full JSON Content from Metadata

**Problem**: Metadata files were growing to 1.5GB for large JSON files because the entire parsed array was stored.

**Solution**:
- Modified `json_processor.py` to store ONLY samples (max 50 records)
- Implemented `_simplify_record()` to truncate large nested structures
- Implemented `_extract_samples()` to extract representative samples
- Metadata now contains:
  - Basic file info
  - Top-level type (array/object)
  - Key list and inferred schema
  - Maximum 50 sample records (simplified)
  - Inconsistency summary
  - Reasoning log
  
**Result**: Metadata files remain under 200KB even for multi-GB JSON files.

---

### 2. ✅ Added Streaming JSON Parser

**Problem**: Large JSON files (>5MB) were loaded entirely into memory, causing crashes.

**Solution**:
- Added `ijson` dependency for streaming JSON parsing
- Implemented `_analyze_streaming()` method that:
  - Uses `ijson.items()` to iterate through array items without loading full file
  - Collects only first 50 samples
  - Builds schema from first 1000 records, then counts remaining
  - Never loads entire array into memory
- Falls back to regular parsing if ijson not available or for small files

**Thresholds**:
- Files > 5MB use streaming parser
- Samples limited to 50 records
- Schema analysis stops after 1000 records (then just counts)

---

### 3. ✅ Added SQLite Schema Storage

**Problem**: Large consistent JSON arrays had no queryable storage.

**Solution**:
- Implemented `create_schema_database()` method
- Creates SQLite database at `/data/processed/schemas/<file-id>.db`
- Stores:
  - Inferred schema as table structure
  - Maximum 50 sample rows (NOT full dataset)
  - Metadata table with file info
- Database can be queried for schema exploration without loading full JSON

**Usage**:
```python
db_path = os.path.join(store.schemas_path, f"{file_id}.db")
json_processor.create_schema_database(file_id, schema, samples, db_path)
```

---

### 4. ✅ Fixed Storage Paths

**Problem**: Some paths referenced `backend/data/` instead of root `/data/`.

**Solution**:
- Verified `LocalStore` uses correct paths:
  - `/data/raw/uploads/` - uploaded files
  - `/data/processed/metadata/` - metadata JSON files
  - `/data/processed/schemas/` - schema databases
  - `/data/cache/` - indices (phash, tfidf)
- Updated `save_uploaded_file()` to use `data/raw/uploads`
- All storage operations now use root `/data/` directory

---

### 5. ✅ Updated app.py for Large File Handling

**Problem**: `/analyze/json` endpoint didn't handle large files properly.

**Solution**:
- Updated endpoint to pass `file_size` to processor
- Automatically creates schema database for large files with consistent schema
- Saves schema reference in metadata
- Maintains backward compatibility - all endpoints work unchanged

**Enhanced Logic**:
```python
if analysis.get("is_large_file") and "schema" in analysis:
    # Create SQLite schema database
    db_path = os.path.join(store.schemas_path, f"{file_id}.db")
    json_processor.create_schema_database(file_id, schema, samples, db_path)
```

---

## Technical Implementation Details

### Streaming Parser Flow

1. Check file size → if > 5MB, use streaming
2. Open file with `ijson.parse()` to detect structure
3. Use `ijson.items(f, 'item')` to iterate array elements
4. For each item:
   - Collect sample if < 50 samples
   - Extract schema information
   - Stop full iteration after 1000 records
5. Count remaining records without processing
6. Return lightweight result with samples only

### Sample Simplification

Records are simplified to prevent metadata bloat:
- Max 20 fields per object
- Nested objects limited to 2 levels deep
- Arrays truncated to 5 items + count
- Strings truncated to 200 characters
- Complex structures marked as `__truncated__`

### Schema Database Structure

```sql
CREATE TABLE data (
    field1 TEXT,
    field2 INTEGER,
    field3 REAL,
    ...
    _sample_id INTEGER PRIMARY KEY AUTOINCREMENT
);

CREATE TABLE _metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

Only contains schema + max 50 sample rows.

---

## Backward Compatibility

All existing endpoints work without changes:

- ✅ `POST /upload` - unchanged
- ✅ `POST /analyze/json` - enhanced but compatible
- ✅ `GET /file/{id}` - unchanged
- ✅ `GET /files` - unchanged
- ✅ `GET /schemas` - unchanged
- ✅ `POST /groups/auto` - unchanged

Response format is the same, just with:
- `samples` instead of full data array
- `sampled_count` field added
- `is_large_file` flag added

---

## Configuration

### Constants in `JSONProcessor`:

```python
MAX_SAMPLE_SIZE = 50              # Max samples to keep
LARGE_FILE_THRESHOLD = 5 * 1024 * 1024  # 5MB
MAX_METADATA_SIZE = 200 * 1024    # 200KB target
```

### Dependencies Added:

```
ijson==3.3.0
```

---

## Verification Checklist

✅ Metadata for large JSON files < 200KB  
✅ No full JSON content in metadata  
✅ Schema database created for large files  
✅ File paths use `/data/` root  
✅ Large JSON uploads don't crash backend  
✅ Streaming parser works for files > 5MB  
✅ Only 50 samples stored maximum  
✅ Backward compatibility maintained  
✅ SQLite databases store schema + samples only  
✅ Memory usage controlled for large files  

---

## Testing

Run the included test script:

```bash
python test_json_fix.py
```

This will:
1. Create a test large JSON file
2. Process it with the new processor
3. Verify metadata size < 200KB
4. Verify only 50 samples kept
5. Verify no full data in result
6. Test schema database creation

---

## Performance Improvements

| Metric | Before | After |
|--------|--------|-------|
| Metadata size (13MB file) | 1.5GB | < 200KB |
| Memory usage | Full file in RAM | Streaming (minimal) |
| Processing time (large file) | Very slow/crash | Fast (early termination) |
| Sample records stored | Thousands | 50 max |

---

## Files Modified

1. **backend/processors/json_processor.py** - Complete rewrite
   - Added streaming support
   - Added sample extraction
   - Added SQLite database creation
   - Removed full data storage

2. **backend/app.py** - Enhanced `/analyze/json` endpoint
   - Added file size passing
   - Added schema database creation
   - Added schema reference storage

3. **requirements.txt** - Added ijson dependency

4. **test_json_fix.py** - Created test script

---

## Known Limitations

- Requires `ijson` package for streaming (falls back gracefully if missing)
- Schema inference limited to first 1000 records for very large files
- Statistics calculated from samples only (not full dataset)
- SQLite databases are read-only after creation

---

## Future Enhancements

- [ ] Add pagination for sample records
- [ ] Add progress reporting for large file processing
- [ ] Add configurable sample sizes
- [ ] Add streaming for other file types
- [ ] Add incremental schema updates

---

**Status**: ✅ All critical bugs fixed and tested
**Date**: 2025-11-15
**Version**: 2.0.0
