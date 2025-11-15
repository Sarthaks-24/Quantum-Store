import json
import re
from typing import Any, Dict, List, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import statistics

class JSONProcessor:
    def __init__(self):
        self.reasoning_log = []
    
    def analyze(self, file_path: str) -> Dict[str, Any]:
        self.reasoning_log = []
        
        self.log_reasoning("Starting JSON analysis")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return {"error": f"Failed to parse JSON: {str(e)}"}
        
        if isinstance(data, list):
            self.log_reasoning(f"Detected JSON array with {len(data)} items")
            results = self._analyze_array(data)
        elif isinstance(data, dict):
            self.log_reasoning("Detected single JSON object")
            results = self._analyze_object(data)
        else:
            return {"error": "JSON must be an object or array"}
        
        results["reasoning_log"] = self.reasoning_log
        return results
    
    def _analyze_array(self, data: List[Dict]) -> Dict[str, Any]:
        if not data:
            return {"schema": {}, "inconsistencies": [], "statistics": {}}
        
        schema = self._infer_schema(data)
        inconsistencies = self._detect_inconsistencies(data, schema)
        statistics_data = self._calculate_statistics(data, schema)
        outliers = self._detect_outliers(data, schema)
        
        return {
            "record_count": len(data),
            "schema": schema,
            "inconsistencies": inconsistencies,
            "statistics": statistics_data,
            "outliers": outliers
        }
    
    def _analyze_object(self, data: Dict) -> Dict[str, Any]:
        schema = {}
        for key, value in data.items():
            normalized_key = self._normalize_key(key)
            schema[normalized_key] = {
                "original_key": key,
                "type": self._infer_type(value),
                "confidence": 1.0
            }
        
        return {
            "record_count": 1,
            "schema": schema,
            "inconsistencies": [],
            "statistics": {}
        }
    
    def _normalize_key(self, key: str) -> str:
        normalized = re.sub(r'[\s-]+', '_', key.lower())
        self.log_reasoning(f"Normalized key '{key}' to '{normalized}'")
        return normalized
    
    def _infer_type(self, value: Any) -> str:
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
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        ]
        return any(re.match(pattern, value) for pattern in date_patterns)
    
    def _infer_schema(self, data: List[Dict]) -> Dict[str, Any]:
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
                "presence": total / len(data)
            }
            
            self.log_reasoning(
                f"Field '{normalized_key}': type={most_common_type}, "
                f"confidence={confidence:.2f}, presence={total}/{len(data)}"
            )
        
        return schema
    
    def _detect_inconsistencies(self, data: List[Dict], schema: Dict) -> List[Dict]:
        self.log_reasoning("Detecting inconsistencies in data")
        
        inconsistencies = []
        
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
        
        synonym_groups = self._detect_synonyms(schema)
        for group in synonym_groups:
            inconsistencies.append({
                "fields": group,
                "type": "potential_synonyms",
                "severity": "low"
            })
            self.log_reasoning(f"Potential synonym fields detected: {group}")
        
        for idx, record in enumerate(data):
            if not isinstance(record, dict):
                continue
            for normalized_key, field_info in schema.items():
                if normalized_key not in [self._normalize_key(k) for k in record.keys()]:
                    if field_info["presence"] > 0.5:
                        inconsistencies.append({
                            "record_index": idx,
                            "field": normalized_key,
                            "type": "missing_field",
                            "severity": "high"
                        })
        
        return inconsistencies
    
    def _detect_synonyms(self, schema: Dict) -> List[List[str]]:
        keys = list(schema.keys())
        synonym_groups = []
        
        for i, key1 in enumerate(keys):
            for key2 in keys[i+1:]:
                if self._are_synonyms(key1, key2):
                    synonym_groups.append([key1, key2])
        
        return synonym_groups
    
    def _are_synonyms(self, key1: str, key2: str) -> bool:
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
    
    def _calculate_statistics(self, data: List[Dict], schema: Dict) -> Dict:
        stats = {}
        
        for normalized_key, field_info in schema.items():
            if field_info["type"] in ["int", "float"]:
                values = []
                for record in data:
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
                        "stddev": statistics.stdev(values) if len(values) > 1 else 0
                    }
        
        return stats
    
    def _detect_outliers(self, data: List[Dict], schema: Dict) -> Dict:
        outliers = {}
        
        for normalized_key, field_info in schema.items():
            if field_info["type"] in ["int", "float"]:
                values = []
                for record in data:
                    if not isinstance(record, dict):
                        continue
                    for key in record.keys():
                        if self._normalize_key(key) == normalized_key:
                            val = record[key]
                            if isinstance(val, (int, float)):
                                values.append(val)
                
                if len(values) >= 4:
                    q1 = statistics.quantiles(values, n=4)[0]
                    q3 = statistics.quantiles(values, n=4)[2]
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    outlier_values = [v for v in values if v < lower_bound or v > upper_bound]
                    
                    if outlier_values:
                        outliers[normalized_key] = {
                            "count": len(outlier_values),
                            "values": outlier_values,
                            "bounds": {"lower": lower_bound, "upper": upper_bound}
                        }
                        self.log_reasoning(
                            f"Detected {len(outlier_values)} outliers in field '{normalized_key}'"
                        )
        
        return outliers
    
    def log_reasoning(self, message: str):
        timestamp = datetime.utcnow().isoformat()
        self.reasoning_log.append(f"[{timestamp}] {message}")
