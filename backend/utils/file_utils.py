import os
import shutil
from typing import Optional
from fastapi import UploadFile
import mimetypes

def get_file_type(filename: str) -> str:
    """Determine file type based on extension."""
    ext = os.path.splitext(filename)[1].lower()
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    text_extensions = {'.txt', '.md', '.csv', '.log', '.rtf'}
    json_extensions = {'.json'}
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    
    if ext in json_extensions:
        return "json"
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

def save_uploaded_file(file: UploadFile, file_id: str, base_path: str = "data") -> str:
    """Save an uploaded file and return its path."""
    uploads_path = os.path.join(base_path, "raw", "uploads")
    os.makedirs(uploads_path, exist_ok=True)
    
    ext = os.path.splitext(file.filename)[1]
    filename = f"{file_id}{ext}"
    file_path = os.path.join(uploads_path, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
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
