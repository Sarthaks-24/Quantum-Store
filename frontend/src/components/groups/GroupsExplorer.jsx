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
  File,
  Loader
} from 'lucide-react';
import { fetchGroups, fetchFiles, rebuildGroups } from '../../api';
import { normalizeGroups, normalizeGroupsFromFiles } from '../../utils/normalizeGroups';
import PreviewModal from '../ui/PreviewModal';

/**
 * GroupsExplorer - Deterministic multi-level accordion with lazy-loading
 * 
 * Features:
 * - Canonical data normalization via normalizeGroups
 * - Deterministic expand/collapse via expandedMap keyed by id
 * - Lazy-loading of subgroup items
 * - Search with auto-expand on match
 * - Full accessibility (aria-expanded, keyboard nav)
 * - Fallback to /files endpoint if /groups unavailable
 */

// Category icons mapping
const getCategoryIcon = (categoryId) => {
  const id = categoryId?.toLowerCase() || '';
  if (id.includes('image')) return ImageIcon;
  if (id.includes('pdf') || id.includes('document')) return FileText;
  if (id.includes('json')) return Database;
  if (id.includes('text') || id.includes('code')) return FileCode;
  if (id.includes('video')) return Video;
  if (id.includes('audio') || id.includes('music')) return Music;
  return FolderOpen;
};

