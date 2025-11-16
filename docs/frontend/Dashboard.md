# Dashboard.jsx - Main Dashboard Component

**Location**: `frontend/src/components/ui/Dashboard.jsx`  
**Lines**: 380  
**Dependencies**: React, Framer Motion, React Router, Recharts, Lucide Icons, api.js

---

## Overview

The Dashboard component is the **main landing page** of QuantumStore. It displays a comprehensive overview of the file system with real-time statistics, charts, and recently uploaded files. The component automatically loads on app startup and provides quick navigation to other sections.

**Key Responsibilities**:
- Display file statistics (total files, storage used, file counts by type)
- Show weekly upload activity as a bar chart
- Display file type distribution as a pie chart
- List the 10 most recent uploads with metadata
- Provide quick access to file previews

---

## Responsibilities

1. **Data Fetching**
   - Fetch summary statistics from `/summary` endpoint
   - Fetch recent files from `/files` endpoint
   - Compute weekly activity data from all files
   - Handle loading and error states

2. **Statistics Display**
   - Total Files count
   - Storage Used (formatted as MB/GB)
   - Image file count
   - Document count (PDFs + JSON)

3. **Data Visualization**
   - Weekly Activity Bar Chart (7 days)
   - File Type Distribution Pie Chart

4. **Recent Files**
   - Display last 10 uploaded files
   - Sort by newest first (uploaded_at)
   - Show file icon based on classification type
   - Enable click-to-preview functionality

5. **Performance Optimization**
   - Memoize stat cards and charts
   - Use React.memo for child components
   - Debounce expensive calculations

---

## Input / Output

### Props
**None** - Dashboard is a top-level route component

### State Variables

```javascript
const [summary, setSummary] = useState(null)
// Shape: { totalFiles, totalSize, totalImages, totalPDFs, totalJSON, byType: {...} }

const [recentFiles, setRecentFiles] = useState([])
// Array of file objects (max 10)

const [selectedFile, setSelectedFile] = useState(null)
// Currently previewed file object or null

const [loading, setLoading] = useState(true)
// Boolean: data loading state

const [activityData, setActivityData] = useState([])
// Array: [{ name: 'Mon', uploads: 5 }, ...]
```

### API Calls

```javascript
// Parallel data fetching on mount
Promise.all([
  fetchSummary(),        // GET /summary
  fetchRecentFiles(100), // GET /files (limit 100)
  fetchFiles()           // GET /files (all)
])
```

### Events Emitted
- **onFileClick**: Opens PreviewModal with selected file
- **onClose**: Closes PreviewModal

---

## Internal Flow

### 1. **Component Mount**
```
useEffect (on mount)
  └─> loadDashboardData()
      ├─> fetchSummary() → setSummary()
      ├─> fetchRecentFiles(100) → sort by date → slice(0, 10) → setRecentFiles()
      └─> fetchFiles() → computeWeeklyActivity() → normalizeWeeklyActivity() → setActivityData()
```

### 2. **Data Processing**

**Sort Recent Files**:
```javascript
const sortedFiles = [...filesData].sort((a, b) => {
  const dateA = new Date(a.uploaded_at || 0);
  const dateB = new Date(b.uploaded_at || 0);
  return dateB - dateA; // Newest first
});
setRecentFiles(sortedFiles.slice(0, 10));
```

**Compute Weekly Activity**:
```javascript
const weeklyData = normalizeWeeklyActivity(computeWeeklyActivity(allFiles));
// Returns: [{ name: 'Mon', uploads: X }, { name: 'Tue', uploads: Y }, ...]
```

### 3. **Rendering Pipeline**

```
Dashboard Component
  ├─> Top Bar (Welcome message + Last sync time)
  ├─> Stats Grid (4 cards)
  │   ├─> StatCard (Total Files)
  │   ├─> StatCard (Storage Used)
  │   ├─> StatCard (Images)
  │   └─> StatCard (Documents)
  ├─> Charts Grid (2 cards)
  │   ├─> Weekly Activity (BarChart from Recharts)
  │   └─> File Types (PieChart from Recharts)
  └─> Recent Uploads
      ├─> FileCard x 10 (sorted by date)
      └─> PreviewModal (conditional)
```

