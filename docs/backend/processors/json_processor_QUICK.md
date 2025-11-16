# JSON Processor - Quick Reference

## What It Does
Analyzes JSON files and extracts structure, even for huge files (100MB+)

## Main Function
```python
processor = JSONProcessor()
result = processor.analyze(file_path)
```

## Smart Features

### 1. **Streaming for Large Files**
- File > 5MB? → Uses `ijson` library (streaming parser)
- File < 5MB? → Loads entire JSON normally
- **Why?** Large JSONs (100MB) would crash if loaded into memory

### 2. **Sampling (Not Loading Everything)**
```python
MAX_SAMPLE_SIZE = 50  # Only keep 50 records
```
- If JSON has 10,000 records → Only analyzes first 50 deeply
- Saves **200KB** instead of **10MB** metadata
- **Why?** You don't need all 10,000 records to understand structure

### 3. **Schema Auto-Detection**
Automatically figures out data types:
```json
{
  "user_id": {"type": "int", "nullable": false},
  "name": {"type": "string", "nullable": true},
  "age": {"type": "int", "nullable": true}
}
```

## Output Example
```json
{
  "record_count": 10000,
  "sampled_count": 50,
  "schema": {
    "user_id": {"type": "int", "nullable": false},
    "username": {"type": "string", "nullable": false},
    "email": {"type": "string", "nullable": true}
  },
  "samples": [
    {"user_id": 1, "username": "alice", "email": "alice@example.com"},
    {"user_id": 2, "username": "bob", "email": null}
  ],
  "statistics": {
    "user_id": {"min": 1, "max": 10000, "avg": 5000.5}
  },
  "inconsistencies": [
    {"field": "email", "issue": "25% null values"}
  ]
}
```

## How It Works

### For Arrays
```python
# 1. Open file with streaming
items = ijson.items(file, 'item')

# 2. Process first 1000 records
for i, item in enumerate(items):
    if i < 50:
        samples.append(item)  # Save sample
    
    # Analyze schema from all 1000
    if i < 1000:
        detect_types(item)
    else:
        break  # Stop after 1000

# 3. Count remaining
record_count = i + sum(1 for _ in items)
```

### For Objects
```python
# Just load the entire object (single record)
with open(file_path) as f:
    data = json.load(f)
```

## Type Detection
```python
def _infer_type(value):
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        # Try to detect date format
        if re.match(r'^\d{4}-\d{2}-\d{2}', value):
            return "date"
        return "string"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
```

## Classification Hints
Provides data for classifier to determine category:
```python
{
  "has_nested_objects": True,
  "avg_nesting_depth": 3.2,
  "has_array_values": True,
  "field_count": 15,
  "suggested_category": "json_nested"
}
```

**Categories:**
- `json_flat_structured` - Simple {"key": "value"}
- `json_nested` - Deep objects with 3+ levels
- `json_array_of_objects` - Database-like [{}, {}, {}]
- `json_semistructured` - Mixed types
- `json_invalid` - Malformed JSON

## Performance

| File Size | Method | Time |
|-----------|--------|------|
| 100KB | Regular | 10ms |
| 5MB | Regular | 200ms |
| 10MB | Streaming | 500ms |
| 100MB | Streaming | 3s |

**Memory:**
- Regular: Loads entire file (100MB JSON = 200MB RAM)
- Streaming: Only 50 samples (100MB JSON = 2MB RAM)

## Key Methods

### `analyze(file_path)`
Main entry point, chooses streaming or regular

### `_analyze_streaming(file_path)`
For large files (>5MB), uses ijson

### `_stream_analyze_array(file_path)`
Processes JSON arrays with sampling

### `_build_schema_from_types(keys, field_types, record_count)`
Builds schema from collected type info

### `_calculate_statistics_from_samples(samples, schema)`
Computes min/max/avg from samples only

### `_detect_inconsistencies_from_samples(samples, schema)`
Finds type mismatches, nulls, etc.

## Example Usage in Backend

```python
# In app.py
@app.post("/analyze/json")
async def analyze_json_endpoint(file_id: str):
    metadata = store.get_metadata(file_id)
    file_path = metadata["file_path"]
    
    # Analyze JSON
    analysis = json_processor.analyze(file_path)
    
    # Classify
    category = classifier.classify_file(
        file_path, 
        "json", 
        {"json": analysis}
    )
    
    # Save
    store.save_metadata(file_id, {...})
```

## Limitations
1. **Only first 50 samples saved** (not all records)
2. **Only first 1000 records analyzed** for schema (large files)
3. **No deep validation** (just type inference)
4. **No JSON Path queries** (can't extract specific fields)
5. **Streaming requires ijson library** (optional dependency)

## Quiz Tips
- **Large file threshold:** 5MB
- **Sample size:** 50 records max
- **Analysis depth:** 1000 records max
- **Memory savings:** 100× less for large files
- **Output categories:** 5 types (flat, nested, array, semi, invalid)
