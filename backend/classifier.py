"""
QuantumStore Advanced Multi-Level Classification System
========================================================

COMPLETELY REWRITTEN - Advanced categorization for ALL file types.

Classification Output:
{
    "type": "image" | "json" | "pdf" | "audio" | "video" | "text" | "binary",
    "category": "image_screenshot" | "json_flat_structured" | "pdf_scanned" | etc.,
    "subcategories": ["image_jpeg", "image_landscape"],  # Multiple tags
    "confidence": 0.87,  # 0.0 - 1.0
}

Features:
- 15+ image categories (screenshot, scanned_doc, photo, meme, AI-gen, etc.)
- 5 JSON categories (flat_structured, nested, unstructured, etc.)
- 9 PDF categories (text_doc, scanned, form, tables, slides, etc.)
- 5 audio categories (music, voice_note, podcast, etc.)
- 5 video categories (youtube, screen_recording, portrait, etc.)
- Fallback: Extension-based grouping (.md_group, .mp3_group, etc.)
"""

import os
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path


# ============================================================================
# EXTENSION TO TYPE MAPPING
# ============================================================================

EXTENSION_TYPE_MAP = {
    # PDF
    '.pdf': 'pdf',
    
    # Data
    '.json': 'json',
    '.jsonl': 'json',
    '.csv': 'text',
    '.tsv': 'text',
    '.xml': 'text',
    
    # Documents
    '.txt': 'text',
    '.md': 'text',
    '.rtf': 'text',
    '.doc': 'binary',
    '.docx': 'binary',
    
    # Images
    '.jpg': 'image',
    '.jpeg': 'image',
    '.png': 'image',
    '.gif': 'image',
    '.bmp': 'image',
    '.svg': 'image',
    '.webp': 'image',
    '.tiff': 'image',
    '.tif': 'image',
    
    # Audio
    '.mp3': 'audio',
    '.m4a': 'audio',
    '.wav': 'audio',
    '.flac': 'audio',
    '.aac': 'audio',
    '.ogg': 'audio',
    '.opus': 'audio',
    '.wma': 'audio',
    
    # Video
    '.mp4': 'video',
    '.mov': 'video',
    '.avi': 'video',
    '.mkv': 'video',
    '.wmv': 'video',
    '.flv': 'video',
    '.webm': 'video',
    '.m4v': 'video',
    
    # Code
    '.py': 'text',
    '.js': 'text',
    '.ts': 'text',
    '.html': 'text',
    '.css': 'text',
    
    # Archives
    '.zip': 'binary',
    '.tar': 'binary',
    '.gz': 'binary',
    '.rar': 'binary',
    '.7z': 'binary',
}


