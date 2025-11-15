import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Download, 
  FileText, 
  Image as ImageIcon, 
  Video, 
  Music, 
  Database,
  Calendar,
  HardDrive,
  Tag,
  AlertCircle,
  BarChart3,
  Eye,
  ChevronLeft,
  ChevronRight,
  ExternalLink
} from 'lucide-react';
import { fetchFilePreview, downloadFile, fetchFileAnalytics } from '../../api';

const PreviewModal = ({ file, files = [], onClose, onNavigate }) => {
  const [activeTab, setActiveTab] = useState('preview');
  const [preview, setPreview] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [expandedFields, setExpandedFields] = useState({});

  // Find current file index
  const currentIndex = files.findIndex(f => f.id === file.id);
  const hasPrevious = currentIndex > 0;
  const hasNext = currentIndex < files.length - 1;

  useEffect(() => {
    loadPreview();
    // Reset analytics when file changes
    setAnalytics(null);
    setActiveTab('preview');
  }, [file.id]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowLeft' && hasPrevious && onNavigate) {
        e.preventDefault();
        onNavigate(files[currentIndex - 1]);
      } else if (e.key === 'ArrowRight' && hasNext && onNavigate) {
        e.preventDefault();
        onNavigate(files[currentIndex + 1]);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, currentIndex, hasPrevious, hasNext, files, onNavigate]);

  useEffect(() => {
    if (activeTab === 'analytics' && !analytics && !loadingAnalytics) {
      loadAnalytics();
    }
  }, [activeTab]);

  const loadPreview = async () => {
    setLoading(true);
    try {
      const data = await fetchFilePreview(file.id);
      setPreview(data);
    } catch (error) {
      console.error('Failed to load preview:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    const fileType = file.classification?.type;
    if (!fileType || fileType === 'unknown') {
      setAnalytics({ error: 'Analytics not available for this file type' });
      return;
    }

    setLoadingAnalytics(true);
    try {
      const data = await fetchFileAnalytics(file.id, fileType);
      setAnalytics(data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
      setAnalytics({ error: 'Failed to load analytics' });
    } finally {
      setLoadingAnalytics(false);
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadFile(file.id, file.filename);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    } finally {
      setDownloading(false);
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
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getFileIcon = () => {
    const type = file.classification?.type;
    switch (type) {
      case 'image': return ImageIcon;
      case 'pdf': return FileText;
      case 'video': return Video;
      case 'audio': return Music;
      case 'json': return Database;
      default: return FileText;
    }
  };

  const FileIconComponent = getFileIcon();

  const renderAnalyticsContent = () => {
    if (loadingAnalytics) {
      return (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-accent-indigo border-t-transparent mx-auto"></div>
          <p className="text-white/60 mt-4">Loading analytics...</p>
        </div>
      );
    }

    if (analytics?.error) {
      return (
        <div className="text-center py-12">
          <AlertCircle size={48} className="mx-auto text-amber-400 mb-3" />
          <p className="text-white/60">{analytics.error}</p>
        </div>
      );
    }

    if (!analytics) {
      return (
        <div className="text-center py-12">
          <p className="text-white/60">No analytics data available</p>
        </div>
      );
    }

    const toggleExpand = (key) => {
      setExpandedFields(prev => ({
        ...prev,
        [key]: !prev[key]
      }));
    };

    const renderValue = (key, value) => {
      if (typeof value === 'string' && value.length > 400) {
        const isExpanded = expandedFields[key];
        const displayText = isExpanded ? value : value.substring(0, 400) + '...';
        
        return (
          <div>
            <div className="text-sm font-medium whitespace-pre-wrap break-words max-h-64 overflow-y-auto">
              {displayText}
            </div>
            <button
              onClick={() => toggleExpand(key)}
              className="mt-2 px-3 py-1 bg-accent-indigo/20 hover:bg-accent-indigo/30 text-accent-indigo rounded-lg text-xs font-medium transition-colors"
            >
              {isExpanded ? 'Show Less' : 'Show More'}
            </button>
          </div>
        );
      }
      
      if (typeof value === 'number' && value < 1 && value > 0) {
        return `${(value * 100).toFixed(1)}%`;
      }
      
      if (typeof value === 'string') {
        return <div className="text-lg font-semibold whitespace-pre-wrap break-words">{value}</div>;
      }
      
      return <div className="text-lg font-semibold">{String(value)}</div>;
    };

    return (
      <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
        <h3 className="text-lg font-semibold mb-4">Analytics Results</h3>
        <div className="grid grid-cols-1 gap-4">
          {Object.entries(analytics).map(([key, value]) => {
            if (key === 'error' || typeof value === 'object') return null;
            
            return (
              <div key={key} className="glass-card p-4 rounded-xl">
                <div className="text-white/60 text-sm mb-2 capitalize">
                  {key.replace(/_/g, ' ')}
                </div>
                {renderValue(key, value)}
              </div>
            );
          })}
        </div>

        {Object.entries(analytics).some(([, value]) => typeof value === 'object' && value !== null) && (
          <div className="glass-card p-4 rounded-xl mt-4">
            <h4 className="text-sm font-semibold text-white/80 mb-3">Additional Data</h4>
            <div className="max-h-64 overflow-y-auto">
              <pre className="text-xs text-white/60 whitespace-pre-wrap break-words">
                {JSON.stringify(
                  Object.fromEntries(
                    Object.entries(analytics).filter(([, value]) => typeof value === 'object' && value !== null)
                  ),
                  null,
                  2
                )}
              </pre>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          transition={{ type: 'spring', damping: 25 }}
          className="glass-card max-w-4xl w-full max-h-[90vh] overflow-y-auto scrollbar-hide"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 bg-bg-gradient-start/90 backdrop-blur-md p-6 border-b border-white/10">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start gap-4 flex-1">
                <div className="p-3 bg-accent-indigo/20 rounded-xl">
                  <FileIconComponent size={28} className="text-accent-indigo" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h2 className="text-2xl font-bold truncate">{file.filename}</h2>
                    <span className="px-2 py-1 bg-white/5 rounded text-xs text-white/50 capitalize">
                      {file.classification?.type || 'unknown'}
                    </span>
                  </div>
                  <p className="text-white/60 text-sm mt-1">
                    {file.classification?.category || 'Uncategorized'}
                  </p>
                  {file.classification?.subcategories && file.classification.subcategories.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {file.classification.subcategories.slice(0, 3).map((tag, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-accent-teal/20 text-accent-teal rounded-lg text-xs font-medium"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              
              {/* Navigation and Close Buttons */}
              <div className="flex items-center gap-2">
                {files.length > 1 && (
                  <>
                    <button
                      onClick={() => hasPrevious && onNavigate && onNavigate(files[currentIndex - 1])}
                      disabled={!hasPrevious}
                      className={`p-2 rounded-xl transition-colors ${
                        hasPrevious 
                          ? 'hover:bg-white/10 text-white' 
                          : 'text-white/30 cursor-not-allowed'
                      }`}
                      aria-label="Previous file"
                    >
                      <ChevronLeft size={24} />
                    </button>
                    <span className="text-white/40 text-sm">
                      {currentIndex + 1} / {files.length}
                    </span>
                    <button
                      onClick={() => hasNext && onNavigate && onNavigate(files[currentIndex + 1])}
                      disabled={!hasNext}
                      className={`p-2 rounded-xl transition-colors ${
                        hasNext 
                          ? 'hover:bg-white/10 text-white' 
                          : 'text-white/30 cursor-not-allowed'
                      }`}
                      aria-label="Next file"
                    >
                      <ChevronRight size={24} />
                    </button>
                  </>
                )}
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/10 rounded-xl transition-colors"
                  aria-label="Close preview"
                >
                  <X size={24} />
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('preview')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all ${
                  activeTab === 'preview'
                    ? 'bg-accent-indigo text-white'
                    : 'bg-white/5 text-white/60 hover:bg-white/10'
                }`}
              >
                <Eye size={18} />
                Preview
              </button>
              <button
                onClick={() => setActiveTab('analytics')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all ${
                  activeTab === 'analytics'
                    ? 'bg-accent-indigo text-white'
                    : 'bg-white/5 text-white/60 hover:bg-white/10'
                }`}
              >
                <BarChart3 size={18} />
                Analytics
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 max-h-[calc(90vh-200px)] overflow-y-auto">
            {activeTab === 'preview' ? (
              loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-accent-indigo border-t-transparent mx-auto"></div>
                  <p className="text-white/60 mt-4">Loading preview...</p>
                </div>
              ) : preview?.error ? (
                <div className="text-center py-12">
                  <AlertCircle size={48} className="mx-auto text-red-400 mb-3" />
                  <p className="text-white/60">Preview unavailable</p>
                  <p className="text-white/40 text-sm mt-2">{preview.message}</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Metadata Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="glass-card p-4 rounded-xl">
                      <div className="flex items-center gap-3 mb-2">
                        <HardDrive size={18} className="text-accent-teal" />
                        <span className="text-white/60 text-sm">File Size</span>
                      </div>
                      <p className="text-lg font-semibold">{formatSize(file.size)}</p>
                    </div>

                    <div className="glass-card p-4 rounded-xl">
                      <div className="flex items-center gap-3 mb-2">
                        <Calendar size={18} className="text-accent-indigo" />
                        <span className="text-white/60 text-sm">Uploaded</span>
                      </div>
                      <p className="text-lg font-semibold">{formatDate(file.uploaded_at)}</p>
                    </div>

                    {file.classification?.confidence && (
                      <div className="glass-card p-4 rounded-xl">
                        <div className="flex items-center gap-3 mb-2">
                          <Tag size={18} className="text-accent-teal" />
                          <span className="text-white/60 text-sm">Confidence</span>
                        </div>
                        <p className="text-lg font-semibold">
                          {(file.classification.confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                    )}

                    <div className="glass-card p-4 rounded-xl">
                      <div className="flex items-center gap-3 mb-2">
                        <FileText size={18} className="text-accent-indigo" />
                        <span className="text-white/60 text-sm">Type</span>
                      </div>
                      <p className="text-lg font-semibold capitalize">{file.classification?.type || 'Unknown'}</p>
                    </div>
                  </div>

                  {/* Preview Content */}
                  {preview && (
                    <div className="glass-card p-6 rounded-xl">
                      <h3 className="text-lg font-semibold mb-4">Analysis Results</h3>
                      
                      {/* Image Preview */}
                      {file.classification?.type === 'image' && preview.width && (
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-white/60">Dimensions:</span>
                              <span className="ml-2 font-medium">{preview.width} x {preview.height}</span>
                            </div>
                            <div>
                              <span className="text-white/60">Format:</span>
                              <span className="ml-2 font-medium">{preview.format || 'N/A'}</span>
                            </div>
                            {preview.has_exif !== undefined && (
                              <div>
                                <span className="text-white/60">EXIF Data:</span>
                                <span className="ml-2 font-medium">{preview.has_exif ? 'Yes' : 'No'}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* PDF Preview */}
                      {file.classification?.type === 'pdf' && (
                        <div className="space-y-3 text-sm">
                          {preview.page_count && (
                            <div>
                              <span className="text-white/60">Pages:</span>
                              <span className="ml-2 font-medium">{preview.page_count}</span>
                            </div>
                          )}
                          {preview.text_length && (
                            <div>
                              <span className="text-white/60">Text Length:</span>
                              <span className="ml-2 font-medium">{preview.text_length.toLocaleString()} chars</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* JSON Preview */}
                      {file.classification?.type === 'json' && preview.record_count !== undefined && (
                        <div className="space-y-3 text-sm">
                          <div>
                            <span className="text-white/60">Records:</span>
                            <span className="ml-2 font-medium">{preview.record_count}</span>
                          </div>
                          {preview.field_consistency && (
                            <div>
                              <span className="text-white/60">Consistency:</span>
                              <span className="ml-2 font-medium">{(preview.field_consistency * 100).toFixed(0)}%</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Audio/Video Preview */}
                      {(file.classification?.type === 'audio' || file.classification?.type === 'video') && preview.duration_seconds && (
                        <div className="space-y-3 text-sm">
                          <div>
                            <span className="text-white/60">Duration:</span>
                            <span className="ml-2 font-medium">{preview.duration_formatted || `${preview.duration_seconds}s`}</span>
                          </div>
                          {preview.width && preview.height && (
                            <div>
                              <span className="text-white/60">Resolution:</span>
                              <span className="ml-2 font-medium">{preview.width} x {preview.height}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-3">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleDownload}
                      disabled={downloading}
                      className="btn-primary flex-1 flex items-center justify-center gap-2"
                    >
                      <Download size={20} />
                      {downloading ? 'Downloading...' : 'Download File'}
                    </motion.button>
                    
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={onClose}
                      className="px-6 py-3 bg-white/10 rounded-xl font-medium transition-all hover:bg-white/20"
                    >
                      Close
                    </motion.button>
                  </div>
                </div>
              )
            ) : (
              renderAnalyticsContent()
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default PreviewModal;
