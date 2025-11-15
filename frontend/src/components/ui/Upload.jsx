import React, { useState, useRef, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
  Upload as UploadIcon, 
  X, 
  CheckCircle, 
  AlertCircle,
  File,
  Image as ImageIcon,
  FileText,
  Video,
  Music,
  Database
} from 'lucide-react';
import { uploadFiles } from '../../api';

// Utility functions (pure, moved outside component)
const formatSize = (bytes) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const getFileIcon = (type) => {
  if (type.startsWith('image/')) return ImageIcon;
  if (type.startsWith('video/')) return Video;
  if (type.startsWith('audio/')) return Music;
  if (type.includes('pdf')) return FileText;
  if (type.includes('json')) return Database;
  if (type.startsWith('text/')) return FileText;
  return File;
};

const Upload = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({});
  const [uploadResults, setUploadResults] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const addFiles = useCallback((files) => {
    const newFiles = files.map((file, index) => ({
      id: `${Date.now()}-${index}`,
      file,
      name: file.name,
      size: file.size,
      type: file.type,
    }));
    setSelectedFiles(prev => [...prev, ...newFiles]);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
  }, [addFiles]);

  const handleFileSelect = useCallback((e) => {
    const files = Array.from(e.target.files);
    addFiles(files);
  }, [addFiles]);

  const removeFile = useCallback((id) => {
    setSelectedFiles(prev => prev.filter(f => f.id !== id));
  }, []);

  const handleUpload = useCallback(async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setUploadResults([]);

    const filesToUpload = selectedFiles.map(f => f.file);
    
    const results = await uploadFiles(filesToUpload, (fileIndex, progress) => {
      setUploadProgress(prev => ({
        ...prev,
        [fileIndex]: progress
      }));
    });

    setUploadResults(results);
    setIsUploading(false);
  }, [selectedFiles]);

  const handleViewFile = useCallback(() => {
    // Navigate to files page with the uploaded file
    navigate('/files');
  }, [navigate]);

  const handleReset = useCallback(() => {
    setSelectedFiles([]);
    setUploadProgress({});
    setUploadResults([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const successCount = useMemo(() => 
    uploadResults.filter(r => r.success).length,
    [uploadResults]
  );
  
  const failCount = useMemo(() => 
    uploadResults.filter(r => !r.success).length,
    [uploadResults]
  );

  return (
    <div className="flex-1 p-6 overflow-y-auto scrollbar-hide">
      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-6"
      >
        <h1 className="text-3xl font-bold mb-2">Upload Files</h1>
        <p className="text-white/60">Upload and classify your files with advanced analytics</p>
      </motion.div>

      {uploadResults.length === 0 ? (
        <>
          {/* Drop Zone */}
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1 }}
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`glass-card p-12 rounded-2xl mb-6 transition-all duration-300 ${
              isDragging ? 'border-2 border-accent-indigo bg-accent-indigo/10 scale-105' : 'border-2 border-dashed border-white/20'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              disabled={isUploading}
            />

            <div className="text-center">
              <motion.div
                animate={isDragging ? { scale: 1.2, rotate: 10 } : { scale: 1, rotate: 0 }}
                className="inline-block mb-4"
              >
                <UploadIcon size={64} className={isDragging ? 'text-accent-indigo' : 'text-white/40'} />
              </motion.div>

              <h3 className="text-xl font-semibold mb-2">
                {isDragging ? 'Drop files here' : 'Drag & drop files here'}
              </h3>
              <p className="text-white/60 mb-6">or</p>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="btn-primary"
              >
                Browse Files
              </motion.button>

              <p className="text-white/40 text-sm mt-4">
                Supports images, PDFs, JSON, videos, audio, and text files
              </p>
            </div>
          </motion.div>

          {/* Selected Files */}
          {selectedFiles.length > 0 && (
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className="glass-card p-6 rounded-2xl mb-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">
                  Selected Files ({selectedFiles.length})
                </h3>
                <button
                  onClick={handleReset}
                  className="text-white/60 hover:text-white transition-colors text-sm"
                >
                  Clear All
                </button>
              </div>

              <div className="space-y-3 mb-6 max-h-64 overflow-y-auto scrollbar-hide">
                {selectedFiles.map((fileItem, index) => {
                  const FileIcon = getFileIcon(fileItem.type);
                  const progress = uploadProgress[index] || 0;

                  return (
                    <motion.div
                      key={fileItem.id}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex items-center gap-3 p-3 bg-white/5 rounded-xl"
                    >
                      <div className="p-2 bg-accent-teal/20 rounded-lg">
                        <FileIcon size={20} className="text-accent-teal" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{fileItem.name}</p>
                        <p className="text-sm text-white/60">{formatSize(fileItem.size)}</p>
                        
                        {isUploading && (
                          <div className="mt-2">
                            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${progress}%` }}
                                className="h-full bg-gradient-to-r from-accent-indigo to-accent-teal"
                                transition={{ duration: 0.3 }}
                              />
                            </div>
                          </div>
                        )}
                      </div>

                      {!isUploading && (
                        <button
                          onClick={() => removeFile(fileItem.id)}
                          className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                          aria-label="Remove file"
                        >
                          <X size={18} className="text-white/60" />
                        </button>
                      )}
                    </motion.div>
                  );
                })}
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleUpload}
                disabled={isUploading}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {isUploading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    Uploading...
                  </>
                ) : (
                  <>
                    <UploadIcon size={20} />
                    Upload {selectedFiles.length} File{selectedFiles.length !== 1 ? 's' : ''}
                  </>
                )}
              </motion.button>
            </motion.div>
          )}
        </>
      ) : (
        /* Upload Results */
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="glass-card p-8 rounded-2xl"
        >
          <div className="text-center mb-6">
            {failCount === 0 ? (
              <>
                <CheckCircle size={64} className="mx-auto text-green-400 mb-4" />
                <h2 className="text-2xl font-bold mb-2">Upload Successful!</h2>
                <p className="text-white/60">
                  {successCount} file{successCount !== 1 ? 's' : ''} uploaded and classified
                </p>
              </>
            ) : (
              <>
                <AlertCircle size={64} className="mx-auto text-amber-400 mb-4" />
                <h2 className="text-2xl font-bold mb-2">Upload Complete</h2>
                <p className="text-white/60">
                  {successCount} succeeded, {failCount} failed
                </p>
              </>
            )}
          </div>

          <div className="space-y-3 mb-6 max-h-96 overflow-y-auto scrollbar-hide">
            {uploadResults.map((result, index) => (
              <motion.div
                key={index}
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: index * 0.05 }}
                className={`flex items-center gap-3 p-4 rounded-xl ${
                  result.success ? 'bg-green-500/10' : 'bg-red-500/10'
                }`}
              >
                {result.success ? (
                  <CheckCircle size={24} className="text-green-400 flex-shrink-0" />
                ) : (
                  <AlertCircle size={24} className="text-red-400 flex-shrink-0" />
                )}
                
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{result.file}</p>
                  {result.error && (
                    <p className="text-sm text-red-400">{result.error}</p>
                  )}
                </div>

                {result.success && (
                  <button
                    onClick={() => handleViewFile(result)}
                    className="px-4 py-2 bg-accent-indigo rounded-lg text-sm font-medium hover:bg-accent-indigo/80 transition-colors"
                  >
                    View File
                  </button>
                )}
              </motion.div>
            ))}
          </div>

          <div className="flex gap-3">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleReset}
              className="btn-secondary flex-1"
            >
              Upload More
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => navigate('/files')}
              className="btn-primary flex-1"
            >
              View All Files
            </motion.button>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default Upload;
