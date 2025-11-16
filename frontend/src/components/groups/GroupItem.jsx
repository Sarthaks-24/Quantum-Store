import React, { useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, FolderOpen, Folder } from 'lucide-react';
import SubgroupItem from './SubgroupItem';
import { useAccordion } from '../../hooks/useAccordionState';

/**
 * GroupItem - Top-level category accordion
 * 
 * Props:
 * - group: { name, count, subgroups: [] }
 * - isExpanded: boolean
 * - onToggle: callback
 * - onFileSelect: callback for file clicks
 * - searchTerm: for filtering
 * - icon: Lucide icon component
 */

const GroupItem = React.memo(({ 
  group, 
  isExpanded, 
  onToggle, 
  onFileSelect,
  searchTerm = '',
  icon: IconComponent = FolderOpen
}) => {
  const { name, count, subgroups = [] } = group;

  // Nested accordion for subgroups
  const {
    isExpanded: isSubgroupExpanded,
    toggleItem: toggleSubgroup,
    expandItem: expandSubgroup
  } = useAccordion([], { multiExpand: true });

  const handleToggle = useCallback(() => {
    onToggle();
  }, [onToggle]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onToggle();
    }
  }, [onToggle]);

  // Filter subgroups based on search
  const filteredSubgroups = useMemo(() => {
    if (!searchTerm) return subgroups;
    
    const term = searchTerm.toLowerCase();
    return subgroups.filter(subgroup => {
      // Match subgroup name
      if (subgroup.name?.toLowerCase().includes(term)) return true;
      
      // Match any file in subgroup
      return subgroup.items?.some(item => 
        item.filename?.toLowerCase().includes(term)
      );
    }).map(subgroup => {
      // Auto-expand matching subgroups
      if (subgroup.items?.some(item => item.filename?.toLowerCase().includes(term))) {
        // Expand this subgroup
        setTimeout(() => expandSubgroup(subgroup.name), 0);
      }
      return subgroup;
    });
  }, [subgroups, searchTerm, expandSubgroup]);

  const hasMatchingSubgroups = searchTerm ? filteredSubgroups.length > 0 : true;

  // Don't render if no matches during search
  if (searchTerm && !hasMatchingSubgroups) return null;

  return (
    <div className="mb-4">
      {/* Category Header */}
      <motion.div
        initial={false}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        className={`
          glass-card-hover p-4 cursor-pointer transition-all
          ${isExpanded ? 'ring-2 ring-accent-indigo/50' : ''}
        `}
        role="button"
        tabIndex={0}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        aria-expanded={isExpanded}
        aria-label={`${name}, ${count} items`}
      >
        <div className="flex items-center gap-4">
          {/* Expand Arrow */}
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown size={20} className="text-white/60" />
          </motion.div>

          {/* Category Icon */}
          <div className="p-3 bg-accent-indigo/20 rounded-xl">
            <IconComponent size={24} className="text-accent-indigo" />
          </div>

          {/* Name & Count */}
          <div className="flex-1">
            <h3 className="text-lg font-bold text-white/90">
              {name}
            </h3>
            <p className="text-sm text-white/50 mt-0.5">
              {count} {count === 1 ? 'item' : 'items'}
            </p>
          </div>

          {/* Count Badge */}
          <div className="px-4 py-2 bg-gradient-to-r from-accent-indigo/20 to-accent-teal/20 rounded-xl">
            <span className="text-xl font-bold bg-gradient-to-r from-accent-indigo to-accent-teal bg-clip-text text-transparent">
              {count}
            </span>
          </div>
        </div>
      </motion.div>

      {/* Expanded Content - Subgroups */}
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="mt-3 space-y-2">
              {filteredSubgroups.length > 0 ? (
                filteredSubgroups.map((subgroup, index) => (
                  <SubgroupItem
                    key={`${subgroup.name}-${index}`}
                    subgroup={subgroup}
                    isExpanded={isSubgroupExpanded(subgroup.name)}
                    onToggle={() => toggleSubgroup(subgroup.name)}
                    onFileSelect={onFileSelect}
                    searchTerm={searchTerm}
                  />
                ))
              ) : (
                <div className="ml-4 p-4 text-center text-white/40">
                  No subcategories found
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

GroupItem.displayName = 'GroupItem';

export default GroupItem;
