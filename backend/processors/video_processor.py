"""
Video Processor Module
======================
Handles video file processing and analysis.

This module handles:
- Video metadata extraction
- Duration and format detection
- Resolution categorization
- Content categorization
"""

import os
from typing import Dict, Any, Optional

class VideoProcessor:
    def __init__(self):
        self.reasoning_log = []
    
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze video file and extract metadata.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Dictionary containing video metadata and analysis results
        """
        self.reasoning_log = []
        self.log_reasoning("Starting video analysis")
        
        try:
            # Try to use cv2 for basic video info
            import cv2
            
            cap = cv2.VideoCapture(file_path)
            
            if not cap.isOpened():
                return self._fallback_analysis(file_path)
            
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate duration
            duration_seconds = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Determine content categories
            content_category = self._categorize_video_content(
                duration_seconds=duration_seconds,
                width=width,
                height=height
            )
            
            self.log_reasoning(
                f"Video analyzed: {width}x{height}, {duration_seconds:.1f}s, "
                f"{fps:.1f} fps, category={content_category}"
            )
            
            return {
                "type": "video",
                "width": width,
                "height": height,
                "fps": fps,
                "frame_count": frame_count,
                "duration_seconds": duration_seconds,
                "duration_formatted": self._format_duration(duration_seconds),
                "file_size": file_size,
                "content_category": content_category,
                "reasoning_log": self.reasoning_log,
                "processed": True
            }
            
        except ImportError:
            self.log_reasoning("OpenCV not available, using fallback analysis")
            return self._fallback_analysis(file_path)
        except Exception as e:
            self.log_reasoning(f"Error analyzing video: {str(e)}")
            return self._fallback_analysis(file_path)
    
    def _fallback_analysis(self, file_path: str) -> Dict[str, Any]:
        """Fallback analysis when cv2 is not available."""
        file_size = os.path.getsize(file_path)
        
        # Basic categorization based on file size
        # Rough estimate: larger files are likely longer or higher quality
        if file_size > 500 * 1024 * 1024:  # > 500MB
            content_category = "videos_long"
        elif file_size > 100 * 1024 * 1024:  # > 100MB
            content_category = "videos_medium"
        else:
            content_category = "videos_short"
        
        return {
            "type": "video",
            "file_size": file_size,
            "content_category": content_category,
            "processed": False,
            "message": "Basic analysis only (OpenCV not available)",
            "reasoning_log": self.reasoning_log
        }
    
    def _categorize_video_content(
        self,
        duration_seconds: float,
        width: int,
        height: int
    ) -> str:
        """
        Categorize video based on duration and resolution.
        
        Returns one of:
        - videos_short: < 2 minutes
        - videos_medium: 2-10 minutes
        - videos_long: > 10 minutes
        - videos_hd: 720p
        - videos_fullhd: 1080p
        - videos_4k: 2160p+
        """
        # Resolution-based categorization takes precedence for high-res videos
        resolution = min(width, height)  # Use smaller dimension
        
        if height >= 2160:  # 4K
            return "videos_4k"
        elif height >= 1080:  # Full HD
            return "videos_fullhd"
        elif height >= 720:  # HD
            return "videos_hd"
        
        # Duration-based categorization for lower resolutions
        if duration_seconds < 120:  # < 2 minutes
            return "videos_short"
        elif duration_seconds < 600:  # < 10 minutes
            return "videos_medium"
        else:
            return "videos_long"
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def log_reasoning(self, message: str):
        """Add reasoning log entry."""
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        self.reasoning_log.append(f"[{timestamp}] {message}")
