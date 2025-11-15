"""
Test script to verify JSON processor fixes
"""
import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from processors.json_processor import JSONProcessor

def create_test_json(filename, size_mb=15):
    """Create a test JSON file with many records"""
    print(f"Creating test JSON file: {filename}")
    
    # Create a sample record
    sample_record = {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com",
        "age": 25,
        "city": "New York",
        "country": "USA",
        "created_at": "2025-01-01T00:00:00Z",
        "is_active": True,
        "score": 95.5,
        "tags": ["tag1", "tag2", "tag3"],
        "metadata": {
            "source": "api",
            "version": "1.0"
        }
    }
    
    # Calculate how many records we need
    record_json = json.dumps(sample_record)
    record_size = len(record_json.encode('utf-8'))
    target_size = size_mb * 1024 * 1024
    num_records = target_size // record_size
    
    print(f"Generating {num_records} records...")
    
    # Create array of records
    records = []
    for i in range(num_records):
        record = sample_record.copy()
        record["id"] = i + 1
        record["name"] = f"User {i + 1}"
        record["email"] = f"user{i + 1}@example.com"
        record["age"] = 20 + (i % 50)
        record["score"] = 50 + (i % 50)
        records.append(record)
    
    # Write to file
    with open(filename, 'w') as f:
        json.dump(records, f)
    
    file_size = os.path.getsize(filename)
    print(f"Created file: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    return file_size

def test_json_processor():
    """Test the JSON processor with large file"""
    print("\n" + "="*60)
    print("TESTING JSON PROCESSOR")
    print("="*60 + "\n")
    
    # Create test file
    test_file = "test_large.json"
    file_size = create_test_json(test_file, size_mb=0.5)  # Start with 0.5MB
    
    # Initialize processor
    processor = JSONProcessor()
    
    print("\nAnalyzing JSON file...")
    print("-" * 60)
    
    # Analyze
    result = processor.analyze(test_file, file_size)
    
    # Check results
    print("\nResults:")
    print(f"  Record count: {result.get('record_count', 0)}")
    print(f"  Sampled count: {result.get('sampled_count', 0)}")
    print(f"  Is large file: {result.get('is_large_file', False)}")
    print(f"  Schema fields: {len(result.get('schema', {}))}")
    print(f"  Samples in result: {len(result.get('samples', []))}")
    
    # Calculate metadata size
    metadata_json = json.dumps(result)
    metadata_size = len(metadata_json.encode('utf-8'))
    print(f"\nMetadata size: {metadata_size:,} bytes ({metadata_size / 1024:.2f} KB)")
    
    # Check if metadata is under limit
    max_size = processor.MAX_METADATA_SIZE
    if metadata_size < max_size:
        print(f"✓ PASS: Metadata is under {max_size / 1024:.0f}KB limit")
    else:
        print(f"✗ FAIL: Metadata exceeds {max_size / 1024:.0f}KB limit")
    
    # Check samples limit
    samples_count = len(result.get('samples', []))
    if samples_count <= processor.MAX_SAMPLE_SIZE:
        print(f"✓ PASS: Samples count ({samples_count}) is within limit ({processor.MAX_SAMPLE_SIZE})")
    else:
        print(f"✗ FAIL: Too many samples ({samples_count})")
    
    # Check no full data in result
    if 'data' not in result and 'full_array' not in result:
        print("✓ PASS: No full data array in result")
    else:
        print("✗ FAIL: Full data array found in result")
    
    # Test schema database creation
    if result.get('is_large_file') and 'schema' in result:
        print("\nTesting schema database creation...")
        db_path = "test_schema.db"
        success = processor.create_schema_database(
            "test-file-id",
            result['schema'],
            result.get('samples', []),
            db_path
        )
        
        if success and os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            print(f"✓ PASS: Schema database created ({db_size:,} bytes)")
            os.remove(db_path)
        else:
            print("✗ FAIL: Schema database not created")
    
    # Cleanup
    os.remove(test_file)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_json_processor()
