from typing import Dict, Any, List
import math

class Heuristics:
    
    @staticmethod
    def detect_anomaly(value: float, mean: float, stddev: float, threshold: float = 3.0) -> bool:
        """Detect if a value is an anomaly using standard deviation."""
        if stddev == 0:
            return False
        z_score = abs((value - mean) / stddev)
        return z_score > threshold
    
    @staticmethod
    def calculate_entropy(values: List[Any]) -> float:
        """Calculate Shannon entropy of a list of values."""
        if not values:
            return 0.0
        
        from collections import Counter
        counts = Counter(values)
        total = len(values)
        
        entropy = 0.0
        for count in counts.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    @staticmethod
    def fuzzy_match(str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Fuzzy string matching using normalized edit distance."""
        if not str1 or not str2:
            return False
        
        str1_lower = str1.lower()
        str2_lower = str2.lower()
        
        if str1_lower == str2_lower:
            return True
        
        distance = Heuristics._edit_distance(str1_lower, str2_lower)
        max_len = max(len(str1_lower), len(str2_lower))
        
        similarity = 1 - (distance / max_len) if max_len > 0 else 0
        
        return similarity >= threshold
    
    @staticmethod
    def _edit_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance."""
        if len(s1) < len(s2):
            return Heuristics._edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def infer_data_quality(record: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Infer data quality metrics for a record."""
        completeness = 0.0
        consistency = 0.0
        
        if schema:
            expected_fields = len(schema)
            present_fields = sum(1 for key in schema.keys() if key in record)
            completeness = present_fields / expected_fields if expected_fields > 0 else 0
            
            type_matches = 0
            for field, field_info in schema.items():
                if field in record:
                    expected_type = field_info.get("type")
                    actual_value = record[field]
                    if Heuristics._matches_type(actual_value, expected_type):
                        type_matches += 1
            
            consistency = type_matches / expected_fields if expected_fields > 0 else 0
        
        return {
            "completeness": completeness,
            "consistency": consistency,
            "quality_score": (completeness + consistency) / 2
        }
    
    @staticmethod
    def _matches_type(value: Any, expected_type: str) -> bool:
        """Check if a value matches an expected type."""
        if expected_type == "null":
            return value is None
        elif expected_type == "bool":
            return isinstance(value, bool)
        elif expected_type == "int":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == "float":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        return False
    
    @staticmethod
    def calculate_diversity(values: List[Any]) -> float:
        """Calculate diversity of values (0 = all same, 1 = all unique)."""
        if not values:
            return 0.0
        
        unique_count = len(set(str(v) for v in values))
        total_count = len(values)
        
        return unique_count / total_count if total_count > 0 else 0
    
    @staticmethod
    def detect_pattern(text: str) -> Dict[str, Any]:
        """Detect common patterns in text."""
        import re
        
        patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "url": r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "date": r'\b\d{4}-\d{2}-\d{2}\b',
            "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "credit_card": r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
        }
        
        detected = {}
        for pattern_name, pattern_regex in patterns.items():
            matches = re.findall(pattern_regex, text)
            if matches:
                detected[pattern_name] = {
                    "count": len(matches),
                    "examples": matches[:3]
                }
        
        return detected
