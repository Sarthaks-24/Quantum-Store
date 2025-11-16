# Files.jsx - File Browser Component

**Location**: `frontend/src/components/ui/Files.jsx`  
**Lines**: 450  
**Dependencies**: React, Framer Motion, Lucide Icons, api.js

---

## Overview

The Files component is a **comprehensive file management interface** that displays all uploaded files in a filterable, sortable grid. It provides advanced search, multiple filter dimensions (type, date, size), and instant preview access. The component is performance-optimized with debounced search and memoized calculations.

**Primary Purpose**: Browse, search, filter, and preview all files in the system

---

## Responsibilities

1. **File Listing**
   - Fetch and display all files from backend
   - Show file cards in responsive grid layout
   - Display file metadata (name, category, size, date)

2. **Search Functionality**
   - Real-time search by filename (300ms debounced)
   - Case-insensitive matching
   - Instant visual feedback

3. **Multi-Dimensional Filtering**
   - **Type Filter**: All, Images, PDFs, Text, JSON, Video, Audio, Other
   - **Date Filter**: All, Today, Last 7 Days, Last 30 Days
   - **Size Filter**: All, Small (<1MB), Medium (1-10MB), Large (>10MB)

4. **Sorting**
   - Newest First (default)
   - Oldest First
   - Largest First
   - Smallest First
   - Name A→Z
   - Name Z→A

5. **File Preview**
   - Click any file to open PreviewModal
   - Navigate between files using arrow keys
   - View detailed analytics

---

## Input / Output

### Props
**None** - Files is a top-level route component

### State Variables

```javascript
const [files, setFiles] = useState([])
// All files from backend (unfiltered)

const [filteredFiles, setFilteredFiles] = useState([])
// Filtered and sorted files (displayed)

const [loading, setLoading] = useState(true)
// Loading state for initial fetch

const [searchQuery, setSearchQuery] = useState('')
// Raw search input (updates on every keystroke)

const [debouncedQuery, setDebouncedQuery] = useState('')
// Debounced search query (updates after 300ms)

const [selectedType, setSelectedType] = useState('all')
// Current type filter ('all', 'image', 'pdf', etc.)

const [selectedDateRange, setSelectedDateRange] = useState('all')
// Current date filter ('all', 'today', 'week', 'month')

const [selectedSizeRange, setSelectedSizeRange] = useState('all')
// Current size filter ('all', 'small', 'medium', 'large')

const [sortBy, setSortBy] = useState('newest')
// Current sort order

const [selectedFile, setSelectedFile] = useState(null)
// File currently being previewed (null when modal closed)
```

### Refs

```javascript
const searchTimeoutRef = useRef(null)
// Timeout handle for debounced search
```

### API Calls

```javascript
fetchFiles() // GET /files - Returns all file metadata
```

### Events Emitted
- **onFileSelect**: Opens PreviewModal
- **onNavigate**: Changes preview to different file
- **onClose**: Closes PreviewModal

---

## Internal Flow

### 1. **Component Lifecycle**

```
Component Mount
  └─> useEffect (mount)
      └─> loadFiles()
          ├─> setLoading(true)
          ├─> fetchFiles() → setFiles()
          └─> setLoading(false)

useEffect (search debounce)
  ├─> Clear previous timeout
  ├─> Set 300ms timeout
  └─> setDebouncedQuery(searchQuery)

useEffect (filter/sort)
  └─> applyFiltersAndSort()
      ├─> Filter by search
      ├─> Filter by type
      ├─> Filter by date
      ├─> Filter by size
      ├─> Sort by selected criteria
      └─> setFilteredFiles(result)
```

### 2. **Search Debouncing**

**Without Debouncing** (Bad):
```
User types "report.pdf" (10 keystrokes)
  → 10 filter operations
  → 10 re-renders
  → Poor performance
```

**With Debouncing** (Good):
```
User types "report.pdf"
  → Only 1 filter operation (300ms after last keystroke)
  → 1 re-render
  → Smooth UX
```

