import React, { useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronDown, Folder } from 'lucide-react';
import FileListItem from './FileListItem';

/**
 * SubgroupItem - Nested subcategory accordion
 * 
 * Props:
 * - subgroup: { name, items: [] }
 * - isExpanded: boolean
 * - onToggle: callback
 * - onFileSelect: callback for file clicks
 * - searchTerm: for highlighting matches
 */

const SubgroupItem = React.memo(({ 
  subgroup, 
  isExpanded, 
  onToggle, 
  onFileSelect,
  searchTerm = ''
}) => {
  const { name, items = [] } = subgroup;
  const itemCount = items.length;

  const handleToggle = useCallback(() => {
    onToggle();
  }, [onToggle]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onToggle();
    }
  }, [onToggle]);

  // Filter items based on search
  const filteredItems = useMemo(() => {
    if (!searchTerm) return items;
    
    const term = searchTerm.toLowerCase();
    return items.filter(item => 
      item.filename?.toLowerCase().includes(term)
    );
  }, [items, searchTerm]);

  const displayCount = searchTerm ? filteredItems.length : itemCount;
  const hasMatchingItems = searchTerm ? filteredItems.length > 0 : true;

  // Don't render if no matches during search
  if (searchTerm && !hasMatchingItems) return null;

  return (
    <div className="ml-4 mb-2">
      {/* Subcategory Header */}
      <motion.div
        initial={false}
        whileHover={{ x: 2 }}
        className={`
          flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all
          ${isExpanded 
            ? 'bg-white/10 shadow-lg' 
            : 'bg-white/5 hover:bg-white/10'
          }
        `}
        role="button"
        tabIndex={0}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        aria-expanded={isExpanded}
        aria-label={`${name}, ${displayCount} items`}
      >
        {/* Expand Icon */}
        <motion.div
          animate={{ rotate: isExpanded ? 90 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronRight size={16} className="text-white/60" />
        </motion.div>

        {/* Folder Icon */}
        <div className="p-2 bg-accent-teal/20 rounded-lg">
          <Folder size={18} className="text-accent-teal" />
        </div>

        {/* Name & Count */}
        <div className="flex-1">
          <span className="text-sm font-medium text-white/90">
            {name}
          </span>
        </div>

        {/* Item Count Badge */}
        <div className="px-2 py-1 bg-white/10 rounded-lg">
          <span className="text-xs font-semibold text-white/70">
            {displayCount}
          </span>
        </div>
      </motion.div>

      {/* Expanded Content - File List */}
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="ml-6 mt-2 space-y-2">
              {filteredItems.length > 0 ? (
                filteredItems.map((file, index) => (
                  <FileListItem
                    key={file.id}
                    file={file}
                    onSelect={onFileSelect}
                    index={index}
                    compact={true}
                  />
                ))
              ) : (
                <div className="p-4 text-center text-white/40 text-sm">
                  No files in this subcategory
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

SubgroupItem.displayName = 'SubgroupItem';

export default SubgroupItem;
