import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  Search, 
  SortAsc,
  Image as ImageIcon,
  FileText,
  Video,
  Music,
  Database,
  File,
  Calendar,
  HardDrive,
  BarChart3
} from 'lucide-react';
import { fetchFiles } from '../../api';
import PreviewModal from './PreviewModal';

// Utility functions moved outside component (pure functions)
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

// Extracted FileCard Component
const FileCard = React.memo(({ file, index, onSelect }) => {
  const FileIcon = getFileIcon(file.classification?.type);
  const fileType = file.classification?.type || 'unknown';
  const hasAnalytics = fileType !== 'unknown';

  const handleClick = useCallback(() => {
    onSelect(file);
  }, [file, onSelect]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(file);
    }
  }, [file, onSelect]);

  const handleAnalyticsClick = useCallback((e) => {
    e.stopPropagation();
    onSelect(file);
  }, [file, onSelect]);

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: index * 0.02 }}
      whileHover={{ scale: 1.02 }}
      className="glass-card-hover p-4 cursor-pointer group"
      role="button"
      tabIndex={0}
      aria-label={`View ${file.filename}`}
    >
      <div 
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        className="flex flex-col gap-3"
      >
        {/* File Icon Header */}
        <div className="flex items-start justify-between">
          <div className="p-3 bg-primary-light rounded-lg">
            <FileIcon size={24} className="text-primary" />
          </div>
          {file.classification?.confidence && (
            <div className="px-2 py-1 bg-primary-light rounded-lg">
              <span className="text-xs font-medium text-primary">
                {(file.classification.confidence * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>

        {/* File Info */}
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-text-primary truncate mb-1">{file.filename || 'Unnamed'}</h4>
          <p className="text-sm text-text-secondary truncate mb-2">
            {file.classification?.category || 'Uncategorized'}
          </p>
          
          {/* Tags */}
          {file.classification?.subcategories && file.classification.subcategories.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {file.classification.subcategories.slice(0, 2).map((tag, i) => (
                <span
                  key={i}
                  className="px-2 py-0.5 bg-surface text-text-muted rounded text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Meta Information */}
          <div className="flex flex-col gap-1 text-xs text-text-muted">
            <span className="flex items-center gap-1">
              <HardDrive size={12} />
              {formatSize(file.size)}
            </span>
            <span className="flex items-center gap-1">
              <Calendar size={12} />
              {formatDate(file.uploaded_at || file.created_at)}
            </span>
          </div>
        </div>

        {/* Analytics Button */}
        {hasAnalytics && (
          <button
            onClick={handleAnalyticsClick}
            className="flex items-center justify-center gap-2 px-3 py-2 bg-primary-light hover:bg-primary/10 text-primary rounded-lg transition-colors opacity-0 group-hover:opacity-100"
          >
            <BarChart3 size={14} />
            <span className="text-xs font-medium">View Analytics</span>
          </button>
        )}
      </div>
    </motion.div>
  );
});
FileCard.displayName = 'FileCard';

const Files = () => {
  const [files, setFiles] = useState([]);
  const [filteredFiles, setFilteredFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [selectedDateRange, setSelectedDateRange] = useState('all');
  const [selectedSizeRange, setSelectedSizeRange] = useState('all');
  const [sortBy, setSortBy] = useState('newest');
  const [selectedFile, setSelectedFile] = useState(null);

  // Debounce search query
  const searchTimeoutRef = useRef(null);
  const [debouncedQuery, setDebouncedQuery] = useState('');

  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    searchTimeoutRef.current = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 300);
    
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  useEffect(() => {
    loadFiles();
  }, []);

  useEffect(() => {
    applyFiltersAndSort();
  }, [files, debouncedQuery, selectedType, selectedDateRange, selectedSizeRange, sortBy]);

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

  const applyFiltersAndSort = useCallback(() => {
    let result = [...files];

    // Apply search filter
    if (debouncedQuery) {
      const query = debouncedQuery.toLowerCase();
      result = result.filter(file => 
        (file.filename || '').toLowerCase().includes(query)
      );
    }

    // Apply type filter
    if (selectedType !== 'all') {
      result = result.filter(file => 
        (file.classification?.type || 'unknown') === selectedType
      );
    }

    // Apply date range filter
    if (selectedDateRange !== 'all') {
      const now = new Date();
      const ranges = {
        today: 1,
        week: 7,
        month: 30
      };
      const daysAgo = ranges[selectedDateRange];
      if (daysAgo) {
        const cutoffDate = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000);
        result = result.filter(file => {
          const fileDate = new Date(file.uploaded_at || file.created_at);
          return fileDate >= cutoffDate;
        });
      }
    }

    // Apply size range filter
    if (selectedSizeRange !== 'all') {
      const MB = 1024 * 1024;
      const ranges = {
        small: [0, MB],
        medium: [MB, 10 * MB],
        large: [10 * MB, Infinity]
      };
      const [min, max] = ranges[selectedSizeRange] || [0, Infinity];
      result = result.filter(file => {
        const size = file.size || 0;
        return size >= min && size < max;
      });
    }

    // Apply sorting
    switch (sortBy) {
      case 'newest':
        result.sort((a, b) => {
          const dateA = new Date(a.uploaded_at || a.created_at || 0);
          const dateB = new Date(b.uploaded_at || b.created_at || 0);
          return dateB - dateA;
        });
        break;
      case 'oldest':
        result.sort((a, b) => {
          const dateA = new Date(a.uploaded_at || a.created_at || 0);
          const dateB = new Date(b.uploaded_at || b.created_at || 0);
          return dateA - dateB;
        });
        break;
      case 'largest':
        result.sort((a, b) => (b.size || 0) - (a.size || 0));
        break;
      case 'smallest':
        result.sort((a, b) => (a.size || 0) - (b.size || 0));
        break;
      case 'name-asc':
        result.sort((a, b) => 
          (a.filename || '').localeCompare(b.filename || '')
        );
        break;
      case 'name-desc':
        result.sort((a, b) => 
          (b.filename || '').localeCompare(a.filename || '')
        );
        break;
      default:
        break;
    }

    setFilteredFiles(result);
  }, [files, debouncedQuery, selectedType, selectedDateRange, selectedSizeRange, sortBy]);

  const handleSearchChange = useCallback((e) => {
    setSearchQuery(e.target.value);
  }, []);

  const handleFileSelect = useCallback((file) => {
    setSelectedFile(file);
  }, []);

  const handleClosePreview = useCallback(() => {
    setSelectedFile(null);
  }, []);

  const handleNavigate = useCallback((newFile) => {
    setSelectedFile(newFile);
  }, []);

  // Memoize type filters to avoid recalculation
  const typeFilters = useMemo(() => [
    { value: 'all', label: 'All Types', count: files.length },
    { value: 'image', label: 'Images', count: files.filter(f => f.classification?.type === 'image').length },
    { value: 'pdf', label: 'PDFs', count: files.filter(f => f.classification?.type === 'pdf').length },
    { value: 'text', label: 'Text', count: files.filter(f => f.classification?.type === 'text').length },
    { value: 'json', label: 'JSON', count: files.filter(f => f.classification?.type === 'json').length },
    { value: 'video', label: 'Videos', count: files.filter(f => f.classification?.type === 'video').length },
    { value: 'audio', label: 'Audio', count: files.filter(f => f.classification?.type === 'audio').length },
    { value: 'unknown', label: 'Other', count: files.filter(f => !f.classification?.type || f.classification?.type === 'unknown').length },
  ], [files]);

  return (
    <div className="flex-1 p-6 overflow-y-auto scrollbar-hide">
      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-6"
      >
        <h1 className="text-3xl font-bold mb-2">Files</h1>
        <p className="text-text-secondary">Manage and analyze your uploaded files</p>
      </motion.div>

      {/* Search and Filters */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-6 mb-6"
      >
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search Bar */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-muted" size={20} />
              <input
                type="text"
                placeholder="Search files by name..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="w-full pl-10 pr-4 py-3 bg-surface border border-border-color rounded-lg focus:outline-none focus:border-primary transition-colors"
              />
            </div>
          </div>

          {/* Filter Dropdowns */}
          <div className="flex flex-wrap gap-3">
            {/* Date Range Filter */}
            <select
              value={selectedDateRange}
              onChange={(e) => setSelectedDateRange(e.target.value)}
              className="px-4 py-3 bg-card-bg border border-border-color rounded-lg focus:outline-none focus:border-primary cursor-pointer"
            >
              <option value="all">All Dates</option>
              <option value="today">Today</option>
              <option value="week">Last 7 Days</option>
              <option value="month">Last 30 Days</option>
            </select>

            {/* Size Range Filter */}
            <select
              value={selectedSizeRange}
              onChange={(e) => setSelectedSizeRange(e.target.value)}
              className="px-4 py-3 bg-card-bg border border-border-color rounded-lg focus:outline-none focus:border-primary cursor-pointer"
            >
              <option value="all">All Sizes</option>
              <option value="small">Small (&lt;1MB)</option>
              <option value="medium">Medium (1-10MB)</option>
              <option value="large">Large (&gt;10MB)</option>
            </select>

            {/* Sort Dropdown */}
            <div className="relative">
              <SortAsc className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-muted pointer-events-none" size={20} />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="pl-10 pr-8 py-3 bg-card-bg border border-border-color rounded-lg focus:outline-none focus:border-primary cursor-pointer appearance-none"
              >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="largest">Largest First</option>
                <option value="smallest">Smallest First</option>
                <option value="name-asc">A → Z</option>
                <option value="name-desc">Z → A</option>
              </select>
            </div>
          </div>
        </div>

        {/* Type Filters */}
        <div className="flex flex-wrap gap-2 mt-4">
          {typeFilters.map((filter) => (
            <button
              key={filter.value}
              onClick={() => setSelectedType(filter.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                selectedType === filter.value
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-surface text-text-secondary border border-border-color hover:border-primary'
              }`}
            >
              {filter.label} ({filter.count})
            </button>
          ))}
        </div>
      </motion.div>

      {/* Files Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="text-text-secondary mt-4">Loading files...</p>
        </div>
      ) : filteredFiles.length === 0 ? (
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="glass-card p-12 text-center"
        >
          <File size={64} className="mx-auto text-text-muted mb-4" />
          <h3 className="text-xl font-semibold mb-2">No files found</h3>
          <p className="text-text-secondary">
            {searchQuery || selectedType !== 'all'
              ? 'Try adjusting your filters or search query'
              : 'Upload your first file to get started'}
          </p>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredFiles.map((file, index) => (
            <FileCard
              key={file.id || index}
              file={file}
              index={index}
              onSelect={handleFileSelect}
            />
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {selectedFile && (
        <PreviewModal
          file={selectedFile}
          files={filteredFiles}
          onClose={handleClosePreview}
          onNavigate={handleNavigate}
        />
      )}
    </div>
  );
};

export default Files;