**Implementation**:
```javascript
useEffect(() => {
  if (searchTimeoutRef.current) {
    clearTimeout(searchTimeoutRef.current); // Cancel previous timer
  }
  searchTimeoutRef.current = setTimeout(() => {
    setDebouncedQuery(searchQuery); // Update after 300ms
  }, 300);
  
  return () => clearTimeout(searchTimeoutRef.current); // Cleanup
}, [searchQuery]);
```

### 3. **Filter Application Logic**

```javascript
const applyFiltersAndSort = useCallback(() => {
  let result = [...files]; // Copy array

  // 1. Search filter
  if (debouncedQuery) {
    const query = debouncedQuery.toLowerCase();
    result = result.filter(file => 
      (file.filename || '').toLowerCase().includes(query)
    );
  }

  // 2. Type filter
  if (selectedType !== 'all') {
    result = result.filter(file => 
      (file.classification?.type || 'unknown') === selectedType
    );
  }

  // 3. Date range filter
  if (selectedDateRange !== 'all') {
    const now = new Date();
    const cutoffDate = new Date(now - daysAgo * 24 * 60 * 60 * 1000);
    result = result.filter(file => {
      const fileDate = new Date(file.uploaded_at || file.created_at);
      return fileDate >= cutoffDate;
    });
  }

  // 4. Size range filter
  if (selectedSizeRange !== 'all') {
    const [min, max] = getSizeRange(selectedSizeRange);
    result = result.filter(file => 
      file.size >= min && file.size < max
    );
  }

  // 5. Sorting
  switch (sortBy) {
    case 'newest':
      result.sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at));
      break;
    case 'oldest':
      result.sort((a, b) => new Date(a.uploaded_at) - new Date(b.uploaded_at));
      break;
    case 'largest':
      result.sort((a, b) => b.size - a.size);
      break;
    // ...other cases
  }

  setFilteredFiles(result);
}, [files, debouncedQuery, selectedType, selectedDateRange, selectedSizeRange, sortBy]);
```

---

## Key Functions / Hooks

### `loadFiles()`
```javascript
const loadFiles = useCallback(async () => {
  setLoading(true);
  try {
    const data = await fetchFiles();
    setFiles(data);
  } catch (error) {
    console.error('Failed to load files:', error);
  } finally {
    setLoading(false);
  }
}, []);
```
**Purpose**: Fetches all files from backend  
**Called**: On component mount  
**Error Handling**: Logs error, keeps loading state false

---

### `handleSearchChange(e)`
```javascript
const handleSearchChange = useCallback((e) => {
  setSearchQuery(e.target.value);
}, []);
```
**Purpose**: Updates search query state on input change  
**Note**: Actual filtering happens after 300ms debounce

---

### `handleFileSelect(file)`
```javascript
const handleFileSelect = useCallback((file) => {
  setSelectedFile(file);
}, []);
```
**Purpose**: Opens PreviewModal with selected file  
**Triggered**: User clicks FileCard or presses Enter/Space

---

### Utility Functions (Outside Component)

```javascript
const formatSize = (bytes) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatDate = (dateString) => {
  if (!dateString) return 'Unknown';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

const getFileIcon = (type) => {
  switch (type) {
    case 'image': return ImageIcon;
    case 'pdf': return FileText;
    case 'video': return Video;
    case 'audio': return Music;
    case 'json': return Database;
    case 'text': return FileText;
    default: return File;
  }
};
```

---

## Extracted Components

### `<FileCard />`
```javascript
const FileCard = React.memo(({ file, index, onSelect }) => {
  const FileIcon = getFileIcon(file.classification?.type);
  const fileType = file.classification?.type || 'unknown';
  const hasAnalytics = fileType !== 'unknown';

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: index * 0.02 }}
      onClick={() => onSelect(file)}
      className="glass-card-hover p-4 cursor-pointer group"
    >
      {/* File Icon */}
      <div className="p-3 bg-accent-indigo/20 rounded-xl">
        <FileIcon size={28} className="text-accent-indigo" />
      </div>

      {/* Metadata */}
      <h4>{file.filename}</h4>
      <p>{file.classification?.category}</p>
      <p>{formatSize(file.size)}</p>
      <p>{formatDate(file.uploaded_at)}</p>

      {/* Subcategory Tags */}
      {file.classification?.subcategories?.map(tag => (
        <span key={tag}>{tag}</span>
      ))}

      {/* Analytics Button (hover only) */}
      {hasAnalytics && (
        <button onClick={(e) => { e.stopPropagation(); onSelect(file); }}>
          View Analytics
        </button>
      )}
    </motion.div>
  );
});
```

