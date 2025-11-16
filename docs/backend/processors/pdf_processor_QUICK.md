# PDF Processor - Quick Reference

## What It Does
Extracts text from PDFs + runs OCR for scanned documents

## Main Function
```python
processor = PDFProcessor()
result = processor.analyze(file_path)
```

## Key Feature: **Auto OCR**
```python
# If extracted text < 30 chars → Trigger OCR
if len(extracted_text) < 30:
    ocr_text = self._extract_text_with_ocr(doc)
```

**Why?** Scanned PDFs have images of text, not actual text. Need OCR.

## Libraries Used
- **PyMuPDF (fitz):** Open PDFs, extract text, render pages
- **PaddleOCR:** Optical Character Recognition (reads text from images)
- **PIL (Pillow):** Image manipulation

## Output Example
```json
{
  "type": "pdf",
  "page_count": 5,
  "metadata": {
    "title": "Report 2024",
    "author": "John Doe",
    "creation_date": "D:20240115103000"
  },
  "text": "Full extracted text from all pages...",
  "text_length": 5420,
  "is_scanned": false,
  "has_ocr": false,
  "has_forms": false,
  "preview": "data:image/png;base64,iVBOR...",
  "image_count": 3,
  "image_ratio": 0.15,
  "text_ratio": 0.85
}
```

## How It Works

### Step 1: Open PDF
```python
doc = fitz.open(file_path)
page_count = len(doc)  # Number of pages
```

### Step 2: Extract Text
```python
extracted_text = ""
for page_num in range(page_count):
    page = doc[page_num]
    page_text = page.get_text()
    extracted_text += page_text
```

### Step 3: Check if Scanned
```python
has_text = len(extracted_text.strip()) > 0
is_scanned = not has_text or len(extracted_text) < 30
```

**Logic:**
- No text? → Scanned
- Text < 30 chars? → Probably scanned (just headers/footers)

### Step 4: OCR (If Needed)
```python
def _extract_text_with_ocr(self, doc):
    # Initialize OCR engine (lazy load)
    if not self._ocr_initialized:
        from paddleocr import PaddleOCR
        self.ocr_engine = PaddleOCR(lang='en', use_gpu=False)
    
    ocr_text = ""
    for page_num in range(min(5, len(doc))):  # Max 5 pages
        page = doc[page_num]
        
        # Render page as image
        pix = page.get_pixmap(dpi=150)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Run OCR
        result = self.ocr_engine.ocr(np.array(img), cls=True)
        
        # Extract text
        for line in result:
            for word_info in line:
                text = word_info[1][0]
                ocr_text += text + " "
    
    return ocr_text
```

**Performance:**
- OCR is **slow**: 2-5 seconds per page
- Only processes **first 5 pages** to save time

### Step 5: Generate Preview
```python
def _generate_preview(self, doc, page_num=0, max_width=400):
    page = doc[page_num]
    
    # Calculate zoom to get 400px width
    zoom = max_width / page.rect.width
    
    # Render page as image
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    # Convert to PNG
    img_data = pix.tobytes("png")
    
    # Encode as base64
    return base64.b64encode(img_data).decode('utf-8')
```

### Step 6: Analyze for Classification
```python
def _analyze_for_classification(self, doc, text, is_scanned):
    # Count images
    image_count = 0
    for page in doc:
        image_count += len(page.get_images())
    
    # Check for forms
    has_forms = any(page.first_annot for page in doc)
    
    # Calculate ratios
    file_size = doc.xref_length  # Rough estimate
    text_ratio = min(len(text) / max(file_size, 1), 1.0)
    image_ratio = image_count / max(len(doc), 1)
    
    return {
        "image_count": image_count,
        "image_ratio": image_ratio,
        "text_ratio": text_ratio,
        "has_forms": has_forms
    }
```

## Classification Hints

The processor provides data for classifier:

```python
{
  "is_scanned": True,        # Was OCR used?
  "image_count": 5,          # Number of images
  "image_ratio": 0.5,        # Images per page
  "text_ratio": 0.8,         # Text vs file size
  "has_forms": True,         # Has form fields?
  "page_count": 10
}
```

**Classifier uses this to decide category:**
- `is_scanned=True` → `pdfs_scanned`
- `has_forms=True` → `pdfs_form`
- `image_ratio > 0.3` → `pdfs_with_images`
- `page_count > 100, text_ratio > 0.8` → `pdfs_ebook`
- etc.

## Categories (9 types)
- `pdfs_text_document` - Normal text PDFs
- `pdfs_scanned` - Scanned paper (OCR used)
- `pdfs_form` - Forms with fields
- `pdfs_with_images` - PDFs with photos
- `pdfs_with_tables` - Spreadsheet-like
- `pdfs_ebook` - Books (many pages)
- `pdfs_presentation` - Slides
- `pdfs_slides` - Presentation slides
- `pdfs_receipt` - Small receipts

## Performance

| PDF Type | Pages | Time |
|----------|-------|------|
| Text PDF | 5 | 200ms |
| Text PDF | 50 | 1s |
| Scanned | 1 | 3s (OCR) |
| Scanned | 5 | 12s (OCR) |

**Bottleneck:** OCR (2-5s per page)

**Optimization:** Only OCR first 5 pages

## Example Usage

```python
# In app.py
@app.post("/analyze/pdf")
async def analyze_pdf_endpoint(file_id: str):
    metadata = store.get_metadata(file_id)
    file_path = metadata["file_path"]
    
    # Analyze PDF
    analysis = pdf_processor.analyze(file_path)
    
    # Classify
    category = classifier.classify_file(
        file_path, 
        "pdf", 
        {"pdf": analysis}
    )
    
    # Save
    store.save_metadata(file_id, {..., "analysis": {"pdf": analysis}})
```

## Limitations
1. **OCR only first 5 pages** (not entire 100-page PDF)
2. **OCR requires PaddleOCR** (optional dependency, 500MB download)
3. **OCR accuracy ~90%** (not perfect)
4. **No table extraction** (just raw text)
5. **No form data extraction** (just detects presence)
6. **Preview from page 1 only** (not all pages)

## Quiz Tips
- **OCR trigger threshold:** < 30 characters
- **OCR library:** PaddleOCR
- **PDF library:** PyMuPDF (fitz)
- **Preview resolution:** 400px width
- **OCR page limit:** 5 pages max
- **Auto OCR:** Yes, if text < 30 chars
- **Output categories:** 9 types
