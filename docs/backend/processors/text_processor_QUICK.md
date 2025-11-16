# Text Processor - Quick Reference

## What It Does
Analyzes text files: word count, readability, keywords, TF-IDF similarity

## Main Function
```python
processor = TextProcessor()
result = processor.analyze(file_path, corpus_paths=[])
```

## Output Example
```json
{
  "char_count": 5420,
  "word_count": 850,
  "line_count": 120,
  "tokens": {
    "total": 850,
    "unique": 420,
    "top_20": [
      {"token": "python", "count": 45, "frequency": 0.053},
      {"token": "function", "count": 32, "frequency": 0.038}
    ]
  },
  "readability": {
    "score": 65.3,
    "level": "standard",
    "avg_sentence_length": 18.5,
    "complex_word_ratio": 0.15
  },
  "content_category": "text_code",
  "tfidf": {
    "top_terms": [
      {"term": "algorithm", "score": 0.85},
      {"term": "optimization", "score": 0.72}
    ],
    "similarities": [
      {"document_index": 1, "similarity": 0.65}
    ]
  }
}
```

## Key Features

### 1. **Tokenization**
Extracts words from text:
```python
def _tokenize(self, text):
    text_lower = text.lower()
    tokens = re.findall(r'\b[a-z]+\b', text_lower)
    return tokens
```

**Example:**
```
"Hello, world! Python is great." 
→ ["hello", "world", "python", "is", "great"]
```

### 2. **Top Keywords (Stopword Filtering)**
```python
stopwords = {'the', 'a', 'and', 'or', 'but', 'in', 'on', ...}

filtered_tokens = [t for t in tokens 
                   if t not in stopwords and len(t) > 2]

counter = Counter(filtered_tokens)
top_20 = counter.most_common(20)
```

**Why?** "the", "a", "is" are not meaningful keywords

### 3. **Readability Score (Flesch Reading Ease)**
Formula:
```
score = 206.835 - 1.015 × avg_sentence_length - 84.6 × complex_word_ratio
```

**Levels:**
```python
if score >= 90:   level = "very_easy"        # 5th grade
elif score >= 80: level = "easy"             # 6th grade
elif score >= 70: level = "fairly_easy"      # 7th grade
elif score >= 60: level = "standard"         # 8-9th grade
elif score >= 50: level = "fairly_difficult" # 10-12th grade
elif score >= 30: level = "difficult"        # College
else:             level = "very_difficult"   # Professional
```

**Example:**
- Children's book: score = 95 (very_easy)
- News article: score = 65 (standard)
- Technical paper: score = 25 (very_difficult)

### 4. **TF-IDF (Term Frequency-Inverse Document Frequency)**
Finds important words unique to this document:

```python
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(
    max_features=100,
    stop_words='english'
)

tfidf_matrix = vectorizer.fit_transform(documents)
```

**How it works:**
- **TF (Term Frequency):** How often word appears in THIS document
- **IDF (Inverse Document Frequency):** How rare word is across ALL documents

**Example:**
```
Document 1: "Python is great for machine learning"
Document 2: "JavaScript is great for web development"

TF-IDF for Document 1:
- "python": 0.85 (unique to doc 1)
- "machine": 0.80 (unique to doc 1)
- "learning": 0.78 (unique to doc 1)
- "great": 0.10 (appears in both docs)
- "is": 0.05 (common word)
```

### 5. **Similarity Calculation**
```python
from sklearn.metrics.pairwise import cosine_similarity

# Compare document vectors
similarity = cosine_similarity(
    tfidf_matrix[0],  # Target doc
    tfidf_matrix[1:]  # Other docs
)
```

**Returns:** 0.0 (completely different) to 1.0 (identical)

## How It Works

### Step 1: Read File
```python
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()
```

### Step 2: Tokenize
```python
tokens = self._tokenize(text)
# ["hello", "world", "python", ...]
```

### Step 3: Count Basics
```python
char_count = len(text)
word_count = len(tokens)
line_count = text.count('\n') + 1
```

### Step 4: Extract Keywords
```python
top_tokens = self._get_top_tokens(tokens, 20)
# [{"token": "python", "count": 45}, ...]
```

### Step 5: Calculate Readability
```python
readability = self._calculate_readability(text, tokens)
# {"score": 65.3, "level": "standard"}
```

### Step 6: TF-IDF (Optional)
```python
if corpus_paths:  # If comparing with other docs
    tfidf_data = self._calculate_tfidf([file_path] + corpus_paths)
```

## Content Categories

Determines text type:
```python
def _determine_content_category(self, file_path, text, tokens):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.md':
        return "text_markdown"
    elif ext == '.csv':
        return "text_csv"
    elif ext == '.xml':
        return "text_xml"
    elif ext in ['.py', '.js', '.java', '.cpp']:
        return "text_code"
    elif ext == '.log':
        return "text_log"
    else:
        # Heuristic detection
        if '```' in text or 'def ' in text:
            return "text_code"
        elif '<html>' in text.lower():
            return "text_html"
        else:
            return "text_document"
```

**Categories:**
- `text_code` - Python, JavaScript, etc.
- `text_markdown` - .md files
- `text_csv` - CSV data
- `text_xml` - XML data
- `text_log` - Log files
- `text_document` - Generic text

## Performance

| File Size | Time |
|-----------|------|
| 10KB | 10ms |
| 100KB | 50ms |
| 1MB | 500ms |
| 10MB | 5s |

**Bottleneck:** TF-IDF calculation (requires sklearn)

## Example Usage

```python
# In app.py
@app.post("/analyze/text")
async def analyze_text_endpoint(file_id: str):
    metadata = store.get_metadata(file_id)
    file_path = metadata["file_path"]
    
    # Get all text files for TF-IDF comparison
    all_files = store.get_all_files()
    text_files = [f for f in all_files if f["file_type"] == "text"]
    corpus_paths = [f["file_path"] for f in text_files]
    
    # Analyze
    analysis = text_processor.analyze(file_path, corpus_paths)
    
    # Classify
    category = classifier.classify_file(
        file_path, 
        "text", 
        {"text": analysis}
    )
    
    # Save
    store.save_metadata(file_id, {...})
```

## Limitations
1. **Only English stopwords** (not multilingual)
2. **Basic tokenization** (no lemmatization/stemming)
3. **TF-IDF requires corpus** (other documents to compare)
4. **No sentiment analysis**
5. **No entity extraction** (names, places, dates)
6. **Large files (>10MB) slow** (loads entire file into memory)

## Quiz Tips
- **Readability formula:** Flesch Reading Ease
- **Readability range:** 0-100 (higher = easier)
- **Stopwords:** Common words filtered out ("the", "a", "is")
- **TF-IDF:** Finds unique important words
- **Similarity:** Cosine similarity (0.0 to 1.0)
- **Output categories:** 6 types (code, markdown, csv, xml, log, document)
- **Top keywords:** 20 max