**Props**:
- `file`: File object with metadata
- `index`: Number for staggered animation
- `onSelect`: Callback when file is clicked

**Features**:
- Staggered fade-in animation (0.02s delay per item)
- Hover scale effect
- Shows confidence score if available
- Displays up to 2 subcategory tags
- Analytics button appears on hover

---

## Dependencies

### Internal
- **api.js**: `fetchFiles()`
- **PreviewModal.jsx**: File preview component

### External
- **react**: `useState`, `useEffect`, `useCallback`, `useMemo`, `useRef`
- **framer-motion**: `motion` (animations)
- **lucide-react**: Icons (`Search`, `SortAsc`, `Image`, `FileText`, `Video`, `Music`, `Database`, `File`, `Calendar`, `HardDrive`, `BarChart3`)

---

## State Management

### Memoized Values

```javascript
// Type filters - only recalculates when files array changes
const typeFilters = useMemo(() => [
  { value: 'all', label: 'All Types', count: files.length },
  { value: 'image', label: 'Images', count: files.filter(f => f.classification?.type === 'image').length },
  { value: 'pdf', label: 'PDFs', count: files.filter(f => f.classification?.type === 'pdf').length },
  // ...other types
], [files]);
```

**Performance Benefit**: Prevents recalculating file counts on every render

---

## UI Elements

### Search Bar
```jsx
<input
  type="text"
  placeholder="Search files by name..."
  value={searchQuery}
  onChange={handleSearchChange}
  className="w-full pl-10 pr-4 py-3..."
/>
```
- Debounced to 300ms
- Case-insensitive
- Searches filename only (not content)

### Filter Dropdowns
```jsx
<select value={selectedDateRange} onChange={(e) => setSelectedDateRange(e.target.value)}>
  <option value="all">All Dates</option>
  <option value="today">Today</option>
  <option value="week">Last 7 Days</option>
  <option value="month">Last 30 Days</option>
</select>
```

### Type Filter Buttons
```jsx
<button
  onClick={() => setSelectedType('image')}
  className={selectedType === 'image' ? 'active' : ''}
>
  Images (12)
</button>
```
- Shows count for each type
- Highlights active filter

### Sort Dropdown
```jsx
<select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
  <option value="newest">Newest First</option>
  <option value="oldest">Oldest First</option>
  <option value="largest">Largest First</option>
  <option value="smallest">Smallest First</option>
  <option value="name-asc">A → Z</option>
  <option value="name-desc">Z → A</option>
</select>
```

---

## Known Limitations / Edge Cases

1. **Search Filename Only**
   - Doesn't search file content or metadata
   - **Enhancement**: Implement full-text search with backend support

2. **No Multi-Select**
   - Can't select multiple files for batch operations
   - **Workaround**: Preview files one by one

3. **Large File Lists**
   - No pagination or virtualization
   - **Performance Impact**: May lag with 1000+ files
   - **Solution**: Implement React Virtual or pagination

4. **Filter Persistence**
   - Filters reset on page reload
   - **Enhancement**: Save filters to localStorage or URL params

5. **No Export/Download All**
   - Must download files individually
   - **Enhancement**: Add batch download with zip compression

6. **Date Filter Edge Cases**
   - "Today" filter uses local timezone (may differ from server)
   - Files without `uploaded_at` field are excluded
   - **Assumption**: All files have valid timestamps

7. **Type Filter Unknown**
   - Files without classification show as "Other"
   - **Behavior**: Grouped in "Other" category

---

## How to Modify or Extend

### Add New Filter Dimension

