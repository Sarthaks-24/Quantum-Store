"""
PDF Processor - Handles PDF analysis with OCR fallback
Uses PyMuPDF (fitz) for PDF operations and PaddleOCR for scanned documents
"""

import fitz  # PyMuPDF
from PIL import Image
import io
import os
from typing import Dict, Any, Optional
import base64

class PDFProcessor:
    def __init__(self):
        self.ocr_engine = None
        self._ocr_initialized = False
    
    def _init_ocr(self):
        """Lazy initialization of OCR engine (PaddleOCR is optional dependency)"""
        if not self._ocr_initialized:
            try:
                from paddleocr import PaddleOCR  # type: ignore[import-untyped]
                # Initialize with English language, use CPU
                self.ocr_engine = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, show_log=False)
                self._ocr_initialized = True
                print("[PDF] OCR engine initialized successfully")
            except Exception as e:
                print(f"[PDF] Warning: Could not initialize OCR: {e}")
                self.ocr_engine = None
                self._ocr_initialized = True
    
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a PDF file and extract metadata, text, and preview.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing PDF analysis results
        """
        print(f"[PDF] Starting analysis for: {file_path}")
        
        try:
            # Open PDF
            doc = fitz.open(file_path)
            page_count = len(doc)
            print(f"[PDF] Loaded PDF with {page_count} page(s)")
            
            # Extract metadata
            metadata = doc.metadata
            print(f"[PDF] Extracted metadata: {metadata}")
            
            # Extract text from all pages
            print("[PDF] Extracting text from pages...")
            extracted_text = ""
            has_text = False
            
            for page_num in range(page_count):
                page = doc[page_num]
                page_text = page.get_text()
                
                if page_text.strip():
                    has_text = True
                    extracted_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
            
            extracted_text = extracted_text.strip()
            
            # Check if PDF is scanned (no extractable text)
            is_scanned = not has_text
            ocr_text = ""
            
            # AUTOMATIC OCR: Trigger if text length < 30 chars
            if (is_scanned or len(extracted_text) < 30) and page_count > 0:
                print("[PDF] Minimal/no extractable text - triggering automatic OCR")
                print(f"[PDF] Extracted text length: {len(extracted_text)} chars (threshold: 30)")
                is_scanned = True
                ocr_text = self._extract_text_with_ocr(doc)
            
            # Combine extracted and OCR text
            final_text = extracted_text if extracted_text else ocr_text
            
            # Generate preview image from first page
            print("[PDF] Generating preview from first page...")
            preview_base64 = self._generate_preview(doc)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Analyze content for categorization (before closing doc)
            category_analysis = self._analyze_for_classification(doc, final_text, is_scanned)
            
            # Close document
            doc.close()
            
            print(f"[PDF] Analysis complete - Text length: {len(final_text)} chars, Is scanned: {is_scanned}")
            print(f"[PDF] Categories: {category_analysis.get('categories', {})}")
            
            return {
                "type": "pdf",
                "page_count": page_count,
                "metadata": {
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "subject": metadata.get("subject", ""),
                    "creator": metadata.get("creator", ""),
                    "producer": metadata.get("producer", ""),
                    "creation_date": metadata.get("creationDate", ""),
                    "modification_date": metadata.get("modDate", "")
                },
                "preview": preview_base64,
                "text": final_text,
                "text_length": len(final_text),
                "is_scanned": is_scanned,
                "has_ocr": bool(ocr_text),
                "has_forms": category_analysis.get('has_forms', False),
                "file_size": file_size,
                # Metrics for classifier
                "image_count": category_analysis.get('image_count', 0),
                "image_ratio": category_analysis.get('image_ratio', 0),
                "text_ratio": category_analysis.get('text_ratio', 0),
                "categories": category_analysis.get('categories', {}),
            }
            
        except Exception as e:
            print(f"[PDF] Error analyzing PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _generate_preview(self, doc: fitz.Document, page_num: int = 0, max_width: int = 400) -> str:
        """
        Generate a preview image from a PDF page.
        
        Args:
            doc: PyMuPDF document object
            page_num: Page number to render (0-indexed)
            max_width: Maximum width for preview image
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            if page_num >= len(doc):
                page_num = 0
            
            page = doc[page_num]
            
            # Calculate zoom to get desired width
            page_rect = page.rect
            zoom = max_width / page_rect.width
            
            # Render page to pixmap
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            preview_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            print(f"[PDF] Generated preview: {img.width}x{img.height} pixels")
            return preview_base64
            
        except Exception as e:
            print(f"[PDF] Error generating preview: {e}")
            return ""
    
    def _extract_text_with_ocr(self, doc: fitz.Document, max_pages: int = 10) -> str:
        """
        Extract text from scanned PDF using OCR.
        
        Args:
            doc: PyMuPDF document object
            max_pages: Maximum number of pages to OCR (to avoid excessive processing)
            
        Returns:
            Extracted text from OCR
        """
        # Initialize OCR if needed
        self._init_ocr()
        
        if not self.ocr_engine:
            print("[PDF] OCR engine not available, skipping OCR")
            return ""
        
        ocr_text = ""
        pages_to_process = min(len(doc), max_pages)
        
        print(f"[PDF] Running OCR on {pages_to_process} page(s)...")
        
        for page_num in range(pages_to_process):
            try:
                page = doc[page_num]
                
                # Render page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR accuracy
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Convert PIL Image to numpy array for PaddleOCR
                import numpy as np
                img_array = np.array(img)
                
                # Run OCR
                result = self.ocr_engine.ocr(img_array, cls=True)
                
                # Extract text from OCR result
                page_text = ""
                if result and result[0]:
                    for line in result[0]:
                        if line and len(line) > 1:
                            text = line[1][0]  # line[1] is (text, confidence)
                            page_text += text + " "
                
                if page_text.strip():
                    ocr_text += f"\n--- Page {page_num + 1} (OCR) ---\n{page_text.strip()}\n"
                    print(f"[PDF] OCR extracted {len(page_text)} chars from page {page_num + 1}")
                
            except Exception as e:
                print(f"[PDF] Error during OCR on page {page_num + 1}: {e}")
                continue
        
        return ocr_text.strip()
    
    def get_page_count(self, file_path: str) -> int:
        """Get the number of pages in a PDF"""
        try:
            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            print(f"[PDF] Error getting page count: {e}")
            return 0
    
    def extract_page_text(self, file_path: str, page_num: int = 0) -> str:
        """Extract text from a specific page"""
        try:
            doc = fitz.open(file_path)
            if page_num < len(doc):
                page = doc[page_num]
                text = page.get_text()
                doc.close()
                return text
            doc.close()
            return ""
        except Exception as e:
            print(f"[PDF] Error extracting page text: {e}")
            return ""
    
    def _analyze_for_classification(self, doc: fitz.Document, text: str, is_scanned: bool) -> Dict[str, Any]:
        """
        Analyze PDF content and provide metrics for the unified classifier.
        
        Returns metrics dict with:
        - image_count, image_ratio, text_ratio
        - categories: {financial: score, academic: score, report: score}
        - has_forms: bool
        """
        # Analyze document structure
        total_pages = len(doc)
        total_images = 0
        total_text_blocks = 0
        total_tables = 0
        has_forms = False
        
        # Sample first 10 pages for performance
        pages_to_sample = min(total_pages, 10)
        
        for page_num in range(pages_to_sample):
            try:
                page = doc[page_num]
                
                # Count images
                image_list = page.get_images()
                total_images += len(image_list)
                
                # Count text blocks
                blocks = page.get_text("blocks")
                text_blocks = [b for b in blocks if len(b) > 4 and b[4].strip()]
                total_text_blocks += len(text_blocks)
                
                # Detect tables (heuristic: many small blocks in grid)
                if len(blocks) > 15:
                    total_tables += 1
                
                # Check for form fields
                if page.first_widget:
                    has_forms = True
            except:
                pass
        
        # Calculate ratios
        total_elements = total_images + total_text_blocks
        image_ratio = total_images / total_elements if total_elements > 0 else 0
        text_ratio = total_text_blocks / total_elements if total_elements > 0 else 1.0
        
        # Keyword analysis
        text_lower = text.lower() if text else ""
        total_words = len(text_lower.split())
        
        # Financial indicators
        financial_keywords = [
            'revenue', 'profit', 'loss', 'balance', 'asset', 'liability',
            'income', 'expense', 'financial', 'fiscal', 'quarter', 'earnings',
            'shareholder', 'dividend', 'investment', 'budget'
        ]
        financial_count = sum(1 for kw in financial_keywords if kw in text_lower)
        financial_score = (financial_count / len(financial_keywords)) if financial_keywords else 0
        
        # Academic indicators
        academic_keywords = [
            'abstract', 'introduction', 'methodology', 'conclusion', 'references',
            'bibliography', 'citation', 'journal', 'university', 'research',
            'hypothesis', 'experiment', 'analysis', 'results', 'discussion'
        ]
        academic_count = sum(1 for kw in academic_keywords if kw in text_lower)
        academic_score = (academic_count / len(academic_keywords)) if academic_keywords else 0
        
        # Report indicators
        report_keywords = [
            'executive summary', 'table of contents', 'chapter', 'section',
            'appendix', 'overview', 'findings', 'recommendations', 'summary'
        ]
        report_count = sum(1 for kw in report_keywords if kw in text_lower)
        report_score = (report_count / len(report_keywords)) if report_keywords else 0
        
        return {
            'image_count': total_images,
            'image_ratio': image_ratio,
            'text_ratio': text_ratio,
            'has_forms': has_forms,
            'categories': {
                'financial': financial_score,
                'academic': academic_score,
                'report': report_score
            }
        }
