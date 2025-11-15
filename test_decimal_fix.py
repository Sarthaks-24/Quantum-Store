"""
Test script to verify Decimal serialization fix
"""
import json
import sys
import os
from decimal import Decimal
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from utils.serializers import sanitize_for_json, CustomJSONEncoder

def test_sanitize_for_json():
    """Test the sanitize_for_json function"""
    print("="*60)
    print("Testing sanitize_for_json()")
    print("="*60)
    
    # Test cases
    test_cases = [
        {
            "name": "Decimal conversion",
            "input": Decimal('12.45'),
            "expected_type": float,
            "expected_value": 12.45
        },
        {
            "name": "numpy.int64 conversion",
            "input": np.int64(5),
            "expected_type": int,
            "expected_value": 5
        },
        {
            "name": "numpy.float32 conversion",
            "input": np.float32(1.23),
            "expected_type": float,
            "expected_value": 1.23
        },
        {
            "name": "Complex nested structure with Decimal",
            "input": {
                "stats": {
                    "mean": Decimal('45.67'),
                    "median": Decimal('44.0'),
                    "count": np.int64(100)
                },
                "values": [Decimal('1.1'), Decimal('2.2'), np.float64(3.3)]
            },
            "expected_type": dict,
            "expected_value": None  # Will check structure
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"  Input: {test['input']} (type: {type(test['input']).__name__})")
        
        try:
            result = sanitize_for_json(test['input'])
            print(f"  Output: {result} (type: {type(result).__name__})")
            
            # Check type
            if type(result) == test['expected_type']:
                print(f"  ✓ Type matches: {test['expected_type'].__name__}")
                
                # Check value for simple types
                if test['expected_value'] is not None:
                    if abs(result - test['expected_value']) < 0.0001:
                        print(f"  ✓ Value matches: {test['expected_value']}")
                        passed += 1
                    else:
                        print(f"  ✗ Value mismatch: expected {test['expected_value']}, got {result}")
                        failed += 1
                else:
                    # Complex structure - just verify it's serializable
                    try:
                        json_str = json.dumps(result)
                        print(f"  ✓ JSON serializable: {len(json_str)} bytes")
                        passed += 1
                    except Exception as e:
                        print(f"  ✗ JSON serialization failed: {e}")
                        failed += 1
            else:
                print(f"  ✗ Type mismatch: expected {test['expected_type'].__name__}, got {type(result).__name__}")
                failed += 1
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}\n")
    
    return failed == 0

def test_metadata_with_decimals():
    """Test realistic metadata with Decimal values"""
    print("="*60)
    print("Testing metadata with Decimal values")
    print("="*60)
    
    # Simulate metadata that might contain Decimals from statistics
    metadata = {
        "id": "test-123",
        "filename": "test.json",
        "analysis": {
            "json": {
                "record_count": 1000,
                "statistics": {
                    "age": {
                        "min": Decimal('18'),
                        "max": Decimal('65'),
                        "mean": Decimal('42.5'),
                        "median": Decimal('41.0'),
                        "stddev": Decimal('12.345')
                    },
                    "score": {
                        "min": np.float64(0.0),
                        "max": np.float64(100.0),
                        "mean": np.float64(75.5),
                        "count": np.int64(1000)
                    }
                }
            }
        }
    }
    
    print("\nOriginal metadata (with Decimal/numpy types):")
    print(f"  Type of age.mean: {type(metadata['analysis']['json']['statistics']['age']['mean'])}")
    print(f"  Type of score.count: {type(metadata['analysis']['json']['statistics']['score']['count'])}")
    
    # Sanitize
    sanitized = sanitize_for_json(metadata)
    
    print("\nSanitized metadata:")
    print(f"  Type of age.mean: {type(sanitized['analysis']['json']['statistics']['age']['mean'])}")
    print(f"  Type of score.count: {type(sanitized['analysis']['json']['statistics']['score']['count'])}")
    
    # Try to serialize to JSON
    try:
        json_str = json.dumps(sanitized, indent=2)
        print(f"\n✓ Successfully serialized to JSON ({len(json_str)} bytes)")
        
        # Try to parse it back
        parsed = json.loads(json_str)
        print(f"✓ Successfully parsed back from JSON")
        
        # Verify values
        age_mean = parsed['analysis']['json']['statistics']['age']['mean']
        if isinstance(age_mean, float) and abs(age_mean - 42.5) < 0.0001:
            print(f"✓ Value preserved: age.mean = {age_mean}")
        else:
            print(f"✗ Value not preserved correctly: {age_mean}")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n✗ JSON serialization failed: {e}")
        return False

def test_custom_encoder():
    """Test CustomJSONEncoder with Decimal values"""
    print("="*60)
    print("Testing CustomJSONEncoder")
    print("="*60)
    
    data = {
        "decimal_value": Decimal('99.99'),
        "numpy_int": np.int64(42),
        "numpy_float": np.float32(3.14),
        "list": [Decimal('1.1'), Decimal('2.2')],
        "nested": {
            "value": Decimal('100.0')
        }
    }
    
    try:
        json_str = json.dumps(data, cls=CustomJSONEncoder, indent=2)
        print(f"✓ Successfully serialized with CustomJSONEncoder ({len(json_str)} bytes)")
        
        parsed = json.loads(json_str)
        print(f"✓ Successfully parsed back")
        print(f"  decimal_value: {parsed['decimal_value']} (type: {type(parsed['decimal_value']).__name__})")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DECIMAL SERIALIZATION FIX - TEST SUITE")
    print("="*60 + "\n")
    
    test1 = test_sanitize_for_json()
    print()
    test2 = test_metadata_with_decimals()
    print()
    test3 = test_custom_encoder()
    
    print("\n" + "="*60)
    if test1 and test2 and test3:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60 + "\n")