class AdvancedClassifier:
    """
    Advanced multi-level classification system.
    Single entry point: classify_file()
    """
    
    def classify_file(
        self,
        metadata: Dict[str, Any],
        preview: Optional[Dict[str, Any]] = None,
        full_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        MASTER CLASSIFICATION FUNCTION.
        
        Args:
            metadata: File metadata (filename, size, mime_type, etc.)
            preview: Analysis results from processors (optional)
            full_path: Full file path for additional checks (optional)
        
        Returns:
            {
                "type": str,
                "category": str,
                "subcategories": [str],
                "confidence": float
            }
        """
        filename = metadata.get("filename", "")
        mime_type = metadata.get("mime_type", "")
        file_size = metadata.get("size", 0)
        
        # Extract extension
        ext = Path(filename).suffix.lower()
        
        # Detect primary type
        file_type = self._detect_type(ext, mime_type, preview)
        
        # Route to type-specific classifier
        if file_type == "image":
            return self._classify_image(metadata, preview, ext)
        elif file_type == "json":
            return self._classify_json(metadata, preview)
        elif file_type == "pdf":
            return self._classify_pdf(metadata, preview)
        elif file_type == "audio":
            return self._classify_audio(metadata, preview, ext)
        elif file_type == "video":
            return self._classify_video(metadata, preview)
        elif file_type == "text":
            return self._classify_text(metadata, preview, ext)
        else:
            # Fallback: group by extension
            return self._fallback_classification(ext, file_type)
    
    def _detect_type(self, ext: str, mime_type: str, preview: Optional[Dict]) -> str:
        """Detect primary file type."""
        # Check extension first
        if ext in EXTENSION_TYPE_MAP:
            return EXTENSION_TYPE_MAP[ext]
        
        # Check MIME type
        if mime_type:
            if mime_type.startswith('image/'):
                return 'image'
            elif mime_type.startswith('audio/'):
                return 'audio'
            elif mime_type.startswith('video/'):
                return 'video'
            elif 'pdf' in mime_type.lower():
                return 'pdf'
            elif 'json' in mime_type.lower():
                return 'json'
            elif mime_type.startswith('text/'):
                return 'text'
        
        # Check preview for type hints
        if preview:
            if preview.get("type") in ["image", "audio", "video", "pdf", "json"]:
                return preview["type"]
        
        return 'binary'
    
    # ========================================================================
    # IMAGE CLASSIFICATION - 15+ categories
    # ========================================================================
    
    def _classify_image(
        self, metadata: Dict, preview: Optional[Dict], ext: str
    ) -> Dict[str, Any]:
        """
        Advanced image classification with EXIF, resolution, aspect ratio,
        color variance, borders, and heuristics.
        
        Categories:
        - image_screenshot
        - image_scanned_document
        - image_photo_realworld
        - image_graphic_art
        - image_digital_poster
        - image_photo_document
        - image_meme
        - image_selfie_frontcamera
        - image_ai_generated_like
        - image_square, image_portrait, image_landscape, image_panorama
        """
        subcategories = []
        confidence = 0.5
        
        # Add format subcategory
        if ext in ['.jpg', '.jpeg']:
            subcategories.append('image_jpeg')
        elif ext == '.png':
            subcategories.append('image_png')
        elif ext == '.webp':
            subcategories.append('image_webp')
        elif ext == '.gif':
            subcategories.append('image_gif')
        elif ext in ['.tiff', '.tif']:
            subcategories.append('image_tiff')
        elif ext == '.bmp':
            subcategories.append('image_bmp')
        
        if not preview:
            return {
                "type": "image",
                "category": f"image{ext}",
                "subcategories": subcategories,
                "confidence": 0.3
            }
        
        # Extract analysis data
        width = preview.get("width", 0)
        height = preview.get("height", 0)
        has_exif = preview.get("has_exif", False)
        has_alpha = preview.get("has_alpha", False)
        file_size = metadata.get("size", 0)
        
        # Aspect ratio classification
        aspect_ratio = width / height if height > 0 else 1.0
        
        if 0.95 <= aspect_ratio <= 1.05:
            subcategories.append('image_square')
        elif aspect_ratio < 0.7:
            subcategories.append('image_portrait')
        elif aspect_ratio > 1.8:
            subcategories.append('image_panorama')
        else:
            subcategories.append('image_landscape')
        
        # Primary category detection
        category = "image_photo"  # default
        
        # AI generated detection (check before screenshot to catch square AI images)
        if self._is_ai_generated(preview, has_exif, width, height, ext):
            category = "image_ai_generated_like"
            confidence = 0.65
        
        # Screenshot detection
        elif self._is_screenshot(preview, width, height, ext, file_size):
            category = "image_screenshot"
            confidence = 0.85
        
        # Scanned document detection
        elif self._is_scanned_document(preview, width, height, aspect_ratio, file_size):
            category = "image_scanned_document"
            confidence = 0.80
        
        # Meme detection
        elif self._is_meme(preview, width, height, has_alpha, ext):
            category = "image_meme"
            confidence = 0.75
        
        # Selfie/front camera detection
        elif self._is_selfie(preview, has_exif, width, height):
            category = "image_selfie_frontcamera"
            confidence = 0.70
        
        # AI generated detection
        elif self._is_ai_generated(preview, has_exif, width, height, ext):
            category = "image_ai_generated_like"
            confidence = 0.65
        
        # Digital poster/graphic art
        elif self._is_digital_poster(preview, has_alpha, width, height, file_size):
            category = "image_digital_poster"
            confidence = 0.70
        
        elif self._is_graphic_art(preview, has_alpha, ext):
            category = "image_graphic_art"
            confidence = 0.65
        
        # Photo document (receipt, ID card, etc.)
        elif self._is_photo_document(preview, aspect_ratio, width, height):
            category = "image_photo_document"
            confidence = 0.75
        
        # Real world photo (default if has EXIF)
        elif has_exif:
            category = "image_photo_realworld"
            confidence = 0.80
        
        return {
            "type": "image",
            "category": category,
            "subcategories": subcategories,
            "confidence": confidence
        }
    
    def _is_screenshot(self, preview: Dict, w: int, h: int, ext: str, size: int) -> bool:
        """Detect screenshot using heuristics."""
        # Common screenshot resolutions
        common_screens = [
            (1920, 1080), (1366, 768), (1440, 900), (2560, 1440),
            (3840, 2160), (1280, 720), (1600, 900), (2560, 1600)
        ]
        
        # Check exact match with common screen sizes
        if (w, h) in common_screens:
            return True
        
        # PNG without EXIF is often screenshot
        if ext == '.png' and not preview.get("has_exif", False):
            # Large PNG files are often screenshots
            if w >= 1000 and h >= 600:
                return True
        
        # High color variance with sharp edges (from quality metrics)
        quality = preview.get("quality", {})
        if quality.get("sharpness", 0) > 70 and not preview.get("has_exif", False):
            return True
        
        return False
    
    def _is_scanned_document(self, preview: Dict, w: int, h: int, ar: float, size: int) -> bool:
        """Detect scanned documents."""
        # A4/Letter aspect ratios: ~1.29-1.55
        if 1.25 <= ar <= 1.6:
            # Large dimensions typical of scans
            if w >= 1500 or h >= 2000:
                # Low color variance (mostly black/white text)
                colors = preview.get("colors", {})
                if colors.get("is_grayscale", False):
                    return True
                
                # Low dominant color count
                dom_colors = colors.get("dominant_colors", [])
                if len(dom_colors) <= 3:
                    return True
        
        # TIFF files are often scans
        if preview.get("format", "").upper() in ["TIFF", "TIF"]:
            return True
        
        return False
    
    def _is_meme(self, preview: Dict, w: int, h: int, has_alpha: bool, ext: str) -> bool:
        """Detect memes using heuristics."""
        # Memes are often square or near-square
        aspect = w / h if h > 0 else 1.0
        if 0.8 <= aspect <= 1.2:
            # Small to medium size
            if 300 <= w <= 1200 and 300 <= h <= 1200:
                # JPEGs without EXIF
                if ext in ['.jpg', '.jpeg'] and not preview.get("has_exif", False):
                    return True
        
        return False
    
    def _is_selfie(self, preview: Dict, has_exif: bool, w: int, h: int) -> bool:
        """Detect selfies (front camera photos)."""
        if not has_exif:
            return False
        
        # Portrait orientation
        if h > w:
            # Mobile photo dimensions
            if 1000 <= w <= 5000 and 1500 <= h <= 8000:
                # Could check EXIF for front camera flag if available
                return True
        
        return False
    
    def _is_ai_generated(self, preview: Dict, has_exif: bool, w: int, h: int, ext: str) -> bool:
        """Detect AI-generated images."""
        # AI images typically have no EXIF
        if has_exif:
            return False
        
        # Common AI generation sizes
        ai_sizes = [
            (512, 512), (768, 768), (1024, 1024),
            (512, 768), (768, 512), (1024, 768), (768, 1024)
        ]
        
        if (w, h) in ai_sizes:
            return True
        
        # PNG or WEBP without EXIF, square-ish
        aspect = w / h if h > 0 else 1.0
        if ext in ['.png', '.webp'] and 0.6 <= aspect <= 1.4:
            # Medium to large size
            if 500 <= w <= 2048 and 500 <= h <= 2048:
                return True
        
        return False
    
    def _is_digital_poster(self, preview: Dict, has_alpha: bool, w: int, h: int, size: int) -> bool:
        """Detect digital posters."""
        # Portrait orientation, large dimensions
        if h > w and h >= 1000:
            # Has transparency (PNG with alpha)
            if has_alpha:
                return True
            
            # Large file size for dimensions
            pixels = w * h
            if pixels > 0 and size / pixels > 0.5:  # High quality
                return True
        
        return False
    
    def _is_graphic_art(self, preview: Dict, has_alpha: bool, ext: str) -> bool:
        """Detect graphic art."""
        # PNG with alpha channel
        if ext == '.png' and has_alpha:
            # Many distinct colors
            colors = preview.get("colors", {})
            dom_colors = colors.get("dominant_colors", [])
            if len(dom_colors) >= 4:
                return True
        
        # SVG is always graphic art
        if ext == '.svg':
            return True
        
        return False
    
    def _is_photo_document(self, preview: Dict, ar: float, w: int, h: int) -> bool:
        """Detect photo documents (receipts, IDs, cards)."""
        # Small rectangular images
        if w < 1500 and h < 2000:
            # Card-like aspect ratios
            if 1.4 <= ar <= 1.7 or 0.58 <= ar <= 0.72:
                return True
        
        return False
    
    # ========================================================================
    # JSON CLASSIFICATION - 5 categories
    # ========================================================================
    
    def _classify_json(self, metadata: Dict, preview: Optional[Dict]) -> Dict[str, Any]:
        """
        JSON classification with schema generation.
        
        Categories:
        - json_flat_structured (SQL-ready with schema)
        - json_semistructured
        - json_nested
        - json_unstructured
        - json_invalid
        """
        if not preview:
            return {
                "type": "json",
                "category": "json_unstructured",
                "subcategories": [],
                "confidence": 0.3
            }
        
        # Check for parse errors
        if preview.get("parse_error", False):
            return {
                "type": "json",
                "category": "json_invalid",
                "subcategories": ["json_parse_error"],
                "confidence": 1.0
            }
        
        shape = preview.get("shape", "unknown")
        consistency = preview.get("field_consistency", 0.0)
        max_depth = preview.get("max_depth", 0)
        nested_ratio = preview.get("nested_ratio", 0.0)
        record_count = preview.get("record_count", 0)
        
        subcategories = []
        
        # Flat structured: array of objects, high consistency, low depth
        if shape == "array_of_objects":
            if consistency >= 0.95 and max_depth <= 2 and nested_ratio < 0.3:
                category = "json_flat_structured"
                confidence = 0.95
                subcategories.append("sql_ready")
                
                # Generate SQL schema hint
                if preview.get("schema"):
                    subcategories.append("has_schema")
            
            elif consistency >= 0.70:
                category = "json_semistructured"
                confidence = 0.80
                subcategories.append("partial_schema")
            
            else:
                category = "json_unstructured"
                confidence = 0.70
        
        # Nested structures
        elif max_depth > 3 or nested_ratio > 0.5:
            category = "json_nested"
            confidence = 0.85
            subcategories.append(f"depth_{max_depth}")
        
        # Simple structures
        elif shape in ["scalar", "array_of_scalars", "single_object"]:
            if max_depth <= 1:
                category = "json_flat_structured"
                confidence = 0.75
            else:
                category = "json_nested"
                confidence = 0.70
        
        else:
            category = "json_unstructured"
            confidence = 0.60
        
        return {
            "type": "json",
            "category": category,
            "subcategories": subcategories,
            "confidence": confidence
        }
    
    # ========================================================================
    # PDF CLASSIFICATION - 9 categories
    # ========================================================================
    
    def _classify_pdf(self, metadata: Dict, preview: Optional[Dict]) -> Dict[str, Any]:
        """
        Advanced PDF classification.
        
        Categories:
        - pdf_text_document
        - pdf_scanned
        - pdf_form
        - pdf_with_images
        - pdf_with_tables
        - pdf_ebook_layout
        - pdf_presentation
        - pdf_slides
        - pdf_receipt
        """
        if not preview:
            return {
                "type": "pdf",
                "category": "pdf_document",
                "subcategories": [],
                "confidence": 0.3
            }
        
        subcategories = []
        confidence = 0.5
        
        is_scanned = preview.get("is_scanned", False)
        has_forms = preview.get("has_forms", False)
        image_ratio = preview.get("image_ratio", 0.0)
        text_length = preview.get("text_length", 0)
        page_count = preview.get("page_count", 1)
        
        # Form detection (highest priority)
        if has_forms:
            category = "pdf_form"
            confidence = 0.95
            subcategories.append("interactive_form")
        
        # Scanned document
        elif is_scanned:
            category = "pdf_scanned"
            confidence = 0.90
            subcategories.append("ocr_applied")
        
        # Receipt detection (small, portrait, low page count)
        elif page_count <= 2 and text_length < 3000:
            if self._is_pdf_receipt(preview):
                category = "pdf_receipt"
                confidence = 0.85
                subcategories.append("short_document")
        
        # Presentation/slides (multiple pages, high image ratio)
        elif page_count >= 5 and image_ratio > 0.3:
            if self._is_pdf_slides(preview, page_count):
                category = "pdf_slides"
                confidence = 0.80
                subcategories.append(f"pages_{page_count}")
            else:
                category = "pdf_presentation"
                confidence = 0.75
        
        # Ebook layout detection (many pages, specific formatting)
        elif page_count >= 50:
            if self._is_pdf_ebook(preview, page_count, text_length):
                category = "pdf_ebook_layout"
                confidence = 0.80
                subcategories.append("long_document")
        
        # Tables detection
        elif self._has_tables(preview):
            category = "pdf_with_tables"
            confidence = 0.75
            subcategories.append("structured_data")
        
        # Image-heavy PDF
        elif image_ratio > 0.4:
            category = "pdf_with_images"
            confidence = 0.75
            subcategories.append(f"images_{int(image_ratio*100)}pct")
        
        # Default: text document
        else:
            category = "pdf_text_document"
            confidence = 0.70
            subcategories.append("primarily_text")
        
        return {
            "type": "pdf",
            "category": category,
            "subcategories": subcategories,
            "confidence": confidence
        }
    
    def _is_pdf_receipt(self, preview: Dict) -> bool:
        """Detect receipt PDFs."""
        text = preview.get("text_content", "").lower()
        
        # Receipt keywords
        receipt_keywords = [
            "total", "subtotal", "tax", "receipt", "invoice",
            "payment", "transaction", "qty", "amount", "cashier"
        ]
        
        matches = sum(1 for kw in receipt_keywords if kw in text)
        return matches >= 3
    
    def _is_pdf_slides(self, preview: Dict, page_count: int) -> bool:
        """Detect presentation slides."""
        # Slides typically have consistent page sizes, minimal text per page
        text_length = preview.get("text_length", 0)
        avg_text_per_page = text_length / page_count if page_count > 0 else 0
        
        # Slides have less text per page (< 500 chars avg)
        if avg_text_per_page < 500:
            return True
        
        return False
    
    def _is_pdf_ebook(self, preview: Dict, page_count: int, text_length: int) -> bool:
        """Detect ebook-style PDFs."""
        # Ebooks have high text density
        avg_text_per_page = text_length / page_count if page_count > 0 else 0
        
        # Ebooks: > 1500 chars per page, many pages
        if page_count >= 50 and avg_text_per_page > 1500:
            return True
        
        return False
    
    def _has_tables(self, preview: Dict) -> bool:
        """Detect tables in PDF."""
        # Look for table indicators in text
        text = preview.get("text_content", "").lower()
        
        # Table keywords/patterns
        table_indicators = [
            "table", "row", "column", "header",
            "|", "┃", "│", "─", "━"
        ]
        
        matches = sum(1 for ind in table_indicators if ind in text)
        return matches >= 2
    
    # ========================================================================
    # AUDIO CLASSIFICATION - 5 categories
    # ========================================================================
    
    def _classify_audio(
        self, metadata: Dict, preview: Optional[Dict], ext: str
    ) -> Dict[str, Any]:
        """
        Audio classification using metadata.
        
        Categories:
        - audio_music
        - audio_voice_note
        - audio_whatsapp_voice
        - audio_podcast_like
        - audio_recording
        """
        subcategories = []
        confidence = 0.5
        
        # Add format subcategory
        if ext == '.mp3':
            subcategories.append('audio_mp3')
        elif ext == '.m4a':
            subcategories.append('audio_m4a')
        elif ext == '.wav':
            subcategories.append('audio_wav')
        elif ext == '.opus':
            subcategories.append('audio_opus')
        
        if not preview:
            return {
                "type": "audio",
                "category": "audio_recording",
                "subcategories": subcategories,
                "confidence": 0.3
            }
        
        duration = preview.get("duration_seconds", 0)
        file_size = metadata.get("size", 0)
        bitrate = file_size * 8 / duration if duration > 0 else 0
        
        # WhatsApp voice note detection
        if self._is_whatsapp_voice(ext, duration, file_size):
            category = "audio_whatsapp_voice"
            confidence = 0.90
            subcategories.append("voice_message")
        
        # Voice note (short audio, low quality)
        elif duration < 120 and bitrate < 64000:
            category = "audio_voice_note"
            confidence = 0.80
            subcategories.append("short_recording")
        
        # Podcast (long, medium quality)
        elif duration > 600 and 64000 <= bitrate <= 192000:
            category = "audio_podcast_like"
            confidence = 0.75
            subcategories.append("long_audio")
        
        # Music (medium duration, high quality)
        elif 120 <= duration <= 600 and bitrate > 128000:
            category = "audio_music"
            confidence = 0.70
            subcategories.append("high_quality")
        
        # Generic recording
        else:
            category = "audio_recording"
            confidence = 0.60
        
        return {
            "type": "audio",
            "category": category,
            "subcategories": subcategories,
            "confidence": confidence
        }
    
    def _is_whatsapp_voice(self, ext: str, duration: float, size: int) -> bool:
        """Detect WhatsApp voice notes."""
        # WhatsApp uses opus in short clips
        if ext == '.opus' and duration < 180:
            # Typical WhatsApp voice note sizes
            if 5000 < size < 500000:  # 5KB - 500KB
                return True
        
        # Also check m4a (older WhatsApp)
        if ext == '.m4a' and duration < 180:
            if 10000 < size < 1000000:
                return True
        
        return False
    
    # ========================================================================
    # VIDEO CLASSIFICATION - 5 categories
    # ========================================================================
    
    def _classify_video(self, metadata: Dict, preview: Optional[Dict]) -> Dict[str, Any]:
        """
        Video classification using metadata and resolution.
        
        Categories:
        - video_youtube_like
        - video_screen_recording
        - video_portrait
        - video_landscape
        - video_camera_clip
        """
        subcategories = []
        confidence = 0.5
        
        if not preview:
            return {
                "type": "video",
                "category": "video_clip",
                "subcategories": subcategories,
                "confidence": 0.3
            }
        
        width = preview.get("width", 0)
        height = preview.get("height", 0)
        duration = preview.get("duration_seconds", 0)
        fps = preview.get("fps", 0)
        
        # Aspect ratio
        aspect = width / height if height > 0 else 1.0
        
        # Portrait video (mobile)
        if aspect < 0.8:
            category = "video_portrait"
            confidence = 0.90
            subcategories.append("vertical_video")
        
        # Screen recording detection (common resolutions)
        elif self._is_screen_recording(width, height, fps):
            category = "video_screen_recording"
            confidence = 0.85
            subcategories.append(f"{width}x{height}")
        
        # YouTube-like (16:9, high quality, medium-long duration)
        elif self._is_youtube_like(width, height, duration, fps):
            category = "video_youtube_like"
            confidence = 0.80
            subcategories.append("hd_video")
        
        # Camera clip (mobile camera formats)
        elif self._is_camera_clip(width, height, duration):
            category = "video_camera_clip"
            confidence = 0.75
            subcategories.append("mobile_recording")
        
        # Landscape (default)
        else:
            category = "video_landscape"
            confidence = 0.65
            subcategories.append("horizontal_video")
        
        return {
            "type": "video",
            "category": category,
            "subcategories": subcategories,
            "confidence": confidence
        }
    
    def _is_screen_recording(self, w: int, h: int, fps: float) -> bool:
        """Detect screen recordings."""
        # Common screen recording resolutions
        screen_sizes = [
            (1920, 1080), (1280, 720), (2560, 1440),
            (1366, 768), (1440, 900), (3840, 2160)
        ]
        
        if (w, h) in screen_sizes:
            # Screen recordings often have specific FPS
            if 15 <= fps <= 30:
                return True
        
        return False
    
    def _is_youtube_like(self, w: int, h: int, duration: float, fps: float) -> bool:
        """Detect YouTube-style videos."""
        # 16:9 aspect ratio
        aspect = w / h if h > 0 else 1.0
        
        if 1.7 <= aspect <= 1.8:
            # HD resolutions
            if h >= 720:
                # Typical video FPS
                if 24 <= fps <= 60:
                    # Medium to long duration
                    if duration > 60:
                        return True
        
        return False
    
    def _is_camera_clip(self, w: int, h: int, duration: float) -> bool:
        """Detect mobile camera clips."""
        # Common mobile resolutions
        aspect = w / h if h > 0 else 1.0
        
        # 16:9 or 4:3 mobile video
        if 1.3 <= aspect <= 1.8:
            # Short to medium duration
            if 5 <= duration <= 300:
                # Mobile typical resolutions
                if 720 <= h <= 2160:
                    return True
        
        return False
    
    # ========================================================================
    # TEXT CLASSIFICATION
    # ========================================================================
    
    def _classify_text(
        self, metadata: Dict, preview: Optional[Dict], ext: str
    ) -> Dict[str, Any]:
        """Basic text classification."""
        subcategories = []
        
        if ext == '.md':
            category = "text_markdown"
            subcategories.append("markdown")
        elif ext == '.csv':
            category = "text_csv"
            subcategories.append("tabular")
        elif ext == '.xml':
            category = "text_xml"
            subcategories.append("structured")
        elif ext in ['.py', '.js', '.ts', '.html', '.css']:
            category = "text_code"
            subcategories.append(f"code{ext}")
        else:
            category = "text_document"
            subcategories.append("plain_text")
        
        return {
            "type": "text",
            "category": category,
            "subcategories": subcategories,
            "confidence": 0.90
        }
    
    # ========================================================================
    # FALLBACK CLASSIFICATION
    # ========================================================================
    
    def _fallback_classification(self, ext: str, file_type: str) -> Dict[str, Any]:
        """
        Fallback: group by extension when classification fails.
        Examples: .md_group, .mp3_group, .unknown_group
        """
        if ext:
            category = f"{ext[1:]}_group"  # Remove leading dot
        else:
            category = "unknown_group"
        
        return {
            "type": file_type,
            "category": category,
            "subcategories": ["fallback"],
            "confidence": 0.4
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_classifier = AdvancedClassifier()

def classify_file(
    metadata: Dict[str, Any],
    preview: Optional[Dict[str, Any]] = None,
    full_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Global classification function.
    
    Args:
        metadata: File metadata dict
        preview: Analysis results from processors
        full_path: Full file path (optional)
    
    Returns:
        {
            "type": str,
            "category": str,
            "subcategories": [str],
            "confidence": float
        }
    """
    return _classifier.classify_file(metadata, preview, full_path)
