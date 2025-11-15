"""
Test script for advanced classifier
"""
from backend.classifier import classify_file

print("=" * 70)
print("ADVANCED CLASSIFIER TESTS")
print("=" * 70)

# Test 1: Screenshot
print("\n1. Screenshot Detection (1920x1080 PNG without EXIF)")
result = classify_file(
    {'filename': 'screenshot.png', 'size': 500000},
    {'width': 1920, 'height': 1080, 'has_exif': False, 'quality': {'sharpness': 75}}
)
print(f"   Category: {result['category']}")
print(f"   Subcategories: {result['subcategories']}")
print(f"   Confidence: {result['confidence']:.2f}")

# Test 2: Flat structured JSON
print("\n2. JSON Flat Structured (SQL-ready)")
result = classify_file(
    {'filename': 'data.json', 'size': 10000},
    {'shape': 'array_of_objects', 'field_consistency': 0.98, 'max_depth': 1, 
     'nested_ratio': 0.1, 'schema': {}}
)
print(f"   Category: {result['category']}")
print(f"   Subcategories: {result['subcategories']}")
print(f"   Confidence: {result['confidence']:.2f}")

# Test 3: Scanned PDF
print("\n3. PDF Scanned Document")
result = classify_file(
    {'filename': 'scan.pdf', 'size': 5000000},
    {'is_scanned': True, 'has_forms': False, 'page_count': 10, 'image_ratio': 0.9}
)
print(f"   Category: {result['category']}")
print(f"   Subcategories: {result['subcategories']}")
print(f"   Confidence: {result['confidence']:.2f}")

# Test 4: WhatsApp voice note
print("\n4. Audio - WhatsApp Voice Note")
result = classify_file(
    {'filename': 'voice.opus', 'size': 50000},
    {'duration_seconds': 45}
)
print(f"   Category: {result['category']}")
print(f"   Subcategories: {result['subcategories']}")
print(f"   Confidence: {result['confidence']:.2f}")

# Test 5: Portrait video (mobile)
print("\n5. Video - Portrait (Mobile)")
result = classify_file(
    {'filename': 'clip.mp4', 'size': 20000000},
    {'width': 720, 'height': 1280, 'duration_seconds': 30, 'fps': 30}
)
print(f"   Category: {result['category']}")
print(f"   Subcategories: {result['subcategories']}")
print(f"   Confidence: {result['confidence']:.2f}")

# Test 6: AI-generated image
print("\n6. Image - AI Generated (1024x1024 PNG, no EXIF)")
result = classify_file(
    {'filename': 'ai_art.png', 'size': 800000},
    {'width': 1024, 'height': 1024, 'has_exif': False, 'has_alpha': True}
)
print(f"   Category: {result['category']}")
print(f"   Subcategories: {result['subcategories']}")
print(f"   Confidence: {result['confidence']:.2f}")

# Test 7: PDF Receipt
print("\n7. PDF - Receipt")
result = classify_file(
    {'filename': 'receipt.pdf', 'size': 100000},
    {'page_count': 1, 'text_length': 800, 'text_content': 'Total: $45.99 Tax: $3.50 Subtotal: $42.49 Receipt Transaction'}
)
print(f"   Category: {result['category']}")
print(f"   Subcategories: {result['subcategories']}")
print(f"   Confidence: {result['confidence']:.2f}")

# Test 8: Meme
print("\n8. Image - Meme (Square JPEG, no EXIF)")
result = classify_file(
    {'filename': 'meme.jpg', 'size': 150000},
    {'width': 800, 'height': 800, 'has_exif': False, 'has_alpha': False}
)
print(f"   Category: {result['category']}")
print(f"   Subcategories: {result['subcategories']}")
print(f"   Confidence: {result['confidence']:.2f}")

# Test 9: Podcast
print("\n9. Audio - Podcast (long MP3)")
result = classify_file(
    {'filename': 'podcast.mp3', 'size': 45000000},
    {'duration_seconds': 3600}  # 1 hour
)
print(f"   Category: {result['category']}")
print(f"   Subcategories: {result['subcategories']}")
print(f"   Confidence: {result['confidence']:.2f}")

# Test 10: Screen recording
print("\n10. Video - Screen Recording (1920x1080, 30fps)")
result = classify_file(
    {'filename': 'screenrec.mp4', 'size': 150000000},
    {'width': 1920, 'height': 1080, 'fps': 30, 'duration_seconds': 300}
)
print(f"   Category: {result['category']}")
print(f"   Subcategories: {result['subcategories']}")
print(f"   Confidence: {result['confidence']:.2f}")

# Test 11: Fallback (unknown extension)
print("\n11. Fallback - Unknown Extension")
result = classify_file(
    {'filename': 'data.xyz', 'size': 1000},
    None
)
print(f"   Category: {result['category']}")
print(f"   Subcategories: {result['subcategories']}")
print(f"   Confidence: {result['confidence']:.2f}")

print("\n" + "=" * 70)
print("ALL TESTS COMPLETED!")
print("=" * 70)
