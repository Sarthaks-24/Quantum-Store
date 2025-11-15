"""
Categorization System - Three-Layer File Categorization
========================================================

LAYER 1: Extension-based fallback categories (always returns a category)
LAYER 2: Content-based categories (set by individual processors)
LAYER 3: Final category assignment (content takes precedence)
"""

import os
from typing import Optional, Dict, Any


# ============================================================================
# LAYER 1: Extension-Based Fallback Categories
# ============================================================================

EXTENSION_CATEGORY_MAP = {
    # Documents
    '.pdf': 'pdf_docs',
    '.doc': 'word_docs',
    '.docx': 'word_docs',
    '.txt': 'text_docs',
    '.md': 'markdown_docs',
    '.rtf': 'text_docs',
    
    # Data formats
    '.json': 'json_files',
    '.csv': 'csv_tables',
    '.xlsx': 'excel_sheets',
    '.xls': 'excel_sheets',
    '.xml': 'xml_files',
    '.yaml': 'yaml_files',
    '.yml': 'yaml_files',
    
    # Images
    '.jpg': 'images',
    '.jpeg': 'images',
    '.png': 'images',
    '.gif': 'images',
    '.bmp': 'images',
    '.svg': 'images',
    '.webp': 'images',
    '.tiff': 'images',
    '.tif': 'images',
    
    # Audio
    '.mp3': 'audio',
    '.m4a': 'audio',
    '.wav': 'audio',
    '.flac': 'audio',
    '.aac': 'audio',
    '.ogg': 'audio',
    '.wma': 'audio',
    
    # Video
    '.mp4': 'videos',
    '.mov': 'videos',
    '.avi': 'videos',
    '.mkv': 'videos',
    '.wmv': 'videos',
    '.flv': 'videos',
    '.webm': 'videos',
    
    # Code/Scripts
    '.py': 'python_scripts',
    '.js': 'javascript_scripts',
    '.ts': 'typescript_scripts',
    '.cpp': 'cpp_sources',
    '.c': 'cpp_sources',
    '.h': 'cpp_sources',
    '.hpp': 'cpp_sources',
    '.java': 'java_sources',
    '.go': 'go_sources',
    '.rs': 'rust_sources',
    '.rb': 'ruby_scripts',
    '.php': 'php_scripts',
    
    # Web
    '.html': 'web_source',
    '.htm': 'web_source',
    '.css': 'web_source',
    '.scss': 'web_source',
    '.sass': 'web_source',
    '.less': 'web_source',
    
    # Archives
    '.zip': 'archives',
    '.tar': 'archives',
    '.gz': 'archives',
    '.rar': 'archives',
    '.7z': 'archives',
}


def categorize_by_extension(filename: str) -> str:
    """
    LAYER 1: Categorize file based on extension.
    This ALWAYS returns a category - no file is left uncategorized.
    
    Args:
        filename: Name of the file (can be full path)
    
    Returns:
        Extension-based category (e.g., 'pdf_docs', 'images', 'other_txt')
    """
    # Extract extension
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    
    # Check known extensions
    if ext in EXTENSION_CATEGORY_MAP:
        return EXTENSION_CATEGORY_MAP[ext]
    
    # Unknown extension - create dynamic category
    if ext:
        # Remove the dot and create category like 'other_dat', 'other_bin'
        return f"other_{ext[1:]}"
    else:
        # No extension at all
        return "other_no_extension"


# ============================================================================
# LAYER 2: Content-Based Categories (Defined by Each Processor)
# ============================================================================

# PDF Content Categories
PDF_CONTENT_CATEGORIES = {
    'pdf_empty',           # No extractable content
    'pdf_scanned',         # Scanned document (OCR used)
    'pdf_text_heavy',      # Primarily text
    'pdf_financial',       # Financial keywords, tables
    'pdf_report',          # Structured report
    'pdf_academic',        # Academic paper with citations
    'pdf_mixed',           # Mix of images and text
    'pdf_forms',           # Has form fields
}

# JSON Content Categories
JSON_CONTENT_CATEGORIES = {
    'json_structured_sql',        # Perfect for SQL (flat, consistent)
    'json_structured_small_sql',  # Small structured dataset
    'json_semi_structured',       # 60-95% field consistency
    'json_nested',                # Nested objects, NoSQL better
    'json_deep_nested',           # >3 levels deep
    'json_mixed',                 # Heterogeneous/inconsistent
    'json_plain_object',          # Single object
    'json_scalar',                # Single value
    'json_array_of_scalars',      # Simple array of primitives
}

# Image Content Categories
IMAGE_CONTENT_CATEGORIES = {
    'images_portrait',    # Portrait photos
    'images_screenshot',  # Screenshots
    'images_graphics',    # Graphics/illustrations
    'images_photos',      # General photos
    'images_landscape',   # Landscape orientation
}

