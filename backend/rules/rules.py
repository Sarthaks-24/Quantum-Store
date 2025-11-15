from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict

class RuleEngine:
    def __init__(self):
        self.reasoning_log = []
    
    def auto_group_files(self, files: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        self.reasoning_log = []
        self.log_reasoning("Starting automatic file grouping")
        
        groups = defaultdict(list)
        
        for file in files:
            file_type = file.get("file_type", "unknown")
            analysis = file.get("analysis", {})
            
            if file_type == "image":
                image_category = self._get_image_category(analysis)
                groups[f"images_{image_category}"].append(file)
                self.log_reasoning(
                    f"File {file.get('filename')} grouped as image/{image_category}"
                )
            
            elif file_type == "json":
                schema_type = self._get_schema_type(analysis)
                groups[f"json_{schema_type}"].append(file)
                self.log_reasoning(
                    f"File {file.get('filename')} grouped as json/{schema_type}"
                )
            
            elif file_type == "text":
                text_category = self._get_text_category(analysis)
                groups[f"text_{text_category}"].append(file)
                self.log_reasoning(
                    f"File {file.get('filename')} grouped as text/{text_category}"
                )
            
            else:
                groups["uncategorized"].append(file)
        
        similar_groups = self._find_similar_files(files)
        for group_name, group_files in similar_groups.items():
            groups[group_name] = group_files
        
        return dict(groups)
    
    def _get_image_category(self, analysis: Dict) -> str:
        image_analysis = analysis.get("image", {})
        category_info = image_analysis.get("category", {})
        
        if isinstance(category_info, dict):
            return category_info.get("category", "unknown")
        return "unknown"
    
    def _get_schema_type(self, analysis: Dict) -> str:
        json_analysis = analysis.get("json", {})
        schema = json_analysis.get("schema", {})
        
        if not schema:
            return "unknown"
        
        field_names = set(schema.keys())
        
        if "user_id" in field_names or "username" in field_names:
            return "user_data"
        elif "product_id" in field_names or "price" in field_names:
            return "product_data"
        elif "timestamp" in field_names or "created_at" in field_names:
            return "time_series"
        else:
            return "general"
    
    def _get_text_category(self, analysis: Dict) -> str:
        text_analysis = analysis.get("text", {})
        readability = text_analysis.get("readability", {})
        
        level = readability.get("level", "unknown")
        
        if level in ["very_easy", "easy"]:
            return "simple"
        elif level in ["standard", "fairly_easy"]:
            return "standard"
        elif level in ["difficult", "very_difficult", "fairly_difficult"]:
            return "technical"
        
        return "unknown"
    
    def _find_similar_files(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        similar_groups = {}
        
        image_files = [f for f in files if f.get("file_type") == "image"]
        if len(image_files) > 1:
            phash_groups = self._group_by_phash(image_files)
            for idx, group in enumerate(phash_groups):
                if len(group) > 1:
                    similar_groups[f"similar_images_{idx}"] = group
                    self.log_reasoning(
                        f"Found {len(group)} similar images based on perceptual hash"
                    )
        
        text_files = [f for f in files if f.get("file_type") == "text"]
        if len(text_files) > 1:
            tfidf_groups = self._group_by_content(text_files)
            for idx, group in enumerate(tfidf_groups):
                if len(group) > 1:
                    similar_groups[f"similar_texts_{idx}"] = group
                    self.log_reasoning(
                        f"Found {len(group)} similar text files based on content"
                    )
        
        return similar_groups
    
    def _group_by_phash(self, image_files: List[Dict]) -> List[List[Dict]]:
        groups = []
        processed = set()
        
        for i, file1 in enumerate(image_files):
            if i in processed:
                continue
            
            phash1 = file1.get("analysis", {}).get("image", {}).get("phash")
            if not phash1:
                continue
            
            group = [file1]
            processed.add(i)
            
            for j, file2 in enumerate(image_files[i+1:], start=i+1):
                if j in processed:
                    continue
                
                phash2 = file2.get("analysis", {}).get("image", {}).get("phash")
                if not phash2:
                    continue
                
                similarity = self._phash_similarity(phash1, phash2)
                
                if similarity > 0.9:
                    group.append(file2)
                    processed.add(j)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def _phash_similarity(self, phash1: str, phash2: str) -> float:
        if len(phash1) != len(phash2):
            return 0.0
        
        hamming = sum(c1 != c2 for c1, c2 in zip(phash1, phash2))
        similarity = 1 - (hamming / len(phash1))
        
        return similarity
    
    def _group_by_content(self, text_files: List[Dict]) -> List[List[Dict]]:
        groups = []
        processed = set()
        
        for i, file1 in enumerate(text_files):
            if i in processed:
                continue
            
            group = [file1]
            processed.add(i)
            
            for j, file2 in enumerate(text_files[i+1:], start=i+1):
                if j in processed:
                    continue
                
                similarity = self._text_similarity(file1, file2)
                
                if similarity > 0.7:
                    group.append(file2)
                    processed.add(j)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def _text_similarity(self, file1: Dict, file2: Dict) -> float:
        analysis1 = file1.get("analysis", {}).get("text", {})
        analysis2 = file2.get("analysis", {}).get("text", {})
        
        tfidf1 = analysis1.get("tfidf", {})
        tfidf2 = analysis2.get("tfidf", {})
        
        if not tfidf1 or not tfidf2:
            return 0.0
        
        similarities1 = tfidf1.get("similarities", [])
        
        for sim in similarities1:
            if sim.get("document_index") == file2.get("id"):
                return sim.get("similarity", 0.0)
        
        return 0.0
    
    def apply_schema_matching_rule(self, schema1: Dict, schema2: Dict) -> Dict[str, Any]:
        self.log_reasoning("Applying schema matching rules")
        
        fields1 = set(schema1.keys())
        fields2 = set(schema2.keys())
        
        common_fields = fields1 & fields2
        unique_to_1 = fields1 - fields2
        unique_to_2 = fields2 - fields1
        
        similarity = len(common_fields) / len(fields1 | fields2) if fields1 | fields2 else 0
        
        conflicts = []
        for field in common_fields:
            type1 = schema1[field].get("type")
            type2 = schema2[field].get("type")
            
            if type1 != type2:
                conflicts.append({
                    "field": field,
                    "type1": type1,
                    "type2": type2,
                    "resolution": self._resolve_type_conflict(type1, type2)
                })
                self.log_reasoning(
                    f"Type conflict in field '{field}': {type1} vs {type2}"
                )
        
        return {
            "similarity": similarity,
            "common_fields": list(common_fields),
            "unique_to_schema1": list(unique_to_1),
            "unique_to_schema2": list(unique_to_2),
            "conflicts": conflicts
        }
    
    def _resolve_type_conflict(self, type1: str, type2: str) -> str:
        if type1 == type2:
            return type1
        
        type_hierarchy = ["null", "bool", "int", "float", "string", "date", "array", "object"]
        
        try:
            idx1 = type_hierarchy.index(type1)
            idx2 = type_hierarchy.index(type2)
            return type_hierarchy[max(idx1, idx2)]
        except ValueError:
            return "string"
    
    def get_last_reasoning_log(self) -> List[str]:
        return self.reasoning_log
    
    def log_reasoning(self, message: str):
        timestamp = datetime.utcnow().isoformat()
        self.reasoning_log.append(f"[{timestamp}] {message}")
