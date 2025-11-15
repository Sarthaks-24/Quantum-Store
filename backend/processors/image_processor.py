from PIL import Image
import imagehash
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
from sklearn.cluster import KMeans
import cv2
import os

class ImageProcessor:
    def __init__(self):
        self.reasoning_log = []
    
    def analyze(self, file_path: str) -> Dict[str, Any]:
        self.reasoning_log = []
        self.log_reasoning("Starting image analysis")
        
        try:
            img = Image.open(file_path)
            img_array = np.array(img)
        except Exception as e:
            return {"error": f"Failed to load image: {str(e)}"}
        
        basic_info = self._get_basic_info(img, file_path)
        colors = self._analyze_colors(img_array)
        quality_metrics = self._analyze_quality(img_array)
        phash = self._calculate_phash(img)
        histogram = self._calculate_histogram(img_array)
        category = self._categorize_image(img, img_array, basic_info, colors, quality_metrics)
        
        # Add content_category for Layer 2 categorization
        content_category = self._determine_content_category(img, basic_info, category)
        
        return {
            **basic_info,
            "colors": colors,
            "quality": quality_metrics,
            "phash": phash,
            "histogram": histogram,
            "category": category,
            "content_category": content_category,
            "reasoning_log": self.reasoning_log
        }
    
    def _get_basic_info(self, img: Image.Image, file_path: str) -> Dict[str, Any]:
        width, height = img.size
        aspect_ratio = width / height if height > 0 else 0
        
        info = {
            "format": img.format,
            "mode": img.mode,
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "has_alpha": img.mode in ('RGBA', 'LA', 'PA'),
            "file_size": os.path.getsize(file_path)
        }
        
        try:
            exif = img._getexif()
            info["has_exif"] = exif is not None and len(exif) > 0
        except:
            info["has_exif"] = False
        
        self.log_reasoning(
            f"Image: {width}x{height}, format={img.format}, mode={img.mode}, "
            f"alpha={info['has_alpha']}, exif={info['has_exif']}"
        )
        
        return info
    
    def _analyze_colors(self, img_array: np.ndarray) -> Dict[str, Any]:
        if len(img_array.shape) == 2:
            self.log_reasoning("Grayscale image detected")
            return {
                "dominant_colors": [],
                "color_variance": float(np.var(img_array)),
                "is_grayscale": True
            }
        
        if img_array.shape[2] == 4:
            img_rgb = img_array[:, :, :3]
        else:
            img_rgb = img_array
        
        pixels = img_rgb.reshape(-1, 3)
        
        n_colors = min(5, len(pixels))
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        colors = kmeans.cluster_centers_
        labels = kmeans.labels_
        
        counts = np.bincount(labels)
        percentages = counts / len(labels)
        
        dominant_colors = []
        for i in range(n_colors):
            color = colors[i]
            dominant_colors.append({
                "rgb": [int(c) for c in color],
                "hex": "#{:02x}{:02x}{:02x}".format(int(color[0]), int(color[1]), int(color[2])),
                "percentage": float(percentages[i])
            })
        
        dominant_colors.sort(key=lambda x: x["percentage"], reverse=True)
        
        color_variance = float(np.var(pixels))
        
        self.log_reasoning(
            f"Extracted {n_colors} dominant colors, color_variance={color_variance:.2f}"
        )
        
        return {
            "dominant_colors": dominant_colors,
            "color_variance": color_variance,
            "is_grayscale": False
        }
    
    def _analyze_quality(self, img_array: np.ndarray) -> Dict[str, Any]:
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        brightness = float(np.mean(gray))
        
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = float(np.var(laplacian))
        
        edges = cv2.Canny(gray, 100, 200)
        edge_density = float(np.sum(edges > 0) / edges.size)
        
        self.log_reasoning(
            f"Quality metrics: brightness={brightness:.1f}, sharpness={sharpness:.1f}, "
            f"edge_density={edge_density:.3f}"
        )
        
        return {
            "brightness": brightness,
            "sharpness": sharpness,
            "edge_density": edge_density
        }
    
    def _calculate_phash(self, img: Image.Image) -> str:
        phash = str(imagehash.phash(img))
        self.log_reasoning(f"Perceptual hash: {phash}")
        return phash
    
    def _calculate_histogram(self, img_array: np.ndarray) -> Dict[str, List[int]]:
        if len(img_array.shape) == 2:
            hist, _ = np.histogram(img_array, bins=16, range=(0, 256))
            return {"gray": hist.tolist()}
        
        if img_array.shape[2] >= 3:
            hist_r, _ = np.histogram(img_array[:, :, 0], bins=16, range=(0, 256))
            hist_g, _ = np.histogram(img_array[:, :, 1], bins=16, range=(0, 256))
            hist_b, _ = np.histogram(img_array[:, :, 2], bins=16, range=(0, 256))
            
            return {
                "red": hist_r.tolist(),
                "green": hist_g.tolist(),
                "blue": hist_b.tolist()
            }
        
        return {}
    
    def _categorize_image(
        self,
        img: Image.Image,
        img_array: np.ndarray,
        basic_info: Dict,
        colors: Dict,
        quality: Dict
    ) -> Dict[str, Any]:
        self.log_reasoning("Applying heuristic-based categorization")
        
        category = "unknown"
        confidence = 0.0
        reasons = []
        
        is_logo = False
        is_screenshot = False
        is_photo = False
        
        if basic_info["has_alpha"] and basic_info["format"] == "PNG":
            is_logo = True
            reasons.append("Has transparency (alpha channel)")
        
        if colors.get("color_variance", 0) < 1000:
            is_logo = True
            reasons.append("Low color variance suggests simple graphic")
        
        if quality["sharpness"] > 1000 and quality["edge_density"] > 0.1:
            is_screenshot = True
            reasons.append("High sharpness and edge density")
        
        if basic_info.get("has_exif"):
            is_photo = True
            reasons.append("Contains EXIF metadata (likely from camera)")
        
        if colors.get("color_variance", 0) > 3000:
            is_photo = True
            reasons.append("High color variance suggests natural photo")
        
        if is_logo and not is_photo:
            category = "logo"
            confidence = 0.7
        elif is_screenshot and not is_photo:
            category = "screenshot"
            confidence = 0.65
        elif is_photo:
            category = "photo"
            confidence = 0.75
        else:
            category = "graphic"
            confidence = 0.5
        
        self.log_reasoning(f"Categorized as '{category}' with confidence {confidence:.2f}")
        
        return {
            "category": category,
            "confidence": confidence,
            "reasons": reasons
        }
    
    def calculate_similarity(self, phash1: str, phash2: str) -> float:
        hash1 = imagehash.hex_to_hash(phash1)
        hash2 = imagehash.hex_to_hash(phash2)
        
        distance = hash1 - hash2
        
        similarity = 1 - (distance / 64.0)
        
        return max(0.0, similarity)
    
    def log_reasoning(self, message: str):
        timestamp = datetime.utcnow().isoformat()
        self.reasoning_log.append(f"[{timestamp}] {message}")
    
    def _determine_content_category(
        self,
        img: Image.Image,
        basic_info: Dict[str, Any],
        category_info: Dict[str, Any]
    ) -> str:
        """
        Determine content category for Layer 2 categorization.
        
        Returns one of:
        - images_portrait: Portrait photos
        - images_screenshot: Screenshots
        - images_graphics: Graphics/illustrations
        - images_photos: General photos
        - images_landscape: Landscape orientation
        """
        width = basic_info.get("width", 0)
        height = basic_info.get("height", 0)
        aspect_ratio = basic_info.get("aspect_ratio", 1.0)
        
        # Get the basic category from existing analysis
        basic_category = category_info.get("category", "unknown")
        
        # Screenshot detection
        if basic_category == "screenshot":
            return "images_screenshot"
        
        # Graphics/logos
        if basic_category in ["logo", "graphic"]:
            return "images_graphics"
        
        # Photo categorization
        if basic_category == "photo":
            # Portrait vs landscape
            if aspect_ratio < 0.8:  # Taller than wide
                return "images_portrait"
            else:
                return "images_landscape"
        
        # Default fallback
        if aspect_ratio < 0.8:
            return "images_portrait"
        elif basic_info.get("has_exif", False):
            return "images_photos"
        else:
            return "images_graphics"
