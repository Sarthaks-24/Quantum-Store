import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';

/**
 * useAccordion - Shared accordion state management hook
 * 
 * Supports:
 * - Multiple items expanded at once (or single)
 * - Nested accordion state
 * - Smooth animations via state tracking
 */

export const useAccordion = (initialExpandedIds = [], { multiExpand = true } = {}) => {
  const [expandedIds, setExpandedIds] = useState(new Set(initialExpandedIds));

  const toggleItem = useCallback((id) => {
    setExpandedIds(prev => {
      const newSet = new Set(multiExpand ? prev : []);
      
      if (prev.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      
      return newSet;
    });
  }, [multiExpand]);

  const expandItem = useCallback((id) => {
    setExpandedIds(prev => {
      const newSet = new Set(multiExpand ? prev : []);
      newSet.add(id);
      return newSet;
    });
  }, [multiExpand]);

  const collapseItem = useCallback((id) => {
    setExpandedIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(id);
      return newSet;
    });
  }, []);

  const collapseAll = useCallback(() => {
    setExpandedIds(new Set());
  }, []);

  const expandAll = useCallback((ids) => {
    setExpandedIds(new Set(ids));
  }, []);

  const isExpanded = useCallback((id) => {
    return expandedIds.has(id);
  }, [expandedIds]);

  return {
    expandedIds: Array.from(expandedIds),
    toggleItem,
    expandItem,
    collapseItem,
    collapseAll,
    expandAll,
    isExpanded,
  };
};

/**
 * AccordionContext - For nested accordions
 */
const AccordionContext = createContext(null);

export const AccordionProvider = ({ children, value }) => (
  <AccordionContext.Provider value={value}>
    {children}
  </AccordionContext.Provider>
);

export const useAccordionContext = () => {
  const context = useContext(AccordionContext);
  if (!context) {
    throw new Error('useAccordionContext must be used within AccordionProvider');
  }
  return context;
};
