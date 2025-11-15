// API Configuration and Helper Functions
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_TIMEOUT = 10000; // 10 seconds

/**
 * Fetch wrapper with timeout and error handling
 */
async function fetchWithTimeout(url, options = {}, timeout = API_TIMEOUT) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

/**
 * Fetch dashboard summary metrics
 * Falls back to mock data if API fails
 */
export async function fetchSummary() {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/files`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Compute summary from files
    const totalFiles = data.files?.length || 0;
    const totalSize = data.files?.reduce((sum, f) => sum + (f.size || 0), 0) || 0;
    
    // Count by type
    const byType = {};
    data.files?.forEach(file => {
      const type = file.classification?.type || 'unknown';
      byType[type] = (byType[type] || 0) + 1;
    });
    
    return {
      totalFiles,
      totalSize,
      totalImages: byType.image || 0,
      totalPDFs: byType.pdf || 0,
      totalJSON: byType.json || 0,
      totalVideos: byType.video || 0,
      totalAudio: byType.audio || 0,
      byType,
    };
  } catch (error) {
    console.warn('API fetchSummary failed, using fallback:', error.message);
    
    // Fallback to mock data
    return {
      totalFiles: 0,
      totalSize: 0,
      totalImages: 0,
      totalPDFs: 0,
      totalJSON: 0,
      totalVideos: 0,
      totalAudio: 0,
      byType: {},
    };
  }
}

/**
 * Fetch recent files
 * @param {number} limit - Number of files to fetch
 */
export async function fetchRecentFiles(limit = 6) {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/files?limit=${limit}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.files || [];
  } catch (error) {
    console.warn('API fetchRecentFiles failed, using fallback:', error.message);
    
    // Try to load mock data
    try {
      const mockResponse = await fetch('/src/mocks/dashboard.json');
      const mockData = await mockResponse.json();
      return mockData.recentFiles?.slice(0, limit) || [];
    } catch {
      return [];
    }
  }
}

/**
 * Fetch file preview data
 * @param {string} fileId - File ID
 */
export async function fetchFilePreview(fileId) {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/file/${fileId}/preview`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.warn('API fetchFilePreview failed:', error.message);
    
    return {
      error: 'Preview unavailable',
      message: error.message,
    };
  }
}

/**
 * Download file
 * @param {string} fileId - File ID
 * @param {string} filename - Original filename
 */
export async function downloadFile(fileId, filename) {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/file/${fileId}/download`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // Create blob and download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'download';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    return { success: true };
  } catch (error) {
    console.error('Download failed:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Start analysis for a file
 * @param {string} fileId - File ID
 * @param {string} fileType - Type of file (json, pdf, image, etc.)
 */
export async function startAnalysis(fileId, fileType) {
  try {
    const endpoint = `${API_BASE_URL}/analyze/${fileType}`;
    const response = await fetchWithTimeout(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ file_id: fileId }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Analysis failed:', error.message);
    return { error: error.message };
  }
}

/**
 * Upload file
 * @param {File} file - File object
 */
export async function uploadFile(file) {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/upload`,
      {
        method: 'POST',
        body: formData,
      },
      30000 // 30 second timeout for uploads
    );
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Upload failed:', error.message);
    throw error;
  }
}

/**
 * Get all files with optional filters
 */
export async function fetchFiles(filters = {}) {
  try {
    const params = new URLSearchParams(filters);
    const response = await fetchWithTimeout(`${API_BASE_URL}/files?${params}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.files || [];
  } catch (error) {
    console.warn('API fetchFiles failed:', error.message);
    return [];
  }
}

/**
 * Compute weekly activity from files
 * Returns array of {name: 'Mon', uploads: N} for last 7 days
 */
export function computeWeeklyActivity(files) {
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const today = new Date();
  const weekData = [];
  
  // Initialize last 7 days
  for (let i = 6; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(today.getDate() - i);
    weekData.push({
      name: days[date.getDay()],
      uploads: 0,
      date: date.toISOString().split('T')[0]
    });
  }
  
  // Count uploads per day
  files.forEach(file => {
    const uploadDate = file.uploaded_at || file.created_at;
    if (uploadDate) {
      const fileDate = new Date(uploadDate).toISOString().split('T')[0];
      const dayData = weekData.find(d => d.date === fileDate);
      if (dayData) {
        dayData.uploads++;
      }
    }
  });
  
  return weekData;
}

/**
 * Normalize weekly activity data for charts
 * Ensures consistent data shape regardless of source
 */
export function normalizeWeeklyActivity(data) {
  if (!data || !Array.isArray(data)) {
    return [];
  }
  
  return data.map(item => ({
    name: item.name || item.day || 'Unknown',
    uploads: parseInt(item.uploads || item.count || item.value || 0, 10)
  }));
}

/**
 * Fetch file analytics from backend
 * @param {string} fileId - File ID
 * @param {string} fileType - File type (json, pdf, image, video, text)
 */
export async function fetchFileAnalytics(fileId, fileType) {
  if (!fileType) {
    return { error: 'File type required for analytics' };
  }
  
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/analyze/${fileType}?file_id=${fileId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ file_id: fileId }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Analytics fetch failed:', error.message);
    return { error: error.message };
  }
}

/**
 * Upload multiple files
 * @param {File[]} files - Array of File objects
 * @param {Function} onProgress - Progress callback (fileIndex, progress)
 */
export async function uploadFiles(files, onProgress) {
  const results = [];
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    
    try {
      if (onProgress) onProgress(i, 0);
      
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetchWithTimeout(
        `${API_BASE_URL}/upload`,
        {
          method: 'POST',
          body: formData,
        },
        60000 // 60 second timeout for large files
      );
      
      if (onProgress) onProgress(i, 100);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      results.push({ success: true, file: file.name, data: result });
    } catch (error) {
      console.error(`Upload failed for ${file.name}:`, error.message);
      results.push({ success: false, file: file.name, error: error.message });
    }
  }
  
  return results;
}

/**
 * Fetch weekly metrics from backend
 */
export async function fetchWeeklyMetrics() {
  try {
    const files = await fetchFiles();
    return computeWeeklyActivity(files);
  } catch (error) {
    console.warn('Weekly metrics fetch failed:', error.message);
    return [];
  }
}

export default {
  fetchSummary,
  fetchRecentFiles,
  fetchFilePreview,
  downloadFile,
  startAnalysis,
  uploadFile,
  fetchFiles,
  computeWeeklyActivity,
  normalizeWeeklyActivity,
  fetchFileAnalytics,
  uploadFiles,
  fetchWeeklyMetrics,
};