// Helper for size formatting
const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return 'Unknown';
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`;
};

const GroupsExplorer = () => {
  // State management
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [rebuilding, setRebuilding] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState(null);
  
  // Deterministic expand state: Map<id, boolean>
  const [expandedMap, setExpandedMap] = useState(new Map());
  
  // Track which subgroups are loading items
  const [loadingItems, setLoadingItems] = useState(new Set());

  // Load groups data
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Try to fetch from /groups endpoint
      const groupsData = await fetchGroups();
      const normalized = normalizeGroups(groupsData);
      
      if (normalized.length === 0) {
        // Fallback: build from /files if groups are empty
        console.log('[GroupsExplorer] No groups found, falling back to /files');
        const filesData = await fetchFiles();
        const fallbackGroups = normalizeGroupsFromFiles(filesData);
        setGroups(fallbackGroups);
      } else {
        setGroups(normalized);
      }
    } catch (err) {
      console.error('[GroupsExplorer] Failed to load groups:', err);
      
      // Fallback: try to build from /files
      try {
        console.log('[GroupsExplorer] Attempting fallback to /files');
        const filesData = await fetchFiles();
        const fallbackGroups = normalizeGroupsFromFiles(filesData);
        setGroups(fallbackGroups);
      } catch (fallbackErr) {
        console.error('[GroupsExplorer] Fallback also failed:', fallbackErr);
        setError('Failed to load categories. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Rebuild groups from backend
  const handleRebuildGroups = useCallback(async () => {
    setRebuilding(true);
    try {
      await rebuildGroups();
      await loadData();
    } catch (err) {
      console.error('[GroupsExplorer] Failed to rebuild groups:', err);
      setError('Failed to rebuild categories. Please try again.');
    } finally {
      setRebuilding(false);
    }
  }, [loadData]);

  // Toggle expansion for a node (group or subgroup)
  const toggleExpanded = useCallback((id) => {
    setExpandedMap(prev => {
      const newMap = new Map(prev);
      newMap.set(id, !prev.get(id));
      return newMap;
    });
  }, []);

  // Lazy-load items for a subgroup
  const loadSubgroupItems = useCallback(async (groupId, subgroupId) => {
    // Check if already loaded or loading
    const subgroup = groups
      .find(g => g.id === groupId)
      ?.subgroups?.find(sg => sg.id === subgroupId);
    
    if (!subgroup || subgroup.itemsLoaded || loadingItems.has(subgroupId)) {
      return;
    }

    setLoadingItems(prev => new Set(prev).add(subgroupId));

    try {
      // NOTE: Backend doesn't currently expose /groups/{groupId}/subgroups/{subId}/items
      // Fallback: Filter files from /files endpoint by matching category
      console.log(`[GroupsExplorer] Lazy-loading items for subgroup ${subgroupId}`);
      
      const filesData = await fetchFiles();
      const matchingFiles = filesData.filter(file => {
        // Match by subgroup name or category
        const category = file.category || '';
        return category.toLowerCase().includes(subgroup.name.toLowerCase());
      });

      // Update groups state with loaded items
      setGroups(prev => prev.map(group => {
        if (group.id !== groupId) return group;
        
        return {
          ...group,
          subgroups: group.subgroups.map(sg => {
            if (sg.id !== subgroupId) return sg;
            
            return {
              ...sg,
              items: matchingFiles.map(file => ({
                id: file.id,
                filename: file.filename,
                size_bytes: file.size,
                size_human: file.size_human || formatSize(file.size),
                type: file.file_type || file.mime_type,
                uploaded_at: file.uploaded_at,
                category: file.category,
                metadata: file
              })),
              itemsLoaded: true,
              count: matchingFiles.length
            };
          })
        };
      }));
    } catch (err) {
      console.error(`[GroupsExplorer] Failed to load items for subgroup ${subgroupId}:`, err);
    } finally {
      setLoadingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(subgroupId);
        return newSet;
      });
    }
  }, [groups, loadingItems]);

  // Handle subgroup expansion with lazy loading
  const handleSubgroupToggle = useCallback((groupId, subgroupId) => {
    const isExpanding = !expandedMap.get(subgroupId);
    toggleExpanded(subgroupId);
    
    // If expanding and items not loaded, fetch them
    if (isExpanding) {
      loadSubgroupItems(groupId, subgroupId);
    }
  }, [expandedMap, toggleExpanded, loadSubgroupItems]);

  // Handle file selection
  const handleFileSelect = useCallback((file) => {
    setSelectedFile(file.metadata || file);
  }, []);

  // Search and auto-expand logic
  const filteredGroups = useMemo(() => {
    if (!searchTerm.trim()) return groups;

    const term = searchTerm.toLowerCase();
    const matchedGroups = [];
    const newExpandedMap = new Map(expandedMap);

    groups.forEach(group => {
      const groupMatches = group.name.toLowerCase().includes(term);
      const matchedSubgroups = [];

      group.subgroups.forEach(subgroup => {
        const subgroupMatches = subgroup.name.toLowerCase().includes(term);
        const matchedItems = subgroup.items?.filter(item =>
          item.filename?.toLowerCase().includes(term)
        ) || [];

        if (subgroupMatches || matchedItems.length > 0 || groupMatches) {
          // Auto-expand matched groups and subgroups
          if (groupMatches || subgroupMatches || matchedItems.length > 0) {
            newExpandedMap.set(group.id, true);
            if (matchedItems.length > 0) {
              newExpandedMap.set(subgroup.id, true);
            }
          }

          matchedSubgroups.push({
            ...subgroup,
            items: searchTerm.trim() ? matchedItems : subgroup.items
          });
        }
      });

      if (groupMatches || matchedSubgroups.length > 0) {
        matchedGroups.push({
          ...group,
          subgroups: matchedSubgroups
        });
      }
    });

    // Update expanded map if search changed results
    if (searchTerm.trim() && matchedGroups.length > 0) {
      setExpandedMap(newExpandedMap);
    }

    return matchedGroups;
  }, [groups, searchTerm, expandedMap]);

  // Expand all groups
  const handleExpandAll = useCallback(() => {
    const newMap = new Map();
    groups.forEach(group => {
      newMap.set(group.id, true);
      group.subgroups.forEach(subgroup => {
        newMap.set(subgroup.id, true);
      });
    });
    setExpandedMap(newMap);
  }, [groups]);

  // Collapse all groups
  const handleCollapseAll = useCallback(() => {
    setExpandedMap(new Map());
  }, []);

  // Loading state
  if (loading) {
    return (
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <div className="h-10 w-64 bg-surface rounded-lg animate-pulse mb-2" />
            <div className="h-6 w-96 bg-surface rounded-lg animate-pulse" />
          </div>
          
          <div className="space-y-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-white border border-border-color rounded-xl animate-pulse" />
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
          <div className="category-card p-8 text-center">
            <div className="text-red-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-text-primary mb-2">Failed to Load Categories</h3>
            <p className="text-text-secondary mb-6">{error}</p>
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
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold">File Categories</h1>
              <p className="text-text-secondary text-sm mt-1">
                Browse {groups.reduce((sum, g) => sum + g.count, 0)} files organized by type and category
              </p>
            </div>
            <button
              onClick={loadData}
              className="btn-secondary inline-flex items-center gap-2"
              disabled={loading || rebuilding}
            >
              <RefreshCw size={16} className={rebuilding ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" size={20} />
            <input
              type="text"
              placeholder="Search categories, subcategories, or files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-12 py-3 bg-surface border border-border-color rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition-colors"
                aria-label="Clear search"
              >
                ✕
              </button>
            )}
          </div>

          {/* Quick Actions */}
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleExpandAll}
              className="px-4 py-2 bg-card-bg border border-border-color hover:border-primary rounded-lg text-sm text-text-primary transition-all"
            >
              Expand All
            </button>
            <button
              onClick={handleCollapseAll}
              className="px-4 py-2 bg-card-bg border border-border-color hover:border-primary rounded-lg text-sm text-text-primary transition-all"
            >
              Collapse All
            </button>
          </div>
        </motion.div>

        {/* Groups List or Empty State */}
        {filteredGroups.length > 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="space-y-4"
          >
            {filteredGroups.map((group, index) => (
              <GroupItem
                key={group.id}
                group={group}
                isExpanded={expandedMap.get(group.id) || false}
                onToggle={() => toggleExpanded(group.id)}
                onSubgroupToggle={handleSubgroupToggle}
                onFileSelect={handleFileSelect}
                expandedMap={expandedMap}
                loadingItems={loadingItems}
                index={index}
              />
            ))}
          </motion.div>
        ) : (
          <div className="category-card p-12 text-center">
            <FolderOpen size={64} className="mx-auto text-text-muted mb-4" />
            <h3 className="text-xl font-bold text-text-primary mb-2">
              {searchTerm ? 'No Matches Found' : 'No Categories Yet'}
            </h3>
            <p className="text-text-secondary mb-6">
              {searchTerm 
                ? 'Try adjusting your search terms'
                : 'Categories are automatically created when files are analyzed. Click the button below to organize your files.'
              }
            </p>
            {!searchTerm && (
              <button
                onClick={handleRebuildGroups}
                disabled={rebuilding}
                className="btn-primary inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw size={16} className={rebuilding ? 'animate-spin' : ''} />
                {rebuilding ? 'Organizing Files...' : 'Organize Files into Categories'}
              </button>
            )}
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
    </main>
  );
};

/**
 * GroupItem - Top-level category accordion
 */
const GroupItem = ({ 
  group, 
  isExpanded, 
  onToggle, 
  onSubgroupToggle,
  onFileSelect,
  expandedMap,
  loadingItems,
  index 
}) => {
  const Icon = getCategoryIcon(group.id);
  
  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: index * 0.05 }}
      className="category-card"
    >
      {/* Group Header */}
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-surface/50 rounded-lg transition-colors"
        aria-expanded={isExpanded}
        aria-controls={`group-${group.id}-content`}
      >
        <div className="flex items-center gap-3">
          <motion.div
            animate={{ rotate: isExpanded ? 90 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronRight size={20} className="text-text-secondary" />
          </motion.div>
          <div className="w-10 h-10 rounded-lg bg-primary-light flex items-center justify-center">
            <Icon size={20} className="text-primary" />
          </div>
          <div className="text-left">
            <h3 className="font-semibold text-text-primary">{group.name}</h3>
            <p className="text-sm text-text-secondary">{group.subgroups.length} subcategories</p>
          </div>
        </div>
        <div className="px-3 py-1 rounded-full bg-primary-light text-sm font-medium text-primary">
          {group.count}
        </div>
      </button>

      {/* Subgroups */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            id={`group-${group.id}-content`}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-border-color"
          >
            <div className="p-2">
              {group.subgroups.map((subgroup) => (
                <SubgroupItem
                  key={subgroup.id}
                  subgroup={subgroup}
                  groupId={group.id}
                  isExpanded={expandedMap.get(subgroup.id) || false}
                  onToggle={() => onSubgroupToggle(group.id, subgroup.id)}
                  onFileSelect={onFileSelect}
                  isLoading={loadingItems.has(subgroup.id)}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

/**
 * SubgroupItem - Nested subcategory accordion with lazy-loaded items
 */
const SubgroupItem = ({ 
  subgroup, 
  groupId,
  isExpanded, 
  onToggle, 
  onFileSelect,
  isLoading 
}) => {
  return (
    <div className="mb-2 last:mb-0">
      {/* Subgroup Header */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-surface/50 rounded-lg transition-colors"
        aria-expanded={isExpanded}
        aria-controls={`subgroup-${subgroup.id}-content`}
      >
        <div className="flex items-center gap-3">
          <motion.div
            animate={{ rotate: isExpanded ? 90 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronRight size={16} className="text-text-muted" />
          </motion.div>
          <File size={16} className="text-text-muted" />
          <span className="text-sm font-medium text-text-primary">{subgroup.name}</span>
        </div>
        <div className="flex items-center gap-2">
          {isLoading && <Loader size={14} className="animate-spin text-text-muted" />}
          <span className="text-xs px-2 py-0.5 rounded-full bg-primary-light text-primary">
            {subgroup.count}
          </span>
        </div>
      </button>

      {/* File Items */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            id={`subgroup-${subgroup.id}-content`}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="ml-8 mt-2"
          >
            {isLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-16 bg-surface rounded-lg animate-pulse" />
                ))}
              </div>
            ) : subgroup.items && subgroup.items.length > 0 ? (
              <div className="space-y-1">
                {subgroup.items.map((file, idx) => (
                  <FileItem
                    key={file.id}
                    file={file}
                    onSelect={onFileSelect}
                    index={idx}
                  />
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-secondary py-4 pl-4">No files in this subcategory</p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

/**
 * FileItem - Individual file row with metadata
 */
const FileItem = ({ file, onSelect, index }) => {
  return (
    <motion.button
      initial={{ x: -10, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ delay: index * 0.03 }}
      onClick={() => onSelect(file)}
      className="w-full px-4 py-3 flex items-center gap-3 hover:bg-surface/50 rounded-lg transition-all group text-left border-l-2 border-transparent hover:border-primary"
    >
      <File size={16} className="text-text-muted group-hover:text-primary transition-colors flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary truncate">
          {file.filename}
        </p>
        <p className="text-xs text-text-secondary mt-0.5">
          {file.size_human} • {file.type || 'Unknown type'}
        </p>
      </div>
    </motion.button>
  );
};

export default GroupsExplorer;

