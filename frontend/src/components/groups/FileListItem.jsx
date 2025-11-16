import React, { useCallback } from 'react';
import { motion } from 'framer-motion';
import { 
  File as FileIcon,
  FileText,
  Image as ImageIcon,
  FileJson,
  FileCode,
  Video,
  Music
} from 'lucide-react';

/**
 * FileListItem - Shared file card component
 * Used in both Files tab and GroupsExplorer
 * 
 * Props:
 * - file: File object with metadata
 * - onSelect: Callback when file is clicked
 * - index: For stagger animation
 * - compact: Compact mode for groups view
 */

const getFileIcon = (type) => {
  switch (type) {
    case 'image': return ImageIcon;
    case 'pdf': return FileText;
    case 'video': return Video;
    case 'audio': return Music;
    case 'json': return FileJson;
    case 'text': 
    case 'code': return FileCode;
    default: return FileIcon;
  }
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

const FileListItem = React.memo(({ file, onSelect, index = 0, compact = false }) => {
  const FileIconComponent = getFileIcon(file.classification?.type || file.file_type);
  const fileType = file.classification?.type || file.file_type || 'unknown';
  const confidence = file.classification?.confidence;

  const handleClick = useCallback(() => {
    onSelect(file);
  }, [file, onSelect]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(file);
    }
  }, [file, onSelect]);

  if (compact) {
    // Compact mode for groups view
    return (
      <motion.div
        initial={{ x: -20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: index * 0.03 }}
        whileHover={{ x: 4 }}
        className="flex items-center gap-3 p-3 bg-white/5 hover:bg-white/10 rounded-xl cursor-pointer transition-colors group"
        role="button"
        tabIndex={0}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        aria-label={`View ${file.filename}`}
      >
        <div className="p-2 bg-accent-indigo/20 rounded-lg group-hover:bg-accent-indigo/30 transition-colors">
          <FileIconComponent size={18} className="text-accent-indigo" />
        </div>
        
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white/90 truncate">
            {file.filename}
          </p>
          <p className="text-xs text-white/50">
            {formatSize(file.file_size)} • {formatDate(file.upload_date)}
          </p>
        </div>

        {confidence && (
          <div className="px-2 py-1 bg-accent-teal/20 rounded-lg">
            <span className="text-xs font-medium text-accent-teal">
              {(confidence * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </motion.div>
    );
  }

  // Full card mode (same as Files tab)
  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: index * 0.02 }}
      whileHover={{ scale: 1.02 }}
      className="glass-card-hover p-4 cursor-pointer group"
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`View ${file.filename}`}
    >
      <div className="flex flex-col gap-3">
        {/* File Icon Header */}
        <div className="flex items-start justify-between">
          <div className="p-3 bg-accent-indigo/20 rounded-xl">
            <FileIconComponent size={28} className="text-accent-indigo" />
          </div>
          {confidence && (
            <div className="px-2 py-1 bg-accent-teal/20 rounded-lg">
              <span className="text-xs font-medium text-accent-teal">
                {(confidence * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>

        {/* File Info */}
        <div>
          <h3 className="text-sm font-semibold text-white/90 truncate mb-1">
            {file.filename}
          </h3>
          <div className="flex items-center gap-2 text-xs text-white/60">
            <span>{formatSize(file.file_size)}</span>
            <span>•</span>
            <span>{formatDate(file.upload_date)}</span>
          </div>
        </div>

        {/* Category Badge */}
        {file.classification?.category && (
          <div className="mt-1">
            <span className="inline-block px-2 py-1 bg-accent-purple/20 rounded-lg text-xs font-medium text-accent-purple">
              {file.classification.category.replace(/_/g, ' ')}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
});

FileListItem.displayName = 'FileListItem';

export default FileListItem;
