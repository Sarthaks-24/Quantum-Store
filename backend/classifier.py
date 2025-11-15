"""
QuantumStore Unified Classification System
===========================================

SINGLE SOURCE OF TRUTH for file classification.
Completely rebuilt from scratch.

Classification Output:
{
    "type": "pdf" | "json" | "text" | "image" | "audio" | "video" | "binary",
    "subtype": "document" | "scanned" | "structured_data" | etc.,
    "category": "pdf_financial" | "json_structured_sql" | etc.,
    "confidence": 0.0 - 1.0,
    "metadata": {...}  # Additional classification details
}
"""

import os
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path


# ============================================================================
# MASTER EXTENSION MAP - Single source of truth
# ============================================================================

EXTENSION_TYPE_MAP = {
    # PDF Documents
    '.pdf': ('pdf', 'document'),
    
    # Data Formats
    '.json': ('json', 'data'),
    '.jsonl': ('json', 'data'),
    '.csv': ('text', 'tabular'),
    '.tsv': ('text', 'tabular'),
    '.xml': ('text', 'structured'),
    '.yaml': ('text', 'config'),
    '.yml': ('text', 'config'),
    '.toml': ('text', 'config'),
    
    # Documents
    '.txt': ('text', 'document'),
    '.md': ('text', 'markdown'),
    '.rtf': ('text', 'document'),
    '.doc': ('binary', 'document'),
    '.docx': ('binary', 'document'),
    
    # Spreadsheets
    '.xlsx': ('binary', 'spreadsheet'),
    '.xls': ('binary', 'spreadsheet'),
    
    # Images
    '.jpg': ('image', 'raster'),
    '.jpeg': ('image', 'raster'),
    '.png': ('image', 'raster'),
    '.gif': ('image', 'animated'),
    '.bmp': ('image', 'raster'),
    '.svg': ('image', 'vector'),
    '.webp': ('image', 'raster'),
    '.tiff': ('image', 'raster'),
    '.tif': ('image', 'raster'),
    '.ico': ('image', 'icon'),
    
    # Audio
    '.mp3': ('audio', 'compressed'),
    '.m4a': ('audio', 'compressed'),
    '.wav': ('audio', 'uncompressed'),
    '.flac': ('audio', 'lossless'),
    '.aac': ('audio', 'compressed'),
    '.ogg': ('audio', 'compressed'),
    '.wma': ('audio', 'compressed'),
    
    # Video
    '.mp4': ('video', 'compressed'),
    '.mov': ('video', 'compressed'),
    '.avi': ('video', 'compressed'),
    '.mkv': ('video', 'container'),
    '.wmv': ('video', 'compressed'),
    '.flv': ('video', 'streaming'),
    '.webm': ('video', 'streaming'),
    
    # Code
    '.py': ('text', 'code'),
    '.js': ('text', 'code'),
    '.ts': ('text', 'code'),
    '.jsx': ('text', 'code'),
    '.tsx': ('text', 'code'),
    '.cpp': ('text', 'code'),
    '.c': ('text', 'code'),
    '.h': ('text', 'code'),
    '.hpp': ('text', 'code'),
    '.java': ('text', 'code'),
    '.go': ('text', 'code'),
    '.rs': ('text', 'code'),
    '.rb': ('text', 'code'),
    '.php': ('text', 'code'),
    
    # Web
    '.html': ('text', 'web'),
    '.htm': ('text', 'web'),
    '.css': ('text', 'stylesheet'),
    '.scss': ('text', 'stylesheet'),
    '.sass': ('text', 'stylesheet'),
    '.less': ('text', 'stylesheet'),
    
    # Archives
    '.zip': ('binary', 'archive'),
    '.tar': ('binary', 'archive'),
    '.gz': ('binary', 'archive'),
    '.rar': ('binary', 'archive'),
    '.7z': ('binary', 'archive'),
}


# Magic bytes for file detection
MAGIC_BYTES = {
    b'%PDF': ('pdf', 'document'),
    b'\x89PNG\r\n\x1a\n': ('image', 'raster'),
    b'\xff\xd8\xff': ('image', 'raster'),
    b'GIF87a': ('image', 'animated'),
    b'GIF89a': ('image', 'animated'),
    b'PK\x03\x04': ('binary', 'archive'),  # ZIP
    b'Rar!\x1a\x07': ('binary', 'archive'),  # RAR
}


