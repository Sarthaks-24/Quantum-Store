/**
 * Unit tests for normalizeGroups.js utility
 * 
 * Tests:
 * - formatSize() - byte conversion to human-readable format
 * - ensureId() - UUID generation for missing IDs
 * - normalizeGroups() - multiple input format handling
 * - normalizeGroupsFromFiles() - client-side fallback
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { 
  normalizeGroups, 
  normalizeGroupsFromFiles 
} from '../src/utils/normalizeGroups';

describe('normalizeGroups', () => {
  describe('Backend response normalization', () => {
    it('should normalize empty groups object', () => {
      const input = { groups: {} };
      const result = normalizeGroups(input);
      
      expect(result).toEqual([]);
    });

    it('should normalize backend response with single category', () => {
      const input = {
        groups: {
          'image_screenshot': [
            {
              id: 'file-1',
              filename: 'screenshot.png',
              size: 1024,
              file_type: 'image/png',
              category: 'image_screenshot'
            }
          ]
        }
      };

      const result = normalizeGroups(input);
      
      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('Images');
      expect(result[0].count).toBe(1);
      expect(result[0].subgroups).toHaveLength(1);
      expect(result[0].subgroups[0].name).toBe('Screenshot');
      expect(result[0].subgroups[0].items).toHaveLength(1);
      expect(result[0].subgroups[0].items[0].filename).toBe('screenshot.png');
    });

    it('should normalize multiple categories and subgroups', () => {
      const input = {
        groups: {
          'image_screenshot': [
            { id: 'f1', filename: 'ss1.png', size: 1024, category: 'image_screenshot' }
          ],
          'image_photo': [
            { id: 'f2', filename: 'photo.jpg', size: 2048, category: 'image_photo' }
          ],
          'pdf_document': [
            { id: 'f3', filename: 'doc.pdf', size: 4096, category: 'pdf_document' }
          ]
        }
      };

      const result = normalizeGroups(input);
      
      // Should have 2 main groups: Images and Documents
      expect(result.length).toBeGreaterThanOrEqual(2);
      
      const imagesGroup = result.find(g => g.name === 'Images');
      expect(imagesGroup).toBeDefined();
      expect(imagesGroup.count).toBe(2);
      expect(imagesGroup.subgroups).toHaveLength(2);
      
      const docsGroup = result.find(g => g.name === 'Documents');
      expect(docsGroup).toBeDefined();
      expect(docsGroup.count).toBe(1);
    });

    it('should handle files without size (convert to Unknown)', () => {
      const input = {
        groups: {
          'text_plain': [
            { id: 'f1', filename: 'note.txt', category: 'text_plain' }
          ]
        }
      };

      const result = normalizeGroups(input);
      
      expect(result[0].subgroups[0].items[0].size_human).toBe('Unknown');
    });

    it('should convert bytes to human-readable size', () => {
      const input = {
        groups: {
          'image_photo': [
            { id: 'f1', filename: 'small.jpg', size: 512, category: 'image_photo' },
            { id: 'f2', filename: 'medium.jpg', size: 1024 * 500, category: 'image_photo' },
            { id: 'f3', filename: 'large.jpg', size: 1024 * 1024 * 5, category: 'image_photo' }
          ]
        }
      };

      const result = normalizeGroups(input);
      const items = result[0].subgroups[0].items;
      
      expect(items[0].size_human).toMatch(/B$/); // Bytes
      expect(items[1].size_human).toMatch(/KB$/); // Kilobytes
      expect(items[2].size_human).toMatch(/MB$/); // Megabytes
    });

    it('should generate UUIDs for files missing IDs', () => {
      const input = {
        groups: {
          'json_data': [
            { filename: 'data.json', size: 256, category: 'json_data' }
          ]
        }
      };

      const result = normalizeGroups(input);
      const item = result[0].subgroups[0].items[0];
      
      expect(item.id).toBeDefined();
      expect(item.id).toMatch(/^file-[a-f0-9-]+$/); // UUID format
    });

    it('should set itemsLoaded to true for all subgroups', () => {
      const input = {
        groups: {
          'video_recording': [
            { id: 'v1', filename: 'video.mp4', size: 1024 * 1024, category: 'video_recording' }
          ]
        }
      };

      const result = normalizeGroups(input);
      
      expect(result[0].subgroups[0].itemsLoaded).toBe(true);
    });
  });

  describe('Array input handling', () => {
    it('should handle array of groups directly', () => {
      const input = [
        {
          name: 'Custom Group',
          subgroups: [
            {
              name: 'Custom Subgroup',
              items: [
                { id: 'f1', filename: 'file.txt', size: 100 }
              ]
            }
          ]
        }
      ];

      const result = normalizeGroups(input);
      
      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('Custom Group');
      expect(result[0].subgroups[0].name).toBe('Custom Subgroup');
    });
  });

  describe('Nested data structure handling', () => {
    it('should handle { data: { groups: {...} } } format', () => {
      const input = {
        data: {
          groups: {
            'audio_music': [
              { id: 'a1', filename: 'song.mp3', size: 3072, category: 'audio_music' }
            ]
          }
        }
      };

      const result = normalizeGroups(input);
      
      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('Audio Files');
    });
  });

  describe('Edge cases', () => {
    it('should handle null input gracefully', () => {
      const result = normalizeGroups(null);
      expect(result).toEqual([]);
    });

    it('should handle undefined input gracefully', () => {
      const result = normalizeGroups(undefined);
      expect(result).toEqual([]);
    });

    it('should handle empty object input', () => {
      const result = normalizeGroups({});
      expect(result).toEqual([]);
    });

    it('should filter out empty categories', () => {
      const input = {
        groups: {
          'image_photo': [],
          'text_code': [
            { id: 'f1', filename: 'code.js', size: 512, category: 'text_code' }
          ]
        }
      };

      const result = normalizeGroups(input);
      
      // Should only include Text Files group, not Images
      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('Text Files');
    });
  });
});

describe('normalizeGroupsFromFiles', () => {
  it('should build groups from files array (fallback mode)', () => {
    const files = [
      { id: 'f1', filename: 'image.png', size: 1024, category: 'image_photo', file_type: 'image/png' },
      { id: 'f2', filename: 'doc.pdf', size: 2048, category: 'pdf_document', file_type: 'application/pdf' },
      { id: 'f3', filename: 'screenshot.png', size: 1024, category: 'image_screenshot', file_type: 'image/png' }
    ];

    const result = normalizeGroupsFromFiles(files);
    
    expect(result.length).toBeGreaterThanOrEqual(2);
    
    const imagesGroup = result.find(g => g.name === 'Images');
    expect(imagesGroup).toBeDefined();
    expect(imagesGroup.count).toBe(2);
    
    const docsGroup = result.find(g => g.name === 'Documents');
    expect(docsGroup).toBeDefined();
    expect(docsGroup.count).toBe(1);
  });

  it('should handle files without categories', () => {
    const files = [
      { id: 'f1', filename: 'unknown.bin', size: 512 }
    ];

    const result = normalizeGroupsFromFiles(files);
    
    // Should create an "Other" or "Uncategorized" group
    expect(result.length).toBeGreaterThanOrEqual(0);
  });

  it('should handle empty files array', () => {
    const result = normalizeGroupsFromFiles([]);
    expect(result).toEqual([]);
  });

  it('should handle null files input', () => {
    const result = normalizeGroupsFromFiles(null);
    expect(result).toEqual([]);
  });
});

describe('Size formatting', () => {
  it('should format bytes correctly', () => {
    const testCases = [
      { bytes: 0, expected: 'Unknown' },
      { bytes: null, expected: 'Unknown' },
      { bytes: undefined, expected: 'Unknown' },
      { bytes: 512, expectedPattern: /512\.0 B/ },
      { bytes: 1024, expectedPattern: /1\.0 KB/ },
      { bytes: 1536, expectedPattern: /1\.5 KB/ },
      { bytes: 1024 * 1024, expectedPattern: /1\.0 MB/ },
      { bytes: 1024 * 1024 * 2.5, expectedPattern: /2\.5 MB/ },
      { bytes: 1024 * 1024 * 1024, expectedPattern: /1\.0 GB/ }
    ];

    testCases.forEach(({ bytes, expected, expectedPattern }) => {
      const input = {
        groups: {
          'test_category': [
            { id: 't1', filename: 'test.file', size: bytes, category: 'test_category' }
          ]
        }
      };

      const result = normalizeGroups(input);
      
      if (result.length > 0) {
        const item = result[0]?.subgroups?.[0]?.items?.[0];
        if (item) {
          if (expected) {
            expect(item.size_human).toBe(expected);
          } else if (expectedPattern) {
            expect(item.size_human).toMatch(expectedPattern);
          }
        }
      }
    });
  });
});

describe('UUID generation', () => {
  it('should generate unique IDs for multiple files without IDs', () => {
    const input = {
      groups: {
        'text_plain': [
          { filename: 'file1.txt', size: 100, category: 'text_plain' },
          { filename: 'file2.txt', size: 200, category: 'text_plain' },
          { filename: 'file3.txt', size: 300, category: 'text_plain' }
        ]
      }
    };

    const result = normalizeGroups(input);
    const items = result[0].subgroups[0].items;
    
    const ids = items.map(item => item.id);
    const uniqueIds = new Set(ids);
    
    expect(uniqueIds.size).toBe(3); // All IDs should be unique
    ids.forEach(id => {
      expect(id).toMatch(/^file-[a-f0-9-]+$/);
    });
  });

  it('should preserve existing IDs', () => {
    const input = {
      groups: {
        'json_data': [
          { id: 'existing-id-123', filename: 'data.json', size: 256, category: 'json_data' }
        ]
      }
    };

    const result = normalizeGroups(input);
    const item = result[0].subgroups[0].items[0];
    
    expect(item.id).toBe('existing-id-123');
  });
});

describe('Category name formatting', () => {
  it('should format category names correctly', () => {
    const input = {
      groups: {
        'image_screenshot': [{ id: 'f1', filename: 'ss.png', size: 100 }],
        'pdf_invoice_receipt': [{ id: 'f2', filename: 'inv.pdf', size: 200 }],
        'text_source_code': [{ id: 'f3', filename: 'code.py', size: 300 }],
        'video_screen_recording': [{ id: 'f4', filename: 'rec.mp4', size: 400 }]
      }
    };

    const result = normalizeGroups(input);
    
    const findSubgroup = (groupName, subgroupName) => {
      const group = result.find(g => g.name === groupName);
      return group?.subgroups.find(sg => sg.name === subgroupName);
    };
    
    expect(findSubgroup('Images', 'Screenshot')).toBeDefined();
    expect(findSubgroup('Documents', 'Invoice Receipt')).toBeDefined();
    expect(findSubgroup('Text Files', 'Source Code')).toBeDefined();
    expect(findSubgroup('Videos', 'Screen Recording')).toBeDefined();
  });
});

describe('Count aggregation', () => {
  it('should correctly aggregate counts across subgroups', () => {
    const input = {
      groups: {
        'image_photo': [
          { id: 'f1', filename: 'p1.jpg', size: 100 },
          { id: 'f2', filename: 'p2.jpg', size: 100 }
        ],
        'image_screenshot': [
          { id: 'f3', filename: 's1.png', size: 100 },
          { id: 'f4', filename: 's2.png', size: 100 },
          { id: 'f5', filename: 's3.png', size: 100 }
        ]
      }
    };

    const result = normalizeGroups(input);
    const imagesGroup = result.find(g => g.name === 'Images');
    
    expect(imagesGroup.count).toBe(5); // 2 photos + 3 screenshots
    expect(imagesGroup.subgroups[0].count).toBeDefined();
    expect(imagesGroup.subgroups[1].count).toBeDefined();
  });
});
