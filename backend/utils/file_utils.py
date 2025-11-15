import os
import shutil
from typing import Optional
from fastapi import UploadFile
import mimetypes
import re

def clean_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and security issues.
    
    Args:
        filename: Original filename (may contain folder paths)
    
    Returns:
        Sanitized filename (basename only, safe characters)
    """
    # Get basename only (remove any folder paths)
    basename = os.path.basename(filename)
    
    # Remove or replace unsafe characters
    # Keep alphanumeric, dots, hyphens, underscores
    safe_name = re.sub(r'[^\w\s\-\.]', '_', basename)
    
    # Remove leading/trailing whitespace and dots
    safe_name = safe_name.strip('. ')
    
    # Ensure it's not empty
    if not safe_name:
        safe_name = "unnamed_file"
    
    return safe_name

def normalize_extension(filename: str) -> str:
    """
    Extract and normalize file extension.
    
    Args:
        filename: Filename (may include path)
    
    Returns:
        Lowercase extension without dot (e.g., 'pdf' not '.pdf')
    """
    basename = os.path.basename(filename)
    _, ext = os.path.splitext(basename)
    return ext.lower().lstrip('.')

def detect_file_type_comprehensive(filename: str, mime_type: Optional[str] = None, file_bytes: Optional[bytes] = None) -> str:
    """
    COMPREHENSIVE file type detection using multiple methods.
    
    Detection priority:
    1. Magic bytes (file header)
    2. File extension (normalized)
    3. MIME type
    
    Args:
        filename: File name or path
        mime_type: Optional MIME type from upload
        file_bytes: Optional first 512 bytes for magic byte detection
    
    Returns:
        File type: 'json', 'pdf', 'image', 'text', 'video', 'unknown'
    """
    # METHOD 1: Magic bytes detection (most reliable)
    if file_bytes:
        # PDF magic bytes
        if file_bytes.startswith(b'%PDF'):
            return "pdf"
        # PNG magic bytes
        elif file_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            return "image"
        # JPEG magic bytes
        elif file_bytes.startswith(b'\xff\xd8\xff'):
            return "image"
        # GIF magic bytes
        elif file_bytes.startswith(b'GIF87a') or file_bytes.startswith(b'GIF89a'):
            return "image"
        # JSON detection (starts with { or [, allowing whitespace)
        stripped = file_bytes.lstrip()
        if stripped.startswith(b'{') or stripped.startswith(b'['):
            return "json"
    
    # METHOD 2: Extension-based detection (normalized, case-insensitive)
    ext = normalize_extension(filename)
    
    if ext == 'json':
        return "json"
    elif ext == 'pdf':
        return "pdf"
    elif ext in {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif', 'svg'}:
        return "image"
    elif ext in {'txt', 'md', 'csv', 'log', 'rtf'}:
        return "text"
    elif ext in {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv'}:
        return "video"
    
    # METHOD 3: MIME type fallback
    if mime_type:
        mime_lower = mime_type.lower()
        if 'pdf' in mime_lower:
            return "pdf"
        elif mime_lower.startswith('image/'):
            return "image"
        elif mime_lower.startswith('text/'):
            return "text"
        elif mime_lower.startswith('video/'):
            return "video"
        elif mime_lower.startswith('application/json'):
            return "json"
    
    # METHOD 4: Final MIME guess from filename
    guessed_mime, _ = mimetypes.guess_type(filename)
    if guessed_mime:
        if 'pdf' in guessed_mime:
            return "pdf"
        elif guessed_mime.startswith('image/'):
            return "image"
        elif guessed_mime.startswith('text/'):
            return "text"
        elif guessed_mime.startswith('video/'):
            return "video"
        elif guessed_mime.startswith('application/json'):
            return "json"
    
    return "unknown"

def get_file_type(filename: str, mime_type: Optional[str] = None) -> str:
    """
    Determine file type (backward compatibility wrapper).
    Use detect_file_type_comprehensive for full detection.
    """
    return detect_file_type_comprehensive(filename, mime_type, None)

def save_uploaded_file(file_content: bytes, filename: str, folder_id: str, base_path: str = None) -> str:
    """Save uploaded file content and return its path.
    
    Args:
        file_content: Raw bytes content of the file
        filename: Original filename (may contain folder paths)
        folder_id: Folder ID for organizing files (used as prefix)
        base_path: Base directory for uploads (defaults to root/data)
    
    Returns:
        Full path to the saved file
    """
    # Default to root/data directory
    if base_path is None:
        # __file__ is backend/utils/file_utils.py
        utils_dir = os.path.dirname(os.path.abspath(__file__))  # backend/utils
        backend_dir = os.path.dirname(utils_dir)  # backend
        root_dir = os.path.dirname(backend_dir)  # root
        base_path = os.path.join(root_dir, "data")
    
    # Sanitize filename to prevent path traversal and nested folder issues
    safe_filename = clean_filename(filename)
    
    uploads_path = os.path.join(base_path, "raw", "uploads")
    os.makedirs(uploads_path, exist_ok=True)
    
    # Generate unique filename with original extension
    ext = os.path.splitext(safe_filename)[1]
    base_name = os.path.splitext(safe_filename)[0]
    unique_filename = f"{folder_id}_{base_name}{ext}"
    file_path = os.path.join(uploads_path, unique_filename)
    
    # Ensure the directory exists (defensive)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write bytes directly to file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return file_path

async def save_upload_file(file: UploadFile, file_id: str, base_path: str = None) -> str:
    """Save an UploadFile object and return its path.
    
    Args:
        file: FastAPI UploadFile object
        file_id: Unique identifier for the file
        base_path: Base directory for uploads (defaults to root/data)
    
    Returns:
        Full path to the saved file
    """
    # Default to root/data directory
    if base_path is None:
        # __file__ is backend/utils/file_utils.py
        utils_dir = os.path.dirname(os.path.abspath(__file__))  # backend/utils
        backend_dir = os.path.dirname(utils_dir)  # backend
        root_dir = os.path.dirname(backend_dir)  # root
        base_path = os.path.join(root_dir, "data")
    
    # Sanitize filename to prevent issues with folder paths
    safe_filename = clean_filename(file.filename)
    
    uploads_path = os.path.join(base_path, "raw", "uploads")
    os.makedirs(uploads_path, exist_ok=True)
    
    ext = os.path.splitext(safe_filename)[1]
    filename = f"{file_id}{ext}"
    file_path = os.path.join(uploads_path, filename)
    
    # Ensure directory exists (defensive)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Read content and write to file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    return file_path

def get_file_size_category(size_bytes: int) -> str:
    """Categorize file size."""
    if size_bytes < 1024:
        return "tiny"
    elif size_bytes < 1024 * 1024:
        return "small"
    elif size_bytes < 10 * 1024 * 1024:
        return "medium"
    elif size_bytes < 100 * 1024 * 1024:
        return "large"
    else:
        return "very_large"

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def is_safe_path(base_path: str, target_path: str) -> bool:
    """Check if target path is within base path (prevent directory traversal)."""
    base = os.path.abspath(base_path)
    target = os.path.abspath(target_path)
    return target.startswith(base)
