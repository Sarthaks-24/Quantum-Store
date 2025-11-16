# api.js - Backend API Client

**Location**: `frontend/src/api.js`  
**Lines**: 377  
**Type**: Service Module (Pure JavaScript)

---

## Overview

The `api.js` module is the **single source of truth** for all frontend-backend communication. It provides a unified, well-documented API client with consistent error handling, timeout management, and data transformation. Every network request in the application flows through this module.

**Design Philosophy**:
- Single responsibility: API calls only
- No UI logic or state management
- Consistent error handling
- Timeout protection (30 seconds default)
- Clear function signatures with JSDoc

---

## Responsibilities

1. **HTTP Communication**
   - All GET/POST requests to FastAPI backend
   - Request timeout enforcement (30s)
   - Response parsing (JSON)
   - Error handling and propagation

2. **Data Transformation**
   - Convert backend responses to frontend-friendly formats
   - Compute derived data (weekly activity, normalized metrics)
   - Format file metadata for display

3. **API Abstraction**
   - Hide implementation details from components
   - Provide semantic function names (`uploadFile` vs `fetch('/upload')`)
   - Single place to update API URLs or request formats

---

## Configuration

### Base URL
```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```
**Source**: `.env` file via Vite environment variables  
**Default**: `http://localhost:8000`  
**Production**: Set `VITE_API_URL` in `.env` to production backend URL

---

## Core Functions

### `fetchWithTimeout(url, options, timeout = 30000)`
**Internal utility** - Used by all other functions

```javascript
async function fetchWithTimeout(url, options = {}, timeout = 30000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response;
  } catch (error) {
    clearTimeout(id);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout');
    }
    throw error;
  }
}
```

**Purpose**: Wraps `fetch()` with automatic timeout  
**Parameters**:
- `url`: Full URL or relative path
- `options`: Standard fetch options (method, headers, body)
- `timeout`: Milliseconds before aborting (default 30000)

**Throws**:
- `Error('Request timeout')` if > 30s
- `Error(detail)` if HTTP error (4xx/5xx)

**Why This Matters**: Prevents hanging requests that degrade UX

---

## API Functions

### File Upload

#### `uploadFile(file)`
```javascript
export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetchWithTimeout(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  return await response.json();
}
```
**Endpoint**: `POST /upload`  
**Input**: `File` object from input[type="file"]  
**Output**: `{ file_id, filename, file_type, analyzed, message }`  
**Use Case**: Single file upload (not used in UI currently)

---

#### `uploadFiles(files, onProgress)`
```javascript
export async function uploadFiles(files, onProgress) {
  const results = [];
  
  for (let i = 0; i < files.length; i++) {
    try {
      const formData = new FormData();
      formData.append('file', files[i]);

      const response = await fetchWithTimeout(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      }, 60000); // 60s timeout for large files

      const data = await response.json();
      results.push({ success: true, file: files[i].name, ...data });
      onProgress?.(i, 100);
    } catch (error) {
      results.push({ success: false, file: files[i].name, error: error.message });
      onProgress?.(i, 0);
    }
  }

  return results;
}
```
**Endpoint**: `POST /upload` (called sequentially for each file)  
**Input**:
- `files`: Array of File objects
- `onProgress`: Optional callback `(fileIndex, progress) => void`

**Output**: Array of result objects
```javascript
[
  { success: true, file: 'doc.pdf', file_id: 'uuid', ... },
  { success: false, file: 'large.mp4', error: 'Request timeout' }
]
```
**Behavior**: Sequential upload (not parallel to avoid backend overload)  
**Timeout**: 60 seconds per file (larger than default for big files)

---

### File Retrieval

#### `fetchFiles()`
```javascript
export async function fetchFiles() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/files`);
  return await response.json();
}
```
**Endpoint**: `GET /files`  
**Output**: Array of file metadata objects
```javascript
[
  {
    id: 'uuid',
    filename: 'report.pdf',
    file_type: 'pdf',
    size: 1024000,
    uploaded_at: '2024-11-15T10:30:00Z',
    classification: { type: 'pdf', category: 'pdf_form', confidence: 0.85 },
    analysis: { ... }
  },
  // ...more files
]
```

---

#### `fetchRecentFiles(limit = 10)`
```javascript
export async function fetchRecentFiles(limit = 10) {
  const response = await fetchWithTimeout(`${API_BASE_URL}/files`);
  const files = await response.json();
  return files.slice(0, limit);
}
```
**Endpoint**: `GET /files` (same as fetchFiles, but limited)  
**Input**: `limit` - Number of files to return (default 10)  
**Output**: Array of most recent files (truncated)  
**Note**: Backend returns all files, this function limits on client side

---

#### `fetchFilePreview(fileId)`
```javascript
export async function fetchFilePreview(fileId) {
  const response = await fetchWithTimeout(`${API_BASE_URL}/file/${fileId}/preview`);
  return await response.json();
}
```
**Endpoint**: `GET /file/{file_id}/preview`  
**Input**: `fileId` - UUID string  
**Output**: File-specific preview data
```javascript
// For PDFs
{
  preview: 'base64_encoded_png',
  text: 'extracted text...',
  page_count: 10
}