# Video Content Categories
VIDEO_CONTENT_CATEGORIES = {
    'videos_short',    # < 2 minutes
    'videos_medium',   # 2-10 minutes
    'videos_long',     # > 10 minutes
    'videos_hd',       # 720p
    'videos_fullhd',   # 1080p
    'videos_4k',       # 2160p+
}

# Audio Content Categories
AUDIO_CONTENT_CATEGORIES = {
    'audio_music',     # Music tracks
    'audio_raw',       # Raw audio
    'audio_podcast',   # Podcast/voice
    'audio_longform',  # Long recordings
}

# Text Content Categories
TEXT_CONTENT_CATEGORIES = {
    'text_docs',       # Plain text
    'markdown_docs',   # Markdown files
    'code_docs',       # Code documentation
    'logs',            # Log files
}

# All valid content categories
ALL_CONTENT_CATEGORIES = (
    PDF_CONTENT_CATEGORIES |
    JSON_CONTENT_CATEGORIES |
    IMAGE_CONTENT_CATEGORIES |
    VIDEO_CONTENT_CATEGORIES |
    AUDIO_CONTENT_CATEGORIES |
    TEXT_CONTENT_CATEGORIES
)


def validate_content_category(category: Optional[str]) -> bool:
    """
    Validate that a content category is recognized.
    
    Args:
        category: Content category to validate
    
    Returns:
        True if valid, False otherwise
    """
    if category is None:
        return True  # None is valid (means no content category assigned)
    return category in ALL_CONTENT_CATEGORIES


# ============================================================================
# LAYER 3: Final Category Assignment
# ============================================================================

def assign_final_category(
    extension_category: str,
    content_category: Optional[str] = None
) -> str:
    """
    LAYER 3: Assign final category with content taking precedence.
    
    Priority:
    1. If content_category is set and valid, use it
    2. Otherwise, fall back to extension_category
    
    Args:
        extension_category: Category from Layer 1 (extension-based)
        content_category: Category from Layer 2 (content-based), can be None
    
    Returns:
        Final category string (guaranteed to be non-empty)
    """
    # Validate inputs
    if not extension_category:
        raise ValueError("extension_category cannot be empty")
    
    # Content category takes precedence if it exists and is valid
    if content_category and validate_content_category(content_category):
        return content_category
    
    # Fall back to extension category
    return extension_category


def get_category_display_name(category: str) -> str:
    """
    Convert category identifier to human-readable display name.
    
    Args:
        category: Category identifier (e.g., 'pdf_scanned', 'json_flat_structured')
    
    Returns:
        Human-readable display name (e.g., 'PDF - Scanned', 'JSON - Flat Structured')
    """
    # Special cases
    display_map = {
        'pdf_docs': 'PDF Documents',
        'word_docs': 'Word Documents',
        'text_docs': 'Text Files',
        'markdown_docs': 'Markdown Files',
        'json_files': 'JSON Files',
        'csv_tables': 'CSV Tables',
        'excel_sheets': 'Excel Sheets',
        'images': 'Images',
        'audio': 'Audio Files',
        'videos': 'Videos',
        'python_scripts': 'Python Scripts',
        'javascript_scripts': 'JavaScript Scripts',
        'typescript_scripts': 'TypeScript Scripts',
        'cpp_sources': 'C/C++ Sources',
        'java_sources': 'Java Sources',
        'web_source': 'Web Files',
        'archives': 'Archives',
    }
    
    # Check if we have a special mapping
    if category in display_map:
        return display_map[category]
    
    # Content-based categories - convert underscore to readable format
    if category.startswith('pdf_'):
        return f"PDF - {category[4:].replace('_', ' ').title()}"
    elif category.startswith('json_'):
        return f"JSON - {category[5:].replace('_', ' ').title()}"
    elif category.startswith('images_'):
        return f"Images - {category[7:].replace('_', ' ').title()}"
    elif category.startswith('videos_'):
        return f"Videos - {category[7:].replace('_', ' ').title()}"
    elif category.startswith('audio_'):
        return f"Audio - {category[6:].replace('_', ' ').title()}"
    elif category.startswith('other_'):
        ext = category[6:]
        return f"Other - .{ext}"
    
    # Default: just title case with underscores replaced
    return category.replace('_', ' ').title()


def categorize_file(
    filename: str,
    content_category: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Complete categorization workflow for a file.
    
    Args:
        filename: Name of the file
        content_category: Content-based category from processor (optional)
        metadata: Additional metadata that might influence categorization
    
    Returns:
        Dictionary with categorization details:
        {
            'extension_category': str,
            'content_category': str or None,
            'final_category': str,
            'display_name': str
        }
    """
    # Layer 1: Extension-based
    extension_category = categorize_by_extension(filename)
    
    # Layer 3: Final assignment
    final_category = assign_final_category(extension_category, content_category)
    
    # Get display name
    display_name = get_category_display_name(final_category)
    
    return {
        'extension_category': extension_category,
        'content_category': content_category,
        'final_category': final_category,
        'display_name': display_name
    }