---

## Key Functions / Hooks

### `loadDashboardData()`
```javascript
const loadDashboardData = useCallback(async () => {
  setLoading(true);
  try {
    const [summaryData, filesData, allFiles] = await Promise.all([
      fetchSummary(),
      fetchRecentFiles(100),
      fetchFiles()
    ]);
    // Process and set state...
  } catch (error) {
    console.error('Failed to load dashboard data:', error);
    // Fallback to empty activity data
  } finally {
    setLoading(false);
  }
}, []);
```
**Purpose**: Fetches all dashboard data in parallel  
**Called**: On component mount, after file upload (if integrated)  
**Error Handling**: Falls back to empty charts, shows loading indicator

---

### `formatSize(bytes)`
```javascript
const formatSize = useCallback((bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}, []);
```
**Purpose**: Convert bytes to human-readable format  
**Used**: Storage Used stat, file metadata display  
**Example**: `1048576 → "1 MB"`

---

### `handleFileSelect(file)`
```javascript
const handleFileSelect = useCallback((file) => {
  setSelectedFile(file);
}, []);
```
**Purpose**: Opens PreviewModal with clicked file  
**Triggered**: User clicks on a FileCard

---

### `handleClosePreview()`
```javascript
const handleClosePreview = useCallback(() => {
  setSelectedFile(null);
}, []);
```
**Purpose**: Closes PreviewModal  
**Triggered**: User clicks X or presses Escape

---

## Extracted Components

### `<StatCard />`
```javascript
const StatCard = React.memo(({ stat, index }) => (
  <motion.div initial={{ y: 20 }} animate={{ y: 0 }} transition={{ delay: index * 0.1 }}>
    {/* Icon, Value, Title, Change % */}
  </motion.div>
));
```
**Props**:
- `stat`: `{ title, value, icon, color, change }`
- `index`: Number (for stagger animation)

**Purpose**: Displays a single statistic card with animated entry

---

### `<FileCard />`
```javascript
const FileCard = React.memo(({ file, index, formatSize, onSelect }) => {
  // Icon selection based on file.classification.type
  const Icon = getFileIcon(file.classification?.type);
  return (
    <motion.div onClick={() => onSelect(file)}>
      {/* File icon, name, category, size */}
    </motion.div>
  );
});
```
**Props**:
- `file`: File object with metadata
- `index`: Number (for stagger animation)
- `formatSize`: Function to format file size
- `onSelect`: Callback when file is clicked

**Purpose**: Displays a file card with icon, name, and metadata

---

## Dependencies

### Internal
- **api.js**: `fetchSummary`, `fetchRecentFiles`, `fetchFiles`, `computeWeeklyActivity`, `normalizeWeeklyActivity`
- **PreviewModal.jsx**: File preview component

### External
- **react**: `useState`, `useEffect`, `useCallback`, `useMemo`
- **framer-motion**: `motion` (animations)
- **recharts**: `BarChart`, `PieChart`, `Bar`, `Pie`, `Cell`, `XAxis`, `YAxis`, `CartesianGrid`, `Tooltip`, `ResponsiveContainer`
- **lucide-react**: Icons (`Files`, `HardDrive`, `Image`, `FileText`, `Video`, `Music`, `Database`, `TrendingUp`, `Clock`, `FolderOpen`)

---

## State Management

### Memoized Values

```javascript
// Stats array - only recalculates when summary changes
const stats = useMemo(() => [
  { title: 'Total Files', value: summary?.totalFiles || 0, icon: Files, color: 'indigo', change: '+12%' },
  { title: 'Storage Used', value: formatSize(summary?.totalSize), icon: HardDrive, color: 'teal', change: '+8%' },
  { title: 'Images', value: summary?.totalImages || 0, icon: Image, color: 'amber', change: '+15%' },
  { title: 'Documents', value: (summary?.totalPDFs || 0) + (summary?.totalJSON || 0), icon: FileText, color: 'green', change: '+5%' }
], [summary, formatSize]);

// Type distribution - only recalculates when summary.byType changes
const typeDistribution = useMemo(() => 
  summary?.byType ? Object.entries(summary.byType).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value
  })) : [],
  [summary]
);
```