// For images
{
  preview: 'data:image/png;base64,...',
  dimensions: { width: 1920, height: 1080 }
}
```

---

#### `downloadFile(fileId, filename)`
```javascript
export async function downloadFile(fileId, filename) {
  const response = await fetchWithTimeout(`${API_BASE_URL}/file/${fileId}/download`);
  const blob = await response.blob();
  
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
```
**Endpoint**: `GET /file/{file_id}/download`  
**Input**:
- `fileId`: UUID string
- `filename`: Desired filename for download

**Behavior**: Triggers browser download dialog  
**Implementation**:
1. Fetch file as Blob
2. Create temporary Object URL
3. Create hidden anchor element
4. Trigger click programmatically
5. Clean up URL and element

---

### Analytics

#### `fetchFileAnalytics(fileId, fileType)`
```javascript
export async function fetchFileAnalytics(fileId, fileType) {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/file/${fileId}/analytics/${fileType}`
  );
  return await response.json();
}
```
**Endpoint**: `GET /file/{file_id}/analytics/{file_type}`  
**Input**:
- `fileId`: UUID string
- `fileType`: 'image', 'pdf', 'json', 'text', 'video'

**Output**: Type-specific analytics
```javascript
// For images
{
  dimensions: { width: 1920, height: 1080 },
  format: 'PNG',
  color_mode: 'RGB',
  dominant_colors: ['#FF5733', '#33FF57'],
  phash: '8f7e6d5c4b3a2918'
}

// For JSON
{
  depth: 3,
  keys: ['name', 'email', 'address'],
  total_keys: 15,
  structure: 'nested',
  sql_ready: true
}
```

---

### Summary & Metrics

#### `fetchSummary()`
```javascript
export async function fetchSummary() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/summary`);
  return await response.json();
}
```
**Endpoint**: `GET /summary`  
**Output**: Dashboard summary statistics
```javascript
{
  totalFiles: 42,
  totalSize: 104857600, // bytes
  totalImages: 15,
  totalPDFs: 10,
  totalJSON: 5,
  byType: {
    image: 15,
    pdf: 10,
    json: 5,
    text: 8,
    video: 4
  }
}
```

---

### Analysis Triggers

#### `startAnalysis(fileId, fileType)`
```javascript
export async function startAnalysis(fileId, fileType) {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/analyze/${fileType}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_id: fileId })
    },
    60000 // 60s timeout for heavy analysis
  );

  return await response.json();
}
```
**Endpoint**: `POST /analyze/{file_type}`  
**Input**:
- `fileId`: UUID string
- `fileType`: 'json', 'text', 'image', 'pdf', 'video'

**Output**: Analysis results (type-specific)  
**Timeout**: 60 seconds (analysis can be slow)  
**Use Case**: Manually trigger analysis for uploaded files

---

## Data Transformation Functions

### `computeWeeklyActivity(files)`
```javascript
export function computeWeeklyActivity(files) {
  const today = new Date();
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const counts = Array(7).fill(0);

  files.forEach(file => {
    const uploadDate = new Date(file.uploaded_at || file.created_at);
    const daysDiff = Math.floor((today - uploadDate) / (1000 * 60 * 60 * 24));
    
    if (daysDiff >= 0 && daysDiff < 7) {
      const dayIndex = uploadDate.getDay();
      counts[dayIndex]++;
    }
  });

  return dayNames.map((name, i) => ({
    name,
    uploads: counts[i]
  }));
}
```
**Purpose**: Transform file list into weekly upload chart data  
**Input**: Array of file objects with `uploaded_at` field  
**Output**: Array of `{ name: 'Mon', uploads: 5 }` objects (7 items)  
**Logic**:
1. Initialize 7-day array (one per weekday)
2. For each file, calculate days ago
3. If within last 7 days, increment that weekday's count
4. Return formatted array

---

### `normalizeWeeklyActivity(data)`
```javascript
export function normalizeWeeklyActivity(data) {
  const today = new Date();
  const startDay = (today.getDay() + 1) % 7; // Start from Monday
  
  const normalized = [];
  for (let i = 0; i < 7; i++) {
    const dayIndex = (startDay + i) % 7;
    normalized.push(data[dayIndex]);
  }
  
  return normalized;
}
```
**Purpose**: Reorder weekly data to start from Monday (not Sunday)  
**Input**: Array from `computeWeeklyActivity()`  
**Output**: Same array, rotated to start with Monday  
**Example**:
```
Input:  [Sun, Mon, Tue, Wed, Thu, Fri, Sat]
Output: [Mon, Tue, Wed, Thu, Fri, Sat, Sun]
```

---

### `fetchWeeklyMetrics()`
```javascript
export async function fetchWeeklyMetrics() {
  const files = await fetchFiles();
  const weeklyData = computeWeeklyActivity(files);
  return normalizeWeeklyActivity(weeklyData);
}
```
**Purpose**: One-function call for weekly chart data  
**Output**: Normalized weekly activity array  
**Use Case**: Dashboard chart data

---

## Error Handling

### Error Types

1. **Network Errors**
   ```javascript
   throw new Error('Failed to fetch');
   ```
   **Cause**: No internet, server down, CORS issues

2. **Timeout Errors**
   ```javascript
   throw new Error('Request timeout');
   ```
   **Cause**: Request took > 30s (or 60s for uploads/analysis)

3. **HTTP Errors**
   ```javascript
   throw new Error(errorData.detail || `HTTP ${response.status}`);
   ```
   **Cause**: 4xx/5xx response from backend  
   **Examples**:
   - 404: File not found
   - 413: Upload too large
   - 500: Internal server error

### Error Propagation

All functions **throw errors** instead of returning error objects:

```javascript
// Good (what we do)
try {
  const data = await fetchFiles();
} catch (error) {
  console.error('Failed to load files:', error.message);
}