**Example: Add "Classification Confidence" Filter**

1. **Add state**:
```javascript
const [minConfidence, setMinConfidence] = useState(0);
```

2. **Add UI slider**:
```jsx
<input
  type="range"
  min="0"
  max="100"
  value={minConfidence}
  onChange={(e) => setMinConfidence(Number(e.target.value))}
/>
```

3. **Update filter logic**:
```javascript
if (minConfidence > 0) {
  result = result.filter(file => 
    (file.classification?.confidence || 0) >= minConfidence / 100
  );
}
```

---

### Implement Pagination

```javascript
const [page, setPage] = useState(1);
const itemsPerPage = 50;

const paginatedFiles = useMemo(() => {
  const start = (page - 1) * itemsPerPage;
  return filteredFiles.slice(start, start + itemsPerPage);
}, [filteredFiles, page]);

// Render pagination controls
<div>
  <button onClick={() => setPage(p => Math.max(1, p - 1))}>Previous</button>
  <span>Page {page} of {Math.ceil(filteredFiles.length / itemsPerPage)}</span>
  <button onClick={() => setPage(p => p + 1)}>Next</button>
</div>
```

---

### Add Bulk Selection

```javascript
const [selectedFiles, setSelectedFiles] = useState(new Set());

const toggleSelect = (fileId) => {
  setSelectedFiles(prev => {
    const next = new Set(prev);
    if (next.has(fileId)) {
      next.delete(fileId);
    } else {
      next.add(fileId);
    }
    return next;
  });
};

// In FileCard
<input
  type="checkbox"
  checked={selectedFiles.has(file.id)}
  onChange={() => toggleSelect(file.id)}
/>
```

---

### Save Filters to URL

```javascript
import { useSearchParams } from 'react-router-dom';

const [searchParams, setSearchParams] = useSearchParams();

// On filter change
useEffect(() => {
  const params = new URLSearchParams();
  if (selectedType !== 'all') params.set('type', selectedType);
  if (searchQuery) params.set('q', searchQuery);
  setSearchParams(params);
}, [selectedType, searchQuery]);

// On mount
useEffect(() => {
  const type = searchParams.get('type');
  const query = searchParams.get('q');
  if (type) setSelectedType(type);
  if (query) setSearchQuery(query);
}, []);
```

---

## Performance Characteristics

### Initial Load
- **API Call**: ~100-500ms (depends on file count)
- **Render Time**: ~50-200ms (depends on file count)

### Search Performance
- **Without Debounce**: 10 keystrokes = 10 filter ops
- **With Debounce**: 10 keystrokes = 1 filter op (300ms after last)
- **Performance Gain**: ~90% reduction in filter operations

### Re-Render Triggers
- `files` changes → Full re-render
- `filteredFiles` changes → File grid re-renders
- Filter/sort state changes → Triggers `applyFiltersAndSort()`
- Search input changes → Triggers debounce timer (not immediate re-render)

### Memory Footprint
- **Base**: ~10KB (component state)
- **100 files**: ~100KB (metadata)
- **1000 files**: ~1MB (metadata)

---

## Testing Considerations

### Unit Tests
```javascript
it('should debounce search input', async () => {
  const { getByPlaceholderText } = render(<Files />);
  const input = getByPlaceholderText('Search files by name...');
  
  fireEvent.change(input, { target: { value: 't' } });
  fireEvent.change(input, { target: { value: 'te' } });
  fireEvent.change(input, { target: { value: 'test' } });
  
  // Filter should not be applied immediately
  expect(filteredFiles).toHaveLength(allFiles.length);
  
  // After 300ms, filter is applied
  await waitFor(() => expect(filteredFiles.length).toBeLessThan(allFiles.length), { timeout: 400 });
});

it('should filter by file type', () => {
  const { getByText } = render(<Files />);
  fireEvent.click(getByText('Images (12)'));
  expect(filteredFiles.every(f => f.classification.type === 'image')).toBe(true);
});
```

---

**Last Updated**: November 2024  
**Component Status**: ✅ Production-ready, Performance-optimized with debouncing
