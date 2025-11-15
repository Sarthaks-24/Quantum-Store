import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Search, 
  Filter,
  SortAsc,
  Image as ImageIcon,
  FileText,
  Video,
  Music,
  Database,
  File,
  Calendar,
  HardDrive
} from 'lucide-react';
import { fetchFiles } from '../../api';
import PreviewModal from './PreviewModal';

const Files = () => {
  const [files, setFiles] = useState([]);
  const [filteredFiles, setFilteredFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [sortBy, setSortBy] = useState('newest');
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    loadFiles();
  }, []);

  useEffect(() => {
    applyFiltersAndSort();
  }, [files, searchQuery, selectedType, sortBy]);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const data = await fetchFiles();
      setFiles(data);
    } catch (error) {
      console.error('Failed to load files:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFiltersAndSort = () => {
    let result = [...files];

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
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
      case 'size':
        result.sort((a, b) => (b.size || 0) - (a.size || 0));
        break;
      case 'name':
        result.sort((a, b) => 
          (a.filename || '').localeCompare(b.filename || '')
        );
        break;
      default:
        break;
    }

    setFilteredFiles(result);
  };

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

  const typeFilters = [
    { value: 'all', label: 'All Types', count: files.length },
    { value: 'image', label: 'Images', count: files.filter(f => f.classification?.type === 'image').length },
    { value: 'pdf', label: 'PDFs', count: files.filter(f => f.classification?.type === 'pdf').length },
    { value: 'text', label: 'Text', count: files.filter(f => f.classification?.type === 'text').length },
    { value: 'json', label: 'JSON', count: files.filter(f => f.classification?.type === 'json').length },
    { value: 'video', label: 'Videos', count: files.filter(f => f.classification?.type === 'video').length },
    { value: 'audio', label: 'Audio', count: files.filter(f => f.classification?.type === 'audio').length },
    { value: 'unknown', label: 'Other', count: files.filter(f => !f.classification?.type || f.classification?.type === 'unknown').length },
  ];

  return (
    <div className="flex-1 p-6 overflow-y-auto scrollbar-hide">
      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-6"
      >
        <h1 className="text-3xl font-bold mb-2">Files</h1>
        <p className="text-white/60">Manage and analyze your uploaded files</p>
      </motion.div>

      {/* Search and Filters */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-6 rounded-2xl mb-6"
      >
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search Bar */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/40" size={20} />
              <input
                type="text"
                placeholder="Search files by name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:border-accent-indigo transition-colors"
              />
            </div>
          </div>

          {/* Sort Dropdown */}
          <div className="flex gap-3">
            <div className="relative">
              <SortAsc className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/40" size={20} />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="pl-10 pr-8 py-3 bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:border-accent-teal cursor-pointer appearance-none"
              >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="size">Largest First</option>
                <option value="name">A-Z</option>
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
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                selectedType === filter.value
                  ? 'bg-accent-indigo text-white'
                  : 'bg-white/5 text-white/60 hover:bg-white/10'
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
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-accent-indigo border-t-transparent mx-auto"></div>
          <p className="text-white/60 mt-4">Loading files...</p>
        </div>
      ) : filteredFiles.length === 0 ? (
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="glass-card p-12 rounded-2xl text-center"
        >
          <File size={64} className="mx-auto text-white/30 mb-4" />
          <h3 className="text-xl font-semibold mb-2">No files found</h3>
          <p className="text-white/60">
            {searchQuery || selectedType !== 'all'
              ? 'Try adjusting your filters or search query'
              : 'Upload your first file to get started'}
          </p>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredFiles.map((file, index) => {
            const FileIcon = getFileIcon(file.classification?.type);
            
            return (
              <motion.div
                key={file.id || index}
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: index * 0.02 }}
                whileHover={{ scale: 1.02 }}
                onClick={() => setSelectedFile(file)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setSelectedFile(file);
                  }
                }}
                className="glass-card-hover p-4 cursor-pointer"
                role="button"
                tabIndex={0}
                aria-label={`View ${file.filename}`}
              >
                <div className="flex items-start gap-3">
                  <div className="p-3 bg-accent-indigo/20 rounded-xl flex-shrink-0">
                    <FileIcon size={24} className="text-accent-indigo" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium truncate mb-1">{file.filename || 'Unnamed'}</h4>
                    <p className="text-sm text-white/60 truncate mb-2">
                      {file.classification?.category || 'Uncategorized'}
                    </p>
                    <div className="flex items-center gap-3 text-xs text-white/40">
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
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Preview Modal */}
      {selectedFile && (
        <PreviewModal
          file={selectedFile}
          onClose={() => setSelectedFile(null)}
        />
      )}
    </div>
  );
};

export default Files;
