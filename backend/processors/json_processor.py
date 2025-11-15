import json
import re
import os
import sqlite3
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict, Counter
import statistics

try:
    import ijson
    IJSON_AVAILABLE = True
except ImportError:
    IJSON_AVAILABLE = False

class JSONProcessor:
    MAX_SAMPLE_SIZE = 50  # Maximum number of sample records to keep
    LARGE_FILE_THRESHOLD = 5 * 1024 * 1024  # 5MB
    MAX_METADATA_SIZE = 200 * 1024  # 200KB target for metadata
    
    def __init__(self):
        self.reasoning_log = []
    
    def analyze(self, file_path: str, file_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze JSON file with streaming for large files.
        Returns lightweight metadata suitable for storage.
        """
        self.reasoning_log = []
        
        if file_size is None:
            file_size = os.path.getsize(file_path)
        
        self.log_reasoning(f"Starting JSON analysis (file size: {file_size} bytes)")
        
        # Use streaming for large files
        use_streaming = file_size > self.LARGE_FILE_THRESHOLD
        
        if use_streaming and IJSON_AVAILABLE:
            self.log_reasoning("Using streaming parser for large file")
            return self._analyze_streaming(file_path, file_size)
        else:
            if use_streaming and not IJSON_AVAILABLE:
                self.log_reasoning("Warning: Large file but ijson not available, attempting regular parse")
            return self._analyze_regular(file_path)
    
    def _analyze_streaming(self, file_path: str, file_size: int) -> Dict[str, Any]:
        """Stream-parse large JSON files without loading entire content into memory."""
        try:
            with open(file_path, 'rb') as f:
                # Peek at structure
                parser = ijson.parse(f)
                first_event = next(parser, None)
                
                if first_event is None:
                    return {"error": "Empty JSON file"}
                
                # Reset file pointer
                f.seek(0)
                
                # Determine if it's an array or object
                if first_event[1] == 'start_array':
                    return self._stream_analyze_array(file_path, file_size)
                elif first_event[1] == 'start_map':
                    return self._stream_analyze_object(file_path)
                else:
                    return {"error": "JSON must be an object or array"}
                    
        except Exception as e:
            self.log_reasoning(f"Streaming parse failed: {str(e)}, falling back to regular parse")
            return self._analyze_regular(file_path)
    
    def _stream_analyze_array(self, file_path: str, file_size: int) -> Dict[str, Any]:
        """Stream-analyze JSON array, collecting only samples."""
        samples = []
        record_count = 0
        field_types = defaultdict(Counter)
        all_keys = set()
        
        self.log_reasoning("Streaming JSON array")
        
        try:
            with open(file_path, 'rb') as f:
                # Stream parse array items
                items = ijson.items(f, 'item')
                
                for item in items:
                    record_count += 1
                    
                    # Collect samples
                    if len(samples) < self.MAX_SAMPLE_SIZE:
                        # Only keep small sample records
                        if isinstance(item, dict):
                            # Store simplified version
                            simplified = self._simplify_record(item)
                            samples.append(simplified)
                    
                    # Analyze schema from this record
                    if isinstance(item, dict):
                        for key, value in item.items():
                            normalized_key = self._normalize_key(key)
                            all_keys.add((normalized_key, key))
                            field_types[normalized_key][self._infer_type(value)] += 1
                    
                    # Stop full iteration after collecting enough samples
                    if record_count >= 1000 and len(samples) >= self.MAX_SAMPLE_SIZE:
                        # Count remaining items
                        remaining = sum(1 for _ in items)
                        record_count += remaining
                        break
            
            self.log_reasoning(f"Detected JSON array with {record_count} items (sampled {len(samples)})")
            
            # Build schema from collected data
            schema = self._build_schema_from_types(all_keys, field_types, min(record_count, 1000))
            
            # Calculate statistics only from samples
            statistics_data = self._calculate_statistics_from_samples(samples, schema)
            
            # Detect inconsistencies from samples
            inconsistencies = self._detect_inconsistencies_from_samples(samples, schema)
            
            result = {
                "record_count": record_count,
                "sampled_count": len(samples),
                "schema": schema,
                "samples": samples[:self.MAX_SAMPLE_SIZE],  # Ensure limit
                "inconsistencies": inconsistencies,
                "statistics": statistics_data,
                "is_large_file": True,
                "reasoning_log": self.reasoning_log
            }
            
            return result
            
        except Exception as e:
            self.log_reasoning(f"Stream analysis error: {str(e)}")
            return {"error": f"Failed to stream parse JSON: {str(e)}"}
    
    def _stream_analyze_object(self, file_path: str) -> Dict[str, Any]:
        """Analyze single JSON object."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self._analyze_object(data)
            
        except Exception as e:
            return {"error": f"Failed to parse JSON object: {str(e)}"}
    
    def _analyze_regular(self, file_path: str) -> Dict[str, Any]:
        """Regular JSON analysis for small files."""
        self.log_reasoning("Using regular JSON parser")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return {"error": f"Failed to parse JSON: {str(e)}"}
        
        if isinstance(data, list):
            self.log_reasoning(f"Detected JSON array with {len(data)} items")
            return self._analyze_array(data)
        elif isinstance(data, dict):
            self.log_reasoning("Detected single JSON object")
            return self._analyze_object(data)
        else:
            return {"error": "JSON must be an object or array"}
    
    def _analyze_array(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze array but only keep samples in result."""
        if not data:
            return {
                "record_count": 0,
                "schema": {},
                "samples": [],
                "inconsistencies": [],
                "statistics": {},
                "reasoning_log": self.reasoning_log
            }
        
        # Build schema from ALL data
        schema = self._infer_schema(data)
        
        # But only keep sample records
        samples = self._extract_samples(data, self.MAX_SAMPLE_SIZE)
        
        # Calculate statistics from samples only
        statistics_data = self._calculate_statistics_from_samples(samples, schema)
        
        # Detect inconsistencies from samples
        inconsistencies = self._detect_inconsistencies_from_samples(samples, schema)
        
        return {
            "record_count": len(data),
            "sampled_count": len(samples),
            "schema": schema,
            "samples": samples,
            "inconsistencies": inconsistencies,
            "statistics": statistics_data,
            "is_large_file": False,
            "reasoning_log": self.reasoning_log
        }
    
    def _analyze_object(self, data: Dict) -> Dict[str, Any]:
        """Analyze single JSON object."""
        schema = {}
        for key, value in data.items():
            normalized_key = self._normalize_key(key)
            schema[normalized_key] = {
                "original_key": key,
                "type": self._infer_type(value),
                "confidence": 1.0,
                "presence": 1.0
            }
        
        # Store simplified version of object
        simplified_data = self._simplify_record(data)
        
        return {
            "record_count": 1,
            "schema": schema,
            "sample": simplified_data,
            "inconsistencies": [],
            "statistics": {},
            "reasoning_log": self.reasoning_log
        }
    
    def _simplify_record(self, record: Dict, max_depth: int = 2, current_depth: int = 0) -> Dict:
        """Simplify a record by truncating large nested structures."""
        if not isinstance(record, dict):
            return record
        
        if current_depth >= max_depth:
            return {"__truncated__": "nested structure"}
        
        simplified = {}
        for key, value in list(record.items())[:20]:  # Max 20 fields
            if isinstance(value, dict):
                simplified[key] = self._simplify_record(value, max_depth, current_depth + 1)
            elif isinstance(value, list):
                if len(value) > 5:
                    simplified[key] = value[:5] + [f"... {len(value) - 5} more items"]
                else:
                    simplified[key] = value
            elif isinstance(value, str) and len(value) > 200:
                simplified[key] = value[:200] + "..."
            else:
                simplified[key] = value
        
        if len(record) > 20:
            simplified["__truncated_fields__"] = len(record) - 20
        
        return simplified
    
    def _extract_samples(self, data: List[Dict], sample_size: int) -> List[Dict]:
        """Extract representative samples from array."""
        if len(data) <= sample_size:
            return [self._simplify_record(item) for item in data if isinstance(item, dict)]
        
        # Take samples from different parts of the array
        step = len(data) // sample_size
        samples = []
        for i in range(0, len(data), step):
            if len(samples) >= sample_size:
                break
            if isinstance(data[i], dict):
                samples.append(self._simplify_record(data[i]))
        
        return samples[:sample_size]
    
    def _normalize_key(self, key: str) -> str:
        """Normalize key to snake_case."""
        normalized = re.sub(r'[\s-]+', '_', key.lower())
        return normalized
    
    def _infer_type(self, value: Any) -> str:
        """Infer type of a value."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            if self._is_date(value):
                return "date"
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        return "unknown"
    
    def _is_date(self, value: str) -> bool:
        """Check if string looks like a date."""
        if not isinstance(value, str):
            return False
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        ]
        return any(re.match(pattern, value) for pattern in date_patterns)
    
    def _infer_schema(self, data: List[Dict]) -> Dict[str, Any]:
        """Infer unified schema from array of objects."""
        self.log_reasoning("Inferring unified schema from array of objects")
        
        field_types = defaultdict(Counter)
        all_keys = set()
        
        for record in data:
            if not isinstance(record, dict):
                continue
            for key, value in record.items():
                normalized_key = self._normalize_key(key)
                all_keys.add((normalized_key, key))
                field_types[normalized_key][self._infer_type(value)] += 1
        
        return self._build_schema_from_types(all_keys, field_types, len(data))
    
    def _build_schema_from_types(self, all_keys: set, field_types: Dict, total_records: int) -> Dict[str, Any]:
        """Build schema from collected type information."""
        schema = {}
        for normalized_key, original_key in all_keys:
            type_counts = field_types[normalized_key]
            total = sum(type_counts.values())
            most_common_type, count = type_counts.most_common(1)[0]
            confidence = count / total if total > 0 else 0
            
            schema[normalized_key] = {
                "original_keys": [k for n, k in all_keys if n == normalized_key],
                "type": most_common_type,
                "confidence": confidence,
                "type_distribution": dict(type_counts),
                "presence": total / total_records if total_records > 0 else 0
            }
            
            self.log_reasoning(
                f"Field '{normalized_key}': type={most_common_type}, "
                f"confidence={confidence:.2f}, presence={total}/{total_records}"
            )
        
        return schema
    
    def _calculate_statistics_from_samples(self, samples: List[Dict], schema: Dict) -> Dict:
        """Calculate statistics from sample records only."""
        stats = {}
        
        for normalized_key, field_info in schema.items():
            if field_info["type"] in ["int", "float"]:
                values = []
                for record in samples:
                    if not isinstance(record, dict):
                        continue
                    for key in record.keys():
                        if self._normalize_key(key) == normalized_key:
                            val = record[key]
                            if isinstance(val, (int, float)):
                                values.append(val)
                
                if values:
                    stats[normalized_key] = {
                        "min": min(values),
                        "max": max(values),
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "stddev": statistics.stdev(values) if len(values) > 1 else 0,
                        "sample_size": len(values)
                    }
        
        return stats
    
    def _detect_inconsistencies_from_samples(self, samples: List[Dict], schema: Dict) -> List[Dict]:
        """Detect inconsistencies from sample records."""
        self.log_reasoning("Detecting inconsistencies from samples")
        
        inconsistencies = []
        
        # Check for mixed types
        for normalized_key, field_info in schema.items():
            if field_info["confidence"] < 1.0:
                inconsistencies.append({
                    "field": normalized_key,
                    "type": "mixed_types",
                    "details": field_info["type_distribution"],
                    "severity": "medium"
                })
                self.log_reasoning(
                    f"Inconsistency: field '{normalized_key}' has mixed types: "
                    f"{field_info['type_distribution']}"
                )
        
        # Check for potential synonyms
        synonym_groups = self._detect_synonyms(schema)
        for group in synonym_groups:
            inconsistencies.append({
                "fields": group,
                "type": "potential_synonyms",
                "severity": "low"
            })
            self.log_reasoning(f"Potential synonym fields detected: {group}")
        
        return inconsistencies
    
    def _detect_synonyms(self, schema: Dict) -> List[List[str]]:
        """Detect potential synonym fields."""
        keys = list(schema.keys())
        synonym_groups = []
        
        for i, key1 in enumerate(keys):
            for key2 in keys[i+1:]:
                if self._are_synonyms(key1, key2):
                    synonym_groups.append([key1, key2])
        
        return synonym_groups
    
    def _are_synonyms(self, key1: str, key2: str) -> bool:
        """Check if two keys might be synonyms."""
        synonyms = [
            ("id", "identifier"),
            ("name", "title"),
            ("desc", "description"),
            ("img", "image"),
            ("pic", "picture"),
            ("created", "created_at"),
            ("updated", "updated_at")
        ]
        
        for syn1, syn2 in synonyms:
            if (syn1 in key1 and syn2 in key2) or (syn2 in key1 and syn1 in key2):
                return True
        return False
    
    def create_schema_database(self, file_id: str, schema: Dict, samples: List[Dict], 
                               db_path: str) -> bool:
        """
        Create SQLite database with schema and sample data.
        Only stores schema + samples, NOT full dataset.
        """
        try:
            self.log_reasoning(f"Creating schema database at {db_path}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Create database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Build CREATE TABLE statement from schema
            columns = []
            for norm_key, field_info in schema.items():
                sql_type = self._map_type_to_sql(field_info["type"])
                columns.append(f"{norm_key} {sql_type}")
            
            if not columns:
                self.log_reasoning("No columns in schema, skipping database creation")
                conn.close()
                return False
            
            # Add metadata column
            columns.append("_sample_id INTEGER PRIMARY KEY AUTOINCREMENT")
            
            create_table = f"CREATE TABLE IF NOT EXISTS data ({', '.join(columns)})"
            cursor.execute(create_table)
            
            # Insert sample records
            inserted = 0
            for sample in samples[:self.MAX_SAMPLE_SIZE]:
                if not isinstance(sample, dict):
                    continue
                
                # Build INSERT statement
                keys = []
                values = []
                for key, value in sample.items():
                    norm_key = self._normalize_key(key)
                    if norm_key in schema:
                        keys.append(norm_key)
                        # Convert complex types to JSON strings
                        if isinstance(value, (dict, list)):
                            values.append(json.dumps(value))
                        else:
                            values.append(value)
                
                if keys:
                    placeholders = ','.join(['?' for _ in values])
                    insert_sql = f"INSERT INTO data ({','.join(keys)}) VALUES ({placeholders})"
                    try:
                        cursor.execute(insert_sql, values)
                        inserted += 1
                    except sqlite3.Error as e:
                        self.log_reasoning(f"Error inserting sample: {str(e)}")
                        continue
            
            # Create metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS _metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            cursor.execute("INSERT OR REPLACE INTO _metadata VALUES (?, ?)", 
                          ("file_id", file_id))
            cursor.execute("INSERT OR REPLACE INTO _metadata VALUES (?, ?)", 
                          ("created_at", datetime.utcnow().isoformat()))
            cursor.execute("INSERT OR REPLACE INTO _metadata VALUES (?, ?)", 
                          ("sample_count", str(inserted)))
            cursor.execute("INSERT OR REPLACE INTO _metadata VALUES (?, ?)", 
                          ("schema", json.dumps(schema)))
            
            conn.commit()
            conn.close()
            
            self.log_reasoning(f"Successfully created schema database with {inserted} samples")
            return True
            
        except Exception as e:
            self.log_reasoning(f"Error creating schema database: {str(e)}")
            return False
    
    def _map_type_to_sql(self, json_type: str) -> str:
        """Map JSON type to SQL type."""
        mapping = {
            "int": "INTEGER",
            "float": "REAL",
            "bool": "INTEGER",
            "string": "TEXT",
            "date": "TEXT",
            "null": "TEXT",
            "array": "TEXT",
            "object": "TEXT",
            "unknown": "TEXT"
        }
        return mapping.get(json_type, "TEXT")
    
    def log_reasoning(self, message: str):
        """Add reasoning log entry."""
        timestamp = datetime.utcnow().isoformat()
        self.reasoning_log.append(f"[{timestamp}] {message}")
