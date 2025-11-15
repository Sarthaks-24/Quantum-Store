import os
import shutil
from typing import Optional
from fastapi import UploadFile
import mimetypes

def clean_filename(filename: str) -> str:
    """Clean filename by removing path separators and getting basename.
    
    Args:
        filename: Original filename (may contain folder paths like 'Nearby Share/file.txt')
    
    Returns:
        Sanitized filename with path separators replaced by underscores
    
    Examples:
        'Nearby Share/IMG.jpg' -> 'Nearby Share_IMG.jpg'
        'folder\\subfolder\\file.txt' -> 'folder_subfolder_file.txt'
    """
    # First, get just the basename to avoid nested folders
    basename = os.path.basename(filename)
    
    # Also replace any remaining path separators with underscores
    sanitized = basename.replace("/", "_").replace("\\", "_")
    
    # Remove any potentially dangerous characters
    sanitized = sanitized.replace("..", "_")
    
    return sanitized

def get_file_type(filename: str) -> str:
    """Determine file type based on extension."""
    ext = os.path.splitext(filename)[1].lower()
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    text_extensions = {'.txt', '.md', '.csv', '.log', '.rtf'}
    json_extensions = {'.json'}
    pdf_extensions = {'.pdf'}
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    
    if ext in json_extensions:
        return "json"
    elif ext in pdf_extensions:
        return "pdf"
    elif ext in image_extensions:
        return "image"
    elif ext in text_extensions:
        return "text"
    elif ext in video_extensions:
        return "video"
    else:
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            if mime_type.startswith('image/'):
                return "image"
            elif mime_type.startswith('text/'):
                return "text"
            elif mime_type.startswith('video/'):
                return "video"
        
        return "unknown"

def save_uploaded_file(file_content: bytes, filename: str, folder_id: str, base_path: str = "data") -> str:
    """Save uploaded file content and return its path.
    
    Args:
        file_content: Raw bytes content of the file
        filename: Original filename (may contain folder paths)
        folder_id: Folder ID for organizing files (used as prefix)
        base_path: Base directory for uploads
    
    Returns:
        Full path to the saved file
    """
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

async def save_upload_file(file: UploadFile, file_id: str, base_path: str = "data") -> str:
    """Save an UploadFile object and return its path.
    
    Args:
        file: FastAPI UploadFile object
        file_id: Unique identifier for the file
        base_path: Base directory for uploads
    
    Returns:
        Full path to the saved file
    """
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