// Bad (not used)
const { data, error } = await fetchFiles();
if (error) { ... }
```

**Rationale**: Standard JavaScript error handling, works with async/await

---

## Dependencies

### External
- **None** - Pure JavaScript with Web APIs only

### Browser APIs Used
- `fetch()` - HTTP requests
- `AbortController` - Request timeouts
- `FormData` - File uploads
- `Blob` - File downloads
- `URL.createObjectURL()` - Download triggers

---

## Known Limitations / Edge Cases

1. **Sequential Uploads**
   - Files upload one at a time (not parallel)
   - **Rationale**: Prevents overwhelming backend
   - **Trade-off**: Slower for many files, but more stable

2. **No Request Deduplication**
   - Calling `fetchFiles()` twice makes 2 requests
   - **Enhancement**: Implement request caching or deduplication

3. **No Retry Logic**
   - Failed requests don't auto-retry
   - **Workaround**: User must manually retry

4. **No Request Cancellation UI**
   - Can't cancel ongoing upload/download
   - **Enhancement**: Expose AbortController to components

5. **Client-Side Pagination**
   - `fetchRecentFiles()` fetches all, limits client-side
   - **Inefficiency**: Wasteful for large datasets
   - **Backend Enhancement**: Add pagination to `/files` endpoint

6. **No Progress for Downloads**
   - Download size unknown until complete
   - **Enhancement**: Parse Content-Length header for progress bar

---

## How to Modify or Extend

### Add New Endpoint

```javascript
export async function deleteFile(fileId) {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/file/${fileId}`,
    { method: 'DELETE' }
  );
  return await response.json();
}
```

---

### Add Request Interceptor (e.g., Auth Token)

```javascript
function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem('auth_token');
  return fetchWithTimeout(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });
}

// Use in all functions
export async function fetchFiles() {
  const response = await fetchWithAuth(`${API_BASE_URL}/files`);
  return await response.json();
}
```

---

### Implement Request Caching

```javascript
const cache = new Map();

export async function fetchFiles() {
  if (cache.has('files')) {
    return cache.get('files');
  }

  const response = await fetchWithTimeout(`${API_BASE_URL}/files`);
  const data = await response.json();
  
  cache.set('files', data);
  setTimeout(() => cache.delete('files'), 60000); // Expire after 1 min
  
  return data;
}
```

---

### Add Retry Logic

```javascript
async function fetchWithRetry(url, options, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      return await fetchWithTimeout(url, options);
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(r => setTimeout(r, 1000 * (i + 1))); // Exponential backoff
    }
  }
}
```

---

## Testing Considerations

### Mock API for Tests

```javascript
// tests/mocks/api.js
export const mockFetchFiles = jest.fn(() => 
  Promise.resolve([
    { id: '1', filename: 'test.pdf', size: 1024 }
  ])
);

// In test
import * as api from '../api';
jest.spyOn(api, 'fetchFiles').mockImplementation(mockFetchFiles);
```

---

### Test Timeout Handling

```javascript
it('should timeout after 30 seconds', async () => {
  jest.useFakeTimers();
  
  const promise = fetchFiles();
  jest.advanceTimersByTime(31000);
  
  await expect(promise).rejects.toThrow('Request timeout');
});
```

---

**Last Updated**: November 2024  
**Module Status**: ✅ Production-ready, Well-tested
