import json
from datetime import datetime, date
from typing import Any
from decimal import Decimal
import numpy as np

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling special types."""
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, set):
            return list(obj)
        
        return super().default(obj)

def serialize_to_json(data: Any) -> str:
    """Serialize data to JSON string with custom encoder."""
    return json.dumps(data, cls=CustomJSONEncoder, indent=2, ensure_ascii=False)

def safe_serialize(obj: Any) -> Any:
    """Safely serialize an object for JSON."""
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: safe_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [safe_serialize(item) for item in obj]
    else:
        return str(obj)

def sanitize_for_json(data: Any, _debug: bool = False, _path: str = "root") -> Any:
    """
    Universal sanitizer that converts all non-JSON-serializable types.
    
    Handles:
    - Decimal -> float
    - numpy types -> Python primitives
    - datetime/date -> ISO string
    - Recursively sanitizes dicts/lists/tuples
    
    This ensures no Decimal or numpy types reach JSON serialization.
    """
    if data is None or isinstance(data, (bool, str)):
        # Handle these first since bool is a subclass of int
        return data
    elif isinstance(data, Decimal):
        if _debug:
            print(f"[SANITIZER] {_path}: Decimal({data}) -> float({float(data)})")
        return float(data)
    elif isinstance(data, (int, float)):
        # Regular Python int/float
        return data
    elif isinstance(data, np.integer):
        if _debug:
            print(f"[SANITIZER] {_path}: np.{type(data).__name__}({data}) -> int({int(data)})")
        return int(data)
    elif isinstance(data, np.floating):
        if _debug:
            print(f"[SANITIZER] {_path}: np.{type(data).__name__}({data}) -> float({float(data)})")
        return float(data)
    elif isinstance(data, np.ndarray):
        if _debug:
            print(f"[SANITIZER] {_path}: Converting numpy array")
        return [sanitize_for_json(item, _debug, f"{_path}[{i}]") for i, item in enumerate(data.tolist())]
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: sanitize_for_json(value, _debug, f"{_path}.{key}") for key, value in data.items()}
    elif isinstance(data, (list, tuple)):
        return [sanitize_for_json(item, _debug, f"{_path}[{i}]") for i, item in enumerate(data)]
    elif isinstance(data, set):
        return [sanitize_for_json(item, _debug, f"{_path}.set[{i}]") for i, item in enumerate(sorted(data))]
    elif isinstance(data, bytes):
        try:
            return data.decode('utf-8')
        except:
            return str(data)
    else:
        # Fallback for unknown types
        if _debug:
            print(f"[SANITIZER] {_path}: Unknown type {type(data).__name__} -> str")
        return str(data)

