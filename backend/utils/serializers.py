import json
from datetime import datetime, date
from typing import Any
import numpy as np

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling special types."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
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
