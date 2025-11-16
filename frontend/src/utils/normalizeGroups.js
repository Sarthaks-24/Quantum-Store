/**
 * Canonical client-side normalizer for /groups API response
 * 
 * Ensures consistent data structure regardless of backend variations.
 * Generates missing IDs, converts sizes, provides safe defaults.
 */

import { v4 as uuidv4 } from 'uuid';

/**
 * Convert bytes to human-readable format
 * @param {number} bytes - Size in bytes
 * @returns {string} Human-readable size (e.g., "1.5 MB")
 */
export function formatSize(bytes) {
  if (bytes === null || bytes === undefined || isNaN(bytes)) {
    return 'Unknown';
  }
  
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 B';
  
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const size = bytes / Math.pow(1024, i);
  
  return `${size.toFixed(i === 0 ? 0 : 1)} ${sizes[i]}`;
}

/**
 * Ensure item has required ID field
 * @param {Object} item - Item object
 * @param {string} fallbackPrefix - Prefix for generated ID
 * @returns {string} Valid ID
 */
function ensureId(item, fallbackPrefix = 'generated') {
  if (item.id) return item.id;
  if (item.file_id) return item.file_id;
  return `${fallbackPrefix}-${uuidv4()}`;
}

/**
 * Normalize a single file item
 * @param {Object} file - Raw file object
 * @returns {Object} Normalized file object
 */
function normalizeFileItem(file) {
  const id = ensureId(file, 'file');
  const sizeBytes = file.size_bytes || file.size || null;
  const sizeHuman = formatSize(sizeBytes);
  
  return {
    id,
    filename: file.filename || file.name || 'Unnamed File',
    size_bytes: sizeBytes,
    size_human: sizeHuman,
    type: file.type || file.file_type || file.mime_type || 'unknown',
    uploaded_at: file.uploaded_at || file.created_at || new Date().toISOString(),
    category: file.category || 'uncategorized',
    metadata: file.metadata || file,
    // Preserve original data for compatibility
    ...file
  };
}

/**
 * Normalize a subgroup
 * @param {Object} subgroup - Raw subgroup object
 * @param {string} parentId - Parent group ID
 * @returns {Object} Normalized subgroup
 */
function normalizeSubgroup(subgroup, parentId) {
  const id = ensureId(subgroup, `subgroup-${parentId}`);
  const items = Array.isArray(subgroup.items) 
    ? subgroup.items.map(normalizeFileItem)
    : [];
  
  const count = subgroup.count !== undefined && subgroup.count !== null 
    ? subgroup.count 
    : items.length;
  
  return {
    id,
    name: subgroup.name || 'Unnamed Subgroup',
    count,
    items,
    // Track if items have been loaded (for lazy loading)
    itemsLoaded: items.length > 0,
    parentId
  };
}

/**
 * Normalize a top-level group
 * @param {Object} group - Raw group object
 * @returns {Object} Normalized group
 */
function normalizeGroup(group) {
  const id = ensureId(group, 'group');
  const subgroups = Array.isArray(group.subgroups)
    ? group.subgroups.map(sg => normalizeSubgroup(sg, id))
    : [];
  
  // Calculate total count from subgroups if not provided
  const calculatedCount = subgroups.reduce((sum, sg) => sum + sg.count, 0);
  const count = group.count !== undefined && group.count !== null
    ? group.count
    : calculatedCount;
  
  return {
    id,
    name: group.name || 'Unnamed Group',
    count,
    subgroups
  };
}

/**
 * Main normalization function for /groups API response
 * 
 * @param {Object} raw - Raw API response
 * @returns {Array} Normalized groups array
 * 
 * Expected input formats:
 * 1. { groups: [...] }
 * 2. [...] (array directly)
 * 3. { data: { groups: [...] } }
 * 
 * Output format:
 * [
 *   {
 *     id: string,
 *     name: string,
 *     count: number,
 *     subgroups: [
 *       {
 *         id: string,
 *         name: string,
 *         count: number,
 *         items: [
 *           {
 *             id: string,
 *             filename: string,
 *             size_bytes: number|null,
 *             size_human: string,
 *             type: string,
 *             uploaded_at: string,
 *             category: string,
 *             metadata: object
 *           }
 *         ],
 *         itemsLoaded: boolean,
 *         parentId: string
 *       }
 *     ]
 *   }
 * ]
 */
export function normalizeGroups(raw) {
  // Handle null/undefined
  if (!raw) {
    console.warn('[normalizeGroups] Received null/undefined, returning empty array');
    return [];
  }
  
  let groups;
  
  // Extract groups array from various response formats
  if (Array.isArray(raw)) {
    groups = raw;
  } else if (raw.groups && Array.isArray(raw.groups)) {
    groups = raw.groups;
  } else if (raw.data && raw.data.groups && Array.isArray(raw.data.groups)) {
    groups = raw.data.groups;
  } else {
    console.warn('[normalizeGroups] Unexpected format, returning empty array:', raw);
    return [];
  }
  
  // Normalize each group
  return groups.map(normalizeGroup);
}

/**
 * Fallback: Fetch and normalize groups from /files endpoint
 * Use when /groups endpoint is unavailable
 * 
 * @param {Array} files - Array of files from /files endpoint
 * @returns {Array} Normalized groups built from files
 */
export function normalizeGroupsFromFiles(files) {
  if (!Array.isArray(files)) {
    console.warn('[normalizeGroupsFromFiles] Expected array, got:', typeof files);
    return [];
  }
  
  // Group files by category
  const categoryMap = new Map();
  
  files.forEach(file => {
    const category = file.category || 'uncategorized';
    if (!categoryMap.has(category)) {
      categoryMap.set(category, []);
    }
    categoryMap.get(category).push(normalizeFileItem(file));
  });
  
  // Convert to normalized groups structure
  const groups = [];
  categoryMap.forEach((items, category) => {
    // Extract main category and subcategory from category string
    // e.g., "images_screenshot" -> main: "images", sub: "screenshot"
    const parts = category.split('_');
    const mainCategory = parts[0] || 'other';
    const subCategory = parts.slice(1).join('_') || 'general';
    
    // Find or create main group
    let group = groups.find(g => g.id === mainCategory);
    if (!group) {
      group = {
        id: mainCategory,
        name: mainCategory.charAt(0).toUpperCase() + mainCategory.slice(1),
        count: 0,
        subgroups: []
      };
      groups.push(group);
    }
    
    // Add subgroup
    group.subgroups.push({
      id: `${mainCategory}-${subCategory}`,
      name: subCategory.charAt(0).toUpperCase() + subCategory.slice(1).replace(/_/g, ' '),
      count: items.length,
      items,
      itemsLoaded: true,
      parentId: mainCategory
    });
    
    // Update group count
    group.count += items.length;
  });
  
  return groups;
}

export default normalizeGroups;
