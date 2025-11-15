import re
from typing import List, Dict, Any
from collections import Counter
import math
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class TextProcessor:
    def __init__(self):
        self.reasoning_log = []
    
    def analyze(self, file_path: str, corpus_paths: List[str] = None) -> Dict[str, Any]:
        self.reasoning_log = []
        self.log_reasoning("Starting text analysis")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            return {"error": f"Failed to read text file: {str(e)}"}
        
        tokens = self._tokenize(text)
        
        # Determine content category
        content_category = self._determine_content_category(file_path, text, tokens)
        
        analysis = {
            "char_count": len(text),
            "word_count": len(tokens),
            "line_count": text.count('\n') + 1,
            "tokens": {
                "total": len(tokens),
                "unique": len(set(tokens)),
                "top_20": self._get_top_tokens(tokens, 20)
            },
            "readability": self._calculate_readability(text, tokens),
            "content_category": content_category,
            "reasoning_log": self.reasoning_log
        }
        
        if corpus_paths:
            self.log_reasoning(f"Building TF-IDF vectors from corpus of {len(corpus_paths)} documents")
            tfidf_data = self._calculate_tfidf([file_path] + corpus_paths)
            analysis["tfidf"] = tfidf_data
        
        return analysis
    
    def _tokenize(self, text: str) -> List[str]:
        text_lower = text.lower()
        tokens = re.findall(r'\b[a-z]+\b', text_lower)
        self.log_reasoning(f"Tokenized text into {len(tokens)} tokens")
        return tokens
    
    def _get_top_tokens(self, tokens: List[str], n: int) -> List[Dict[str, Any]]:
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'that',
            'this', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        filtered_tokens = [t for t in tokens if t not in stopwords and len(t) > 2]
        
        counter = Counter(filtered_tokens)
        top_tokens = []
        
        for token, count in counter.most_common(n):
            top_tokens.append({
                "token": token,
                "count": count,
                "frequency": count / len(tokens) if tokens else 0
            })
        
        self.log_reasoning(f"Extracted top {len(top_tokens)} meaningful tokens")
        return top_tokens
    
    def _calculate_readability(self, text: str, tokens: List[str]) -> Dict[str, Any]:
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences or not tokens:
            return {"score": 0, "level": "unknown"}
        
        avg_sentence_length = len(tokens) / len(sentences)
        
        long_words = [w for w in tokens if len(w) > 6]
        complex_word_ratio = len(long_words) / len(tokens) if tokens else 0
        
        score = 206.835 - 1.015 * avg_sentence_length - 84.6 * complex_word_ratio
        
        if score >= 90:
            level = "very_easy"
        elif score >= 80:
            level = "easy"
        elif score >= 70:
            level = "fairly_easy"
        elif score >= 60:
            level = "standard"
        elif score >= 50:
            level = "fairly_difficult"
        elif score >= 30:
            level = "difficult"
        else:
            level = "very_difficult"
        
        self.log_reasoning(
            f"Readability: score={score:.1f}, level={level}, "
            f"avg_sentence_length={avg_sentence_length:.1f}"
        )
        
        return {
            "score": score,
            "level": level,
            "avg_sentence_length": avg_sentence_length,
            "complex_word_ratio": complex_word_ratio
        }
    
    def _calculate_tfidf(self, file_paths: List[str]) -> Dict[str, Any]:
        documents = []
        for path in file_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    documents.append(f.read())
            except:
                documents.append("")
        
        if len(documents) < 2:
            return {}
        
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            lowercase=True,
            token_pattern=r'\b[a-z]+\b'
        )
        
        tfidf_matrix = vectorizer.fit_transform(documents)
        feature_names = vectorizer.get_feature_names_out()
        
        target_vector = tfidf_matrix[0].toarray()[0]
        top_indices = target_vector.argsort()[-20:][::-1]
        
        top_terms = []
        for idx in top_indices:
            if target_vector[idx] > 0:
                top_terms.append({
                    "term": feature_names[idx],
                    "tfidf_score": float(target_vector[idx])
                })
        
        self.log_reasoning(f"Calculated TF-IDF vectors with {len(feature_names)} features")
        
        similarities = []
        if len(documents) > 1:
            for i in range(1, len(documents)):
                sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[i:i+1])[0][0]
                similarities.append({
                    "document_index": i,
                    "similarity": float(sim)
                })
            
            self.log_reasoning(f"Computed cosine similarity with {len(similarities)} documents")
        
        return {
            "top_terms": top_terms,
            "similarities": similarities
        }
    
    def calculate_similarity(self, text1: str, text2: str) -> Dict[str, float]:
        tokens1 = set(self._tokenize(text1))
        tokens2 = set(self._tokenize(text2))
        
        jaccard = len(tokens1 & tokens2) / len(tokens1 | tokens2) if tokens1 | tokens2 else 0
        
        levenshtein_dist = self._levenshtein_distance(text1[:500], text2[:500])
        max_len = max(len(text1[:500]), len(text2[:500]))
        levenshtein_sim = 1 - (levenshtein_dist / max_len) if max_len > 0 else 0
        
        return {
            "jaccard": jaccard,
            "levenshtein": levenshtein_sim
        }
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _determine_content_category(
        self,
        file_path: str,
        text: str,
        tokens: List[str]
    ) -> str:
        """
        Determine content category for text files.
        
        Returns one of:
        - text_docs: Plain text
        - markdown_docs: Markdown files
        - code_docs: Code documentation
        - logs: Log files
        """
        import os
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext in ['.md', '.markdown']:
            return "markdown_docs"
        
        # Check content patterns for logs
        log_patterns = ['ERROR', 'WARN', 'INFO', 'DEBUG', 'timestamp', 'exception']
        log_pattern_count = sum(1 for pattern in log_patterns if pattern.lower() in text.lower())
        
        if log_pattern_count >= 3:
            return "logs"
        
        # Check for code documentation patterns
        doc_patterns = ['@param', '@return', '/**', '*/', 'Args:', 'Returns:']
        doc_pattern_count = sum(1 for pattern in doc_patterns if pattern in text)
        
        if doc_pattern_count >= 2:
            return "code_docs"
        
        # Default to plain text
        return "text_docs"
    
    def log_reasoning(self, message: str):
        timestamp = datetime.utcnow().isoformat()
        self.reasoning_log.append(f"[{timestamp}] {message}")