---

## Known Limitations / Edge Cases

1. **No Real-Time Updates**
   - Data doesn't auto-refresh when files are uploaded externally
   - **Workaround**: Manual page refresh or navigate away and back

2. **Change Percentages are Static**
   - `"+12%"`, `"+8%"` are hardcoded placeholders
   - **Assumption**: These would be calculated from historical data in production

3. **Recent Files Limited to 10**
   - Only shows last 10 files even if more exist
   - **Rationale**: Prevents UI clutter and performance issues

4. **Weekly Activity Fallback**
   - If API fails, shows empty bar chart (all zeros)
   - **User Experience**: Clear visual that data is unavailable

5. **No Pagination for Charts**
   - File type pie chart may be cluttered with many types
   - **Assumption**: Most users have < 10 file types

6. **Loading State Blocks UI**
   - Entire dashboard shows "Loading..." during data fetch
   - **Enhancement Opportunity**: Skeleton screens or progressive loading

---

## How to Modify or Extend

### Add a New Stat Card

1. **Update `stats` array**:
```javascript
const stats = useMemo(() => [
  // ...existing stats
  { 
    title: 'Videos', 
    value: summary?.totalVideos || 0, 
    icon: Video, 
    color: 'purple', 
    change: '+20%' 
  }
], [summary, formatSize]);
```

2. **Ensure backend provides `totalVideos` in `/summary` response**

---

### Change Chart Type

**Replace Bar Chart with Line Chart**:
```javascript
import { LineChart, Line } from 'recharts';

<LineChart data={activityData}>
  <Line type="monotone" dataKey="uploads" stroke="#7c3aed" strokeWidth={2} />
  {/* ...other components */}
</LineChart>
```

---

### Add Real-Time Auto-Refresh

```javascript
useEffect(() => {
  const interval = setInterval(() => {
    loadDashboardData();
  }, 30000); // Refresh every 30 seconds

  return () => clearInterval(interval);
}, [loadDashboardData]);
```

---

### Display More Recent Files

```javascript
// Change from 10 to 20
setRecentFiles(sortedFiles.slice(0, 20));
```

**Note**: Adjust grid layout in JSX to accommodate more items:
```javascript
className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
```

---

### Add Error Toast Notifications

```javascript
import { toast } from 'react-hot-toast'; // Install: npm install react-hot-toast

const loadDashboardData = useCallback(async () => {
  try {
    // ...existing code
  } catch (error) {
    toast.error('Failed to load dashboard data');
    console.error(error);
  }
}, []);
```

---

## Performance Characteristics

### Initial Load Time
- **API Calls**: 3 parallel requests (~100-300ms each)
- **Total Time**: ~300-500ms (network dependent)
- **Render Time**: < 50ms (React optimized)

### Re-Render Triggers
- `summary` changes → Stats cards re-render
- `recentFiles` changes → File list re-renders
- `activityData` changes → Charts re-render
- `selectedFile` changes → PreviewModal opens/closes

### Memory Footprint
- **State Size**: ~10KB (summary + 10 files + activity data)
- **Component Tree**: Shallow (3 levels max)

---

## Testing Considerations

### Unit Tests
```javascript
describe('Dashboard', () => {
  it('should load summary data on mount', async () => {
    render(<Dashboard />);
    await waitFor(() => expect(fetchSummary).toHaveBeenCalled());
  });

  it('should display 4 stat cards', () => {
    render(<Dashboard />);
    expect(screen.getAllByRole('article')).toHaveLength(4);
  });

  it('should open PreviewModal on file click', () => {
    const { getByText } = render(<Dashboard />);
    fireEvent.click(getByText('test.pdf'));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});
```

### Integration Tests
- Test data fetching with mock API
- Test chart rendering with sample data
- Test file selection and preview flow

---

**Last Updated**: November 2024  
**Component Status**: ✅ Production-ready, Performance-optimized
