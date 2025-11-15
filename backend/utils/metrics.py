from typing import List, Dict, Any
import numpy as np

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)

def jaccard_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 1.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0

def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate Euclidean distance between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return float('inf')
    
    return sum((a - b) ** 2 for a, b in zip(vec1, vec2)) ** 0.5

def manhattan_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate Manhattan distance between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return float('inf')
    
    return sum(abs(a - b) for a, b in zip(vec1, vec2))

def normalize_vector(vec: List[float]) -> List[float]:
    """Normalize a vector to unit length."""
    magnitude = sum(x * x for x in vec) ** 0.5
    
    if magnitude == 0:
        return vec
    
    return [x / magnitude for x in vec]

def hamming_distance(str1: str, str2: str) -> int:
    """Calculate Hamming distance between two strings."""
    if len(str1) != len(str2):
        raise ValueError("Strings must be of equal length")
    
    return sum(c1 != c2 for c1, c2 in zip(str1, str2))

def calculate_percentile(values: List[float], percentile: float) -> float:
    """Calculate percentile of a list of values."""
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * (percentile / 100)
    
    if index.is_integer():
        return sorted_values[int(index)]
    else:
        lower = sorted_values[int(index)]
        upper = sorted_values[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))

def z_score(value: float, mean: float, stddev: float) -> float:
    """Calculate z-score for a value."""
    if stddev == 0:
        return 0.0
    
    return (value - mean) / stddev

def confidence_interval(values: List[float], confidence: float = 0.95) -> Dict[str, float]:
    """Calculate confidence interval for a list of values."""
    if not values:
        return {"lower": 0.0, "upper": 0.0, "mean": 0.0}
    
    mean = sum(values) / len(values)
    
    if len(values) < 2:
        return {"lower": mean, "upper": mean, "mean": mean}
    
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    stddev = variance ** 0.5
    
    z = 1.96 if confidence == 0.95 else 2.576
    margin = z * (stddev / (len(values) ** 0.5))
    
    return {
        "lower": mean - margin,
        "upper": mean + margin,
        "mean": mean
    }
