import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  FolderOpen,
  Image as ImageIcon,
  FileText,
  Database,
  FileCode,
  Video,
  Music,
  RefreshCw,
  ChevronRight,
  Home
} from 'lucide-react';
import { fetchGroups, rebuildGroups } from '../../api';
import GroupItem from './GroupItem';
import PreviewModal from '../ui/PreviewModal';
import { useAccordion } from '../../hooks/useAccordionState';

/**
 * GroupsExplorer - File categorization browser
 * 
 * Features:
 * - Hierarchical category → subcategory → files view
 * - Search across all levels
 * - Breadcrumb navigation
 * - Inline preview
 * - Smooth animations
 * - Auto-expand on search
 */

// Category icons mapping
const getCategoryIcon = (categoryId) => {
  switch (categoryId) {
    case 'images': return ImageIcon;
    case 'pdfs': return FileText;
    case 'json': return Database;
    case 'text': return FileCode;
    case 'videos': return Video;
    case 'audio': return Music;
    default: return FolderOpen;
  }
};

const GroupsExplorer = () => {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [rebuilding, setRebuilding] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [breadcrumbs, setBreadcrumbs] = useState([]);
  const [error, setError] = useState(null);

  // Accordion state for categories
  const {
    isExpanded,
    toggleItem,
    expandAll,
    collapseAll,
    expandItem
  } = useAccordion([], { multiExpand: true });

  // Load groups
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch groups structure (backend returns full file objects already)
      const groupsData = await fetchGroups();
      setGroups(groupsData.groups || []);
    } catch (err) {
      console.error('Failed to load groups:', err);
      setError('Failed to load categories. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Rebuild groups from metadata
  const handleRebuildGroups = useCallback(async () => {
    setRebuilding(true);
    try {
      await rebuildGroups();
      // Reload data after rebuild
      await loadData();
    } catch (err) {
      console.error('Failed to rebuild groups:', err);
      setError('Failed to rebuild categories. Please try again.');
    } finally {
      setRebuilding(false);
    }
  }, [loadData]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Groups are already populated with file objects from backend
  const populatedGroups = useMemo(() => {
    return groups;
  }, [groups]);

  // Filter and auto-expand on search
  useEffect(() => {
    if (searchTerm) {
      // Auto-expand categories that have matches
      const matchingCategories = populatedGroups
        .filter(group => {
          // Check if category name matches
          if (group.name.toLowerCase().includes(searchTerm.toLowerCase())) return true;
          
          // Check if any subgroup or file matches
          return group.subgroups.some(subgroup => {
            if (subgroup.name.toLowerCase().includes(searchTerm.toLowerCase())) return true;
            return subgroup.items.some(file => 
              file.filename?.toLowerCase().includes(searchTerm.toLowerCase())
            );
          });
        })
        .map(group => group.id);
      
      matchingCategories.forEach(id => expandItem(id));
    }
  }, [searchTerm, populatedGroups, expandItem]);

  // Handle file selection
  const handleFileSelect = useCallback((file) => {
    setSelectedFile(file);
    setBreadcrumbs([
      { label: 'Groups', path: '/groups' },
      { label: file.classification?.category || 'Unknown', path: null },
      { label: file.filename, path: null }
    ]);
  }, []);

  // Handle file navigation in preview modal
  const handleNavigate = useCallback((direction) => {
    if (!selectedFile) return;
    
    // Get all files in current view
    const allVisibleFiles = populatedGroups.flatMap(group => 
      group.subgroups.flatMap(subgroup => subgroup.items)
    );
    
    const currentIndex = allVisibleFiles.findIndex(f => f.id === selectedFile.id);
    if (currentIndex === -1) return;
    
    const newIndex = direction === 'next' 
      ? (currentIndex + 1) % allVisibleFiles.length
      : (currentIndex - 1 + allVisibleFiles.length) % allVisibleFiles.length;
    
    setSelectedFile(allVisibleFiles[newIndex]);
  }, [selectedFile, populatedGroups]);

  // Shimmer loader
  if (loading) {
    return (
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <div className="h-10 w-64 bg-white/10 rounded-xl animate-pulse mb-2" />
            <div className="h-6 w-96 bg-white/5 rounded-lg animate-pulse" />
          </div>
          
          <div className="space-y-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-white/5 rounded-2xl animate-pulse" />
            ))}
          </div>
        </div>
      </main>
    );
  }

  // Error state
  if (error) {
    return (
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card p-8 text-center">
            <div className="text-red-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-white/90 mb-2">Failed to Load Categories</h3>
            <p className="text-white/60 mb-6">{error}</p>
            <button
              onClick={loadData}
              className="btn-primary inline-flex items-center gap-2"
            >
              <RefreshCw size={16} />
              Retry
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 p-8 overflow-y-auto">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-accent-indigo to-accent-teal bg-clip-text text-transparent">
                File Categories
              </h1>
              <p className="text-white/60 mt-2">
                Browse {populatedGroups.reduce((sum, g) => sum + g.count, 0)} files organized by type and category
              </p>
            </div>

            {/* Refresh Button */}
            <button
              onClick={loadData}
              className="btn-secondary flex items-center gap-2"
              disabled={loading}
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>

          {/* Breadcrumbs */}
          <AnimatePresence>
            {breadcrumbs.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="flex items-center gap-2 text-sm text-white/60 mb-4"
              >
                <Home size={14} />
                {breadcrumbs.map((crumb, index) => (
                  <React.Fragment key={index}>
                    <ChevronRight size={14} />
                    <span className={index === breadcrumbs.length - 1 ? 'text-white/90 font-medium' : ''}>
                      {crumb.label}
                    </span>
                  </React.Fragment>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" size={20} />
            <input
              type="text"
              placeholder="Search categories, subcategories, or files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-2xl text-white/90 placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-accent-indigo/50 focus:border-accent-indigo/50 transition-all"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70 transition-colors"
              >
                ✕
              </button>
            )}
          </div>

          {/* Quick Actions */}
          <div className="flex gap-2 mt-4">
            <button
              onClick={() => expandAll(populatedGroups.map(g => g.id))}
              className="px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-white/70 transition-colors"
            >
              Expand All
            </button>
            <button
              onClick={collapseAll}
              className="px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-white/70 transition-colors"
            >
              Collapse All
            </button>
          </div>
        </motion.div>

        {/* Groups List */}
        {populatedGroups.length > 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="space-y-4"
          >
            {populatedGroups.map((group, index) => (
              <GroupItem
                key={group.id}
                group={group}
                isExpanded={isExpanded(group.id)}
                onToggle={() => toggleItem(group.id)}
                onFileSelect={handleFileSelect}
                searchTerm={searchTerm}
                icon={getCategoryIcon(group.id)}
              />
            ))}
          </motion.div>
        ) : (
          <div className="glass-card p-12 text-center">
            <FolderOpen size={64} className="mx-auto text-white/20 mb-4" />
            <h3 className="text-xl font-bold text-white/60 mb-2">
              No Categories Yet
            </h3>
            <p className="text-white/40 mb-6">
              Categories are automatically created when files are analyzed.
              Click the button below to organize your files.
            </p>
            <button
              onClick={handleRebuildGroups}
              disabled={rebuilding}
              className="btn-primary inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw size={16} className={rebuilding ? 'animate-spin' : ''} />
              {rebuilding ? 'Organizing Files...' : 'Organize Files into Categories'}
            </button>
          </div>
        )}

        {/* Preview Modal */}
        {selectedFile && (
          <PreviewModal
            file={selectedFile}
            files={populatedGroups.flatMap(g => g.subgroups.flatMap(sg => sg.items))}
            onClose={() => {
              setSelectedFile(null);
              setBreadcrumbs([]);
            }}
            onNavigate={handleNavigate}
          />
        )}
      </div>
    </main>
  );
};

export default GroupsExplorer;