class UnifiedClassifier:
    """
    Single classification engine for ALL file types.
    Replaces all previous categorization logic.
    """
    
    def __init__(self):
        self.confidence_threshold = 0.7
    
    def classify_file(
        self,
        filename: str,
        file_path: Optional[str] = None,
        mime_type: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        MASTER CLASSIFICATION FUNCTION.
        Single entry point for all file classification.
        
        Args:
            filename: File name
            file_path: Full path to file (optional)
            mime_type: MIME type from upload (optional)
            file_bytes: First 512 bytes for magic byte detection (optional)
            analysis: Content analysis from processor (optional)
        
        Returns:
            Classification result:
            {
                "type": str,
                "subtype": str,
                "category": str,
                "confidence": float,
                "metadata": dict
            }
        """
        # Step 1: Normalize extension
        ext = self._normalize_extension(filename)
        
        # Step 2: Detect type via magic bytes (highest priority)
        type_from_magic, subtype_from_magic = self._detect_from_magic_bytes(file_bytes)
        
        # Step 3: Detect type from extension
        type_from_ext, subtype_from_ext = self._detect_from_extension(ext)
        
        # Step 4: Detect type from MIME
        type_from_mime, subtype_from_mime = self._detect_from_mime(mime_type)
        
        # Step 5: Resolve type conflicts (magic > extension > MIME)
        file_type, subtype = self._resolve_type(
            (type_from_magic, subtype_from_magic),
            (type_from_ext, subtype_from_ext),
            (type_from_mime, subtype_from_mime)
        )
        
        # Step 6: Get category from content analysis
        category, confidence = self._get_category_from_analysis(
            file_type, subtype, analysis
        )
        
        # Step 7: Build metadata
        metadata = {
            "extension": ext,
            "detected_from": self._get_detection_source(
                type_from_magic, type_from_ext, type_from_mime, file_type
            ),
            "mime_type": mime_type,
        }
        
        # Add type-specific metadata
        if analysis:
            metadata.update(self._extract_type_metadata(file_type, analysis))
        
        return {
            "type": file_type,
            "subtype": subtype,
            "category": category,
            "confidence": confidence,
            "metadata": metadata
        }
    
    def _normalize_extension(self, filename: str) -> str:
        """Extract and normalize file extension."""
        ext = Path(filename).suffix.lower()
        return ext if ext else ""
    
    def _detect_from_magic_bytes(
        self, file_bytes: Optional[bytes]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect file type from magic bytes."""
        if not file_bytes:
            return None, None
        
        for magic, (ftype, subtype) in MAGIC_BYTES.items():
            if file_bytes.startswith(magic):
                return ftype, subtype
        
        # JSON detection (heuristic)
        if file_bytes.strip().startswith((b'{', b'[')):
            return 'json', 'data'
        
        return None, None
    
    def _detect_from_extension(self, ext: str) -> Tuple[Optional[str], Optional[str]]:
        """Detect file type from extension."""
        if ext in EXTENSION_TYPE_MAP:
            return EXTENSION_TYPE_MAP[ext]
        return None, None
    
    def _detect_from_mime(
        self, mime_type: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect file type from MIME type."""
        if not mime_type:
            return None, None
        
        mime_lower = mime_type.lower()
        
        # PDF
        if 'pdf' in mime_lower:
            return 'pdf', 'document'
        
        # JSON
        if 'json' in mime_lower:
            return 'json', 'data'
        
        # Images
        if mime_lower.startswith('image/'):
            if 'svg' in mime_lower:
                return 'image', 'vector'
            elif 'gif' in mime_lower:
                return 'image', 'animated'
            else:
                return 'image', 'raster'
        
        # Audio
        if mime_lower.startswith('audio/'):
            return 'audio', 'compressed'
        
        # Video
        if mime_lower.startswith('video/'):
            return 'video', 'compressed'
        
        # Text
        if mime_lower.startswith('text/'):
            if 'html' in mime_lower:
                return 'text', 'web'
            elif 'css' in mime_lower:
                return 'text', 'stylesheet'
            else:
                return 'text', 'document'
        
        return None, None
    
    def _resolve_type(
        self,
        magic_result: Tuple[Optional[str], Optional[str]],
        ext_result: Tuple[Optional[str], Optional[str]],
        mime_result: Tuple[Optional[str], Optional[str]]
    ) -> Tuple[str, str]:
        """
        Resolve type conflicts.
        Priority: magic bytes > extension > MIME > unknown
        """
        # Magic bytes has highest priority
        if magic_result[0]:
            return magic_result
        
        # Extension second
        if ext_result[0]:
            return ext_result
        
        # MIME third
        if mime_result[0]:
            return mime_result
        
        # Unknown
        return 'binary', 'unknown'
    
    def _get_detection_source(
        self,
        type_from_magic: Optional[str],
        type_from_ext: Optional[str],
        type_from_mime: Optional[str],
        final_type: str
    ) -> str:
        """Determine which detection method was used."""
        if type_from_magic == final_type:
            return 'magic_bytes'
        elif type_from_ext == final_type:
            return 'extension'
        elif type_from_mime == final_type:
            return 'mime_type'
        else:
            return 'heuristic'
    
    def _get_category_from_analysis(
        self,
        file_type: str,
        subtype: str,
        analysis: Optional[Dict[str, Any]]
    ) -> Tuple[str, float]:
        """
        Get specific category from content analysis.
        
        Returns:
            (category, confidence)
        """
        if not analysis:
            # No analysis - use type-based default
            return self._get_default_category(file_type, subtype), 0.5
        
        # Check if analysis provided a content_category
        if 'content_category' in analysis:
            category = analysis['content_category']
            confidence = analysis.get('category_confidence', 0.8)
            return category, confidence
        
        # Type-specific category extraction
        if file_type == 'pdf':
            return self._categorize_pdf(analysis)
        elif file_type == 'json':
            return self._categorize_json(analysis)
        elif file_type == 'image':
            return self._categorize_image(analysis)
        elif file_type == 'video':
            return self._categorize_video(analysis)
        elif file_type == 'text':
            return self._categorize_text(analysis)
        else:
            return self._get_default_category(file_type, subtype), 0.5
    
    def _get_default_category(self, file_type: str, subtype: str) -> str:
        """Get default category based on type and subtype."""
        if file_type == 'pdf':
            return 'pdf_document'
        elif file_type == 'json':
            return 'json_data'
        elif file_type == 'image':
            return 'image_general'
        elif file_type == 'video':
            return 'video_general'
        elif file_type == 'audio':
            return 'audio_general'
        elif file_type == 'text':
            if subtype == 'code':
                return 'text_code'
            elif subtype == 'markdown':
                return 'text_markdown'
            else:
                return 'text_document'
        else:
            return 'binary_unknown'
    
    # ========================================================================
    # Type-Specific Categorization
    # ========================================================================
    
    def _categorize_pdf(self, analysis: Dict[str, Any]) -> Tuple[str, float]:
        """
        PDF categorization based on content analysis.
        
        Categories:
        - pdf_empty: No extractable content
        - pdf_scanned: Scanned/OCR document
        - pdf_text_document: Primarily text
        - pdf_financial: Financial document
        - pdf_report: Business report
        - pdf_academic: Academic paper
        - pdf_form: Contains form fields
        - pdf_mixed: Mixed content
        """
        # Check for empty
        text_length = analysis.get('text_length', 0)
        if text_length < 10:
            return 'pdf_empty', 1.0
        
        # Check if scanned
        if analysis.get('is_scanned', False):
            return 'pdf_scanned', 0.95
        
        # Check for form fields
        if analysis.get('has_forms', False):
            return 'pdf_form', 0.95
        
        # Analyze content categories (from analyzer)
        categories = analysis.get('categories', {})
        
        if categories.get('financial', 0) > 0.3:
            return 'pdf_financial', 0.9
        
        if categories.get('academic', 0) > 0.3:
            return 'pdf_academic', 0.9
        
        if categories.get('report', 0) > 0.3:
            return 'pdf_report', 0.85
        
        # Check image ratio
        image_ratio = analysis.get('image_ratio', 0)
        text_ratio = analysis.get('text_ratio', 1.0)
        
        if image_ratio > 0.5:
            return 'pdf_mixed', 0.8
        
        if text_ratio > 0.8:
            return 'pdf_text_document', 0.9
        
        # Default
        return 'pdf_document', 0.7
    
    def _categorize_json(self, analysis: Dict[str, Any]) -> Tuple[str, float]:
        """
        JSON categorization based on structure analysis.
        
        Categories:
        - json_invalid: Parse error
        - json_structured_sql: Flat, consistent, SQL-ready
        - json_structured_small_sql: Small structured dataset
        - json_semi_structured: 60-95% consistency
        - json_nested: Nested objects
        - json_deep_nested: >3 levels deep
        - json_mixed: Heterogeneous
        - json_plain_object: Single object
        - json_scalar: Single value
        - json_array_of_scalars: Simple array
        """
        # Check for parse errors
        if analysis.get('parse_error', False):
            return 'json_invalid', 1.0
        
        # Get structure info
        shape = analysis.get('shape', 'unknown')
        
        # Simple shapes
        if shape == 'scalar':
            return 'json_scalar', 1.0
        
        if shape == 'array_of_scalars':
            return 'json_array_of_scalars', 1.0
        
        if shape == 'single_object':
            max_depth = analysis.get('max_depth', 1)
            if max_depth > 3:
                return 'json_deep_nested', 0.95
            elif max_depth > 1:
                return 'json_nested', 0.9
            else:
                return 'json_plain_object', 0.95
        
        # Array of objects - complex analysis
        if shape == 'array_of_objects':
            consistency = analysis.get('field_consistency', 0)
            max_depth = analysis.get('max_depth', 1)
            nested_ratio = analysis.get('nested_ratio', 0)
            record_count = analysis.get('record_count', 0)
            
            # SQL suitability check
            is_sql_suitable = (
                consistency >= 0.6 and
                max_depth <= 2 and
                nested_ratio < 0.3
            )
            
            if is_sql_suitable:
                if consistency >= 0.95:
                    if record_count < 100:
                        return 'json_structured_small_sql', 0.95
                    else:
                        return 'json_structured_sql', 0.95
                elif consistency >= 0.60:
                    return 'json_semi_structured', 0.85
                else:
                    return 'json_mixed', 0.75
            else:
                # NoSQL territory
                if max_depth > 3:
                    return 'json_deep_nested', 0.9
                elif nested_ratio > 0.5:
                    return 'json_nested', 0.85
                else:
                    return 'json_mixed', 0.7
        
        # Mixed/unknown
        return 'json_mixed', 0.6
    
    def _categorize_image(self, analysis: Dict[str, Any]) -> Tuple[str, float]:
        """Image categorization."""
        # Get dimensions
        width = analysis.get('width', 0)
        height = analysis.get('height', 0)
        
        # Portrait vs landscape
        if width > 0 and height > 0:
            aspect_ratio = width / height
            
            if aspect_ratio < 0.75:
                return 'image_portrait', 0.8
            elif aspect_ratio > 1.5:
                return 'image_landscape', 0.8
        
        # Check for screenshot indicators
        if analysis.get('is_screenshot', False):
            return 'image_screenshot', 0.9
        
        # Default
        return 'image_general', 0.7
    
    def _categorize_video(self, analysis: Dict[str, Any]) -> Tuple[str, float]:
        """Video categorization."""
        duration = analysis.get('duration', 0)
        
        if duration > 0:
            if duration < 120:  # < 2 minutes
                return 'video_short', 0.9
            elif duration < 600:  # 2-10 minutes
                return 'video_medium', 0.9
            else:
                return 'video_long', 0.9
        
        # Check resolution
        height = analysis.get('height', 0)
        if height >= 2160:
            return 'video_4k', 0.95
        elif height >= 1080:
            return 'video_fullhd', 0.95
        elif height >= 720:
            return 'video_hd', 0.95
        
        return 'video_general', 0.7
    
    def _categorize_text(self, analysis: Dict[str, Any]) -> Tuple[str, float]:
        """Text file categorization."""
        # Check if it's code
        if analysis.get('is_code', False):
            return 'text_code', 0.9
        
        # Check if it's markdown
        if analysis.get('is_markdown', False):
            return 'text_markdown', 0.95
        
        # Check if it's a log
        if analysis.get('is_log', False):
            return 'text_log', 0.85
        
        # Default
        return 'text_document', 0.7
    
    def _extract_type_metadata(
        self, file_type: str, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract type-specific metadata from analysis."""
        metadata = {}
        
        if file_type == 'pdf':
            metadata.update({
                'page_count': analysis.get('page_count', 0),
                'text_length': analysis.get('text_length', 0),
                'image_count': analysis.get('image_count', 0),
                'is_scanned': analysis.get('is_scanned', False),
            })
        
        elif file_type == 'json':
            metadata.update({
                'record_count': analysis.get('record_count', 0),
                'field_consistency': analysis.get('field_consistency', 0),
                'max_depth': analysis.get('max_depth', 0),
                'shape': analysis.get('shape', 'unknown'),
            })
        
        elif file_type == 'image':
            metadata.update({
                'width': analysis.get('width', 0),
                'height': analysis.get('height', 0),
                'format': analysis.get('format', 'unknown'),
            })
        
        elif file_type == 'video':
            metadata.update({
                'duration': analysis.get('duration', 0),
                'width': analysis.get('width', 0),
                'height': analysis.get('height', 0),
                'fps': analysis.get('fps', 0),
            })
        
        return metadata


# ============================================================================
# Global classifier instance
# ============================================================================

_classifier = UnifiedClassifier()


def classify_file(
    filename: str,
    file_path: Optional[str] = None,
    mime_type: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Global classification function.
    SINGLE ENTRY POINT for all file classification.
    """
    return _classifier.classify_file(filename, file_path, mime_type, file_bytes, analysis)
