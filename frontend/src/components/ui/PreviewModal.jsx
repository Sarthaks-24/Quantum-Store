import React, { useState, useEffect, useRef } from 'react';
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
  ExternalLink,
  ZoomIn,
  ZoomOut,
  RotateCcw
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
  
  // Zoom and pan state
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panPosition, setPanPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const imageContainerRef = useRef(null);
  const touchStartRef = useRef({ distance: 0, center: { x: 0, y: 0 } });

  // Find current file index
  const currentIndex = files.findIndex(f => f.id === file.id);
  const hasPrevious = currentIndex > 0;
  const hasNext = currentIndex < files.length - 1;

  useEffect(() => {
    loadPreview();
    // Reset analytics and zoom when file changes
    setAnalytics(null);
    setActiveTab('preview');
    resetZoom();
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
    // Use classification type or fall back to file_type
    const fileType = file.classification?.type || file.file_type;
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

  // Zoom and Pan functions
  const resetZoom = () => {
    setZoomLevel(1);
    setPanPosition({ x: 0, y: 0 });
  };

  const zoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 0.25, 4.0));
  };

  const zoomOut = () => {
    setZoomLevel(prev => {
      const newZoom = Math.max(prev - 0.25, 0.5);
      if (newZoom === 1) {
        setPanPosition({ x: 0, y: 0 });
      }
      return newZoom;
    });
  };

  const handleWheel = (e) => {
    if (!imageContainerRef.current) return;
    
    e.preventDefault();
    
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    const multiplier = e.ctrlKey ? 2 : 1;
    
    if (e.shiftKey) {
      // Horizontal pan with shift
      setPanPosition(prev => ({ ...prev, x: prev.x - e.deltaY }));
    } else {
      // Zoom
      setZoomLevel(prev => Math.min(Math.max(prev + delta * multiplier, 0.5), 4.0));
    }
  };

  const handleMouseDown = (e) => {
    if (zoomLevel <= 1) return;
    e.preventDefault();
    setIsDragging(true);
    setDragStart({ x: e.clientX - panPosition.x, y: e.clientY - panPosition.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    e.preventDefault();
    setPanPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleTouchStart = (e) => {
    if (e.touches.length === 2) {
      // Two-finger pinch
      const touch1 = e.touches[0];
      const touch2 = e.touches[1];
      const distance = Math.hypot(
        touch2.clientX - touch1.clientX,
        touch2.clientY - touch1.clientY
      );
      touchStartRef.current = {
        distance,
        center: {
          x: (touch1.clientX + touch2.clientX) / 2,
          y: (touch1.clientY + touch2.clientY) / 2
        }
      };
    } else if (e.touches.length === 1 && zoomLevel > 1) {
      // Single-finger drag when zoomed
      const touch = e.touches[0];
      setIsDragging(true);
      setDragStart({ x: touch.clientX - panPosition.x, y: touch.clientY - panPosition.y });
    }
  };

  const handleTouchMove = (e) => {
    if (e.touches.length === 2) {
      // Pinch zoom
      e.preventDefault();
      const touch1 = e.touches[0];
      const touch2 = e.touches[1];
      const distance = Math.hypot(
        touch2.clientX - touch1.clientX,
        touch2.clientY - touch1.clientY
      );
      
      const scale = distance / touchStartRef.current.distance;
      const newZoom = Math.min(Math.max(zoomLevel * scale, 0.5), 4.0);
      setZoomLevel(newZoom);
      
      touchStartRef.current.distance = distance;
    } else if (e.touches.length === 1 && isDragging) {
      // Pan while zoomed
      e.preventDefault();
      const touch = e.touches[0];
      setPanPosition({
        x: touch.clientX - dragStart.x,
        y: touch.clientY - dragStart.y
      });
    }
  };

  const handleTouchEnd = () => {
    setIsDragging(false);
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
    // Use classification type or fall back to file_type
    const type = file.classification?.type || file.file_type;
    switch (type) {
      case 'image': return ImageIcon;
      case 'pdf': return FileText;
      case 'video': return Video;
      case 'audio': return Music;
      case 'json': return Database;
      case 'text': return FileText;
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

    // Check if string is Base64 image data
    const isBase64Image = (value) => {
      if (typeof value !== 'string') return false;
      // Check if it looks like Base64 (contains only valid Base64 characters and is reasonably long)
      const base64Pattern = /^[A-Za-z0-9+/=]{100,}$/;
      return base64Pattern.test(value.replace(/\s/g, ''));
    };

    const renderValue = (key, value) => {
      // Special handling for preview field (Base64 image)
      if ((key === 'preview' || key.includes('thumbnail') || key.includes('image')) && isBase64Image(value)) {
        return (
          <div className="mt-2 relative">
            {/* Zoom Controls */}
            <div className="absolute top-2 right-2 z-10 backdrop-blur-md bg-white/10 rounded-xl shadow-lg px-3 py-1 flex gap-2">
              <button
                onClick={zoomIn}
                disabled={zoomLevel >= 4.0}
                className="p-1 hover:bg-white/20 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Zoom in"
              >
                <ZoomIn size={18} />
              </button>
              <button
                onClick={zoomOut}
                disabled={zoomLevel <= 0.5}
                className="p-1 hover:bg-white/20 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Zoom out"
              >
                <ZoomOut size={18} />
              </button>
              <button
                onClick={resetZoom}
                className="p-1 hover:bg-white/20 rounded transition-colors"
                aria-label="Reset zoom"
              >
                <RotateCcw size={18} />
              </button>
            </div>
            
            {/* Image Container with Pan/Zoom */}
            <div 
              ref={imageContainerRef}
              className="overflow-hidden rounded-lg border border-white/10 max-h-96 flex items-center justify-center bg-black/20"
              style={{ cursor: zoomLevel > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default' }}
              onWheel={handleWheel}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onTouchStart={handleTouchStart}
              onTouchMove={handleTouchMove}
              onTouchEnd={handleTouchEnd}
            >
              <img 
                src={`data:image/png;base64,${value}`}
                alt="Preview"
                className="max-w-full max-h-96 object-contain select-none"
                style={{
                  transform: `scale(${zoomLevel}) translate(${panPosition.x / zoomLevel}px, ${panPosition.y / zoomLevel}px)`,
                  transition: isDragging ? 'none' : 'transform 150ms ease',
                  pointerEvents: 'none'
                }}
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.parentElement.nextSibling.style.display = 'block';
                }}
                draggable={false}
              />
            </div>
            <div style={{ display: 'none' }} className="text-sm text-white/40 italic mt-2">
              Preview image failed to load
            </div>
          </div>
        );
      }

      // Special handling for text field (extracted text, OCR output)
      if ((key === 'text' || key === 'extracted_text' || key === 'ocr_text') && typeof value === 'string' && value.length > 300) {
        const isExpanded = expandedFields[key];
        const displayText = isExpanded ? value : value.substring(0, 300) + '...';
        
        return (
          <div>
            <div className="text-sm font-mono text-white/80 whitespace-pre-wrap break-words max-h-64 overflow-y-auto p-3 bg-white/5 rounded-lg border border-white/10">
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

      // Long text handling (non-Base64)
      if (typeof value === 'string' && value.length > 400 && !isBase64Image(value)) {
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
      
      // Percentage values
      if (typeof value === 'number' && value < 1 && value > 0) {
        return `${(value * 100).toFixed(1)}%`;
      }
      
      // Regular string values
      if (typeof value === 'string') {
        return <div className="text-lg font-semibold whitespace-pre-wrap break-words">{value}</div>;
      }
      
      // Other values
      return <div className="text-lg font-semibold">{String(value)}</div>;
    };

    return (
      <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
        <h3 className="text-lg font-semibold mb-4">Analytics Results</h3>
        <div className="grid grid-cols-1 gap-4">
          {Object.entries(analytics).filter(([key, value]) => key !== 'error' && typeof value !== 'object').length === 0 ? (
            <div className="text-center py-8">
              <p className="text-white/60">No scalar analytics data available</p>
            </div>
          ) : (
            Object.entries(analytics).map(([key, value]) => {
              if (key === 'error' || typeof value === 'object') return null;
              
              return (
                <div key={key} className="glass-card p-4 rounded-xl">
                  <div className="text-white/60 text-sm mb-2 capitalize">
                    {key.replace(/_/g, ' ')}
                  </div>
                  {renderValue(key, value)}
                </div>
              );
            })
          )}
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
                      {file.classification?.type || file.file_type || 'unknown'}
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
                      <p className="text-lg font-semibold capitalize">{file.classification?.type || file.file_type || 'Unknown'}</p>
                    </div>
                  </div>

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
