"""
Debug script to verify all fixes and identify crash points
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("="*60)
print("QUANTUM STORE - DEBUG VERIFICATION")
print("="*60)

# Test 1: Import checks
print("\n[TEST 1] Checking imports...")
try:
    from utils.serializers import sanitize_for_json, CustomJSONEncoder
    print("  ✓ sanitize_for_json imported")
    print("  ✓ CustomJSONEncoder imported")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

try:
    from storage.store import LocalStore
    print("  ✓ LocalStore imported")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

try:
    from processors.json_processor import JSONProcessor
    print("  ✓ JSONProcessor imported")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Sanitizer functionality
print("\n[TEST 2] Testing sanitizer...")
from decimal import Decimal
import numpy as np
import json

test_data = {
    "decimal": Decimal('42.5'),
    "numpy_int": np.int64(100),
    "numpy_float": np.float32(3.14),
    "nested": {
        "value": Decimal('99.99'),
        "list": [Decimal('1.1'), np.int64(5)]
    }
}

print("  Input types:")
print(f"    decimal: {type(test_data['decimal'])}")
print(f"    numpy_int: {type(test_data['numpy_int'])}")

sanitized = sanitize_for_json(test_data, _debug=True)

print("\n  Output types:")
print(f"    decimal: {type(sanitized['decimal'])}")
print(f"    numpy_int: {type(sanitized['numpy_int'])}")

try:
    json_str = json.dumps(sanitized)
    print(f"\n  ✓ Sanitized data is JSON-serializable ({len(json_str)} bytes)")
except Exception as e:
    print(f"  ✗ JSON serialization failed: {e}")
    sys.exit(1)

# Test 3: Storage path verification
print("\n[TEST 3] Checking storage paths...")
store = LocalStore()
print(f"  Base path: {store.base_path}")
print(f"  Metadata path: {store.metadata_path}")
print(f"  Schemas path: {store.schemas_path}")
print(f"  Uploads path: {store.uploads_path}")

# Check if directories exist
if os.path.exists(store.metadata_path):
    print(f"  ✓ Metadata directory exists")
else:
    print(f"  ℹ Metadata directory will be created on first use")

# Test 4: JSON Processor initialization
print("\n[TEST 4] Testing JSON Processor...")
processor = JSONProcessor()
print(f"  MAX_SAMPLE_SIZE: {processor.MAX_SAMPLE_SIZE}")
print(f"  LARGE_FILE_THRESHOLD: {processor.LARGE_FILE_THRESHOLD:,} bytes ({processor.LARGE_FILE_THRESHOLD / (1024*1024):.1f} MB)")
print(f"  MAX_METADATA_SIZE: {processor.MAX_METADATA_SIZE:,} bytes ({processor.MAX_METADATA_SIZE / 1024:.0f} KB)")

# Test 5: Check ijson availability
print("\n[TEST 5] Checking ijson availability...")
try:
    import ijson
    print("  ✓ ijson is installed")
    print(f"    Version: {ijson.__version__ if hasattr(ijson, '__version__') else 'unknown'}")
except ImportError:
    print("  ✗ ijson is NOT installed")
    print("    Install with: pip install ijson==3.3.0")

# Test 6: Create test JSON and analyze
print("\n[TEST 6] Creating and analyzing test JSON...")
test_json_file = "test_verify.json"
test_data = [
    {"id": i, "name": f"User {i}", "score": 50.0 + i, "age": 20 + i}
    for i in range(100)
]

with open(test_json_file, 'w') as f:
    json.dump(test_data, f)

file_size = os.path.getsize(test_json_file)
print(f"  Created test file: {file_size:,} bytes")

try:
    print("\n  Analyzing...")
    result = processor.analyze(test_json_file, file_size)
    print(f"  ✓ Analysis succeeded")
    print(f"    Record count: {result.get('record_count')}")
    print(f"    Schema fields: {len(result.get('schema', {}))}")
    print(f"    Has samples: {'samples' in result}")
    
    # Check result is serializable
    result_json = json.dumps(result)
    print(f"  ✓ Result is JSON-serializable ({len(result_json):,} bytes)")
    
    # Cleanup
    os.remove(test_json_file)
    print("  ✓ Test file cleaned up")
    
except Exception as e:
    print(f"  ✗ Analysis failed: {e}")
    import traceback
    traceback.print_exc()
    if os.path.exists(test_json_file):
        os.remove(test_json_file)
    sys.exit(1)

print("\n" + "="*60)
print("✓ ALL VERIFICATION TESTS PASSED")
print("="*60)
print("\nThe system is ready. Now test with actual API:")
print("1. Start the server: python backend/app.py")
print("2. Upload a JSON file")
print("3. Call /analyze/json with the file_id")
print("4. Watch the console for detailed debug output")
print("="*60)
