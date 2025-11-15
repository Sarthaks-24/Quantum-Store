// File Preview Modal
async function openFilePreview(fileId) {
    try {
        // Show loading state
        showPreviewModal();
        setPreviewLoading(true);
        
        // Fetch preview data
        const previewData = await api.getFilePreview(fileId);
        
        // Populate modal with data
        displayPreviewContent(previewData);
        setPreviewLoading(false);
        
    } catch (error) {
        console.error('Error loading file preview:', error);
        setPreviewError(error.message);
    }
}

function showPreviewModal() {
    const modal = document.getElementById('previewModal');
    if (!modal) {
        createPreviewModal();
    }
    document.getElementById('previewModal').style.display = 'flex';
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

function closePreviewModal() {
    document.getElementById('previewModal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

function createPreviewModal() {
    const modalHTML = `
        <div id="previewModal" class="preview-modal" style="display: none;">
            <div class="preview-modal-overlay" onclick="closePreviewModal()"></div>
            <div class="preview-modal-content">
                <div class="preview-modal-header">
                    <h2 id="previewTitle">File Preview</h2>
                    <button class="preview-close-btn" onclick="closePreviewModal()">&times;</button>
                </div>
                <div class="preview-modal-body" id="previewBody">
                    <div class="preview-loading">Loading...</div>
                </div>
                <div class="preview-modal-footer">
                    <button class="btn" id="downloadBtn" onclick="downloadPreviewFile()">
                        📥 Download File
                    </button>
                    <button class="btn btn-secondary" onclick="closePreviewModal()">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function setPreviewLoading(isLoading) {
    const body = document.getElementById('previewBody');
    if (isLoading) {
        body.innerHTML = '<div class="preview-loading">Loading preview...</div>';
    }
}

function setPreviewError(message) {
    const body = document.getElementById('previewBody');
    body.innerHTML = `
        <div class="preview-error">
            <p>❌ Error loading preview</p>
            <p style="color: #888; font-size: 0.9em;">${message}</p>
        </div>
    `;
}

let currentFileId = null;

function displayPreviewContent(data) {
    currentFileId = data.file_id;
    
    const metadata = data.metadata;
    const analysis = data.analysis;
    const preview = data.preview;
    
    // Update title
    document.getElementById('previewTitle').textContent = metadata.filename || 'File Preview';
    
    // Build preview HTML
    let html = '';
    
    // Preview section
    html += '<div class="preview-section">';
    html += '<h3>Preview</h3>';
    html += '<div class="preview-content-area">';
    
    if (preview.type === 'image' && preview.content) {
        html += `<img src="data:image/png;base64,${preview.content}" alt="Preview" class="preview-image">`;
    } else if (preview.type === 'text' && preview.content) {
        html += `<pre class="preview-text">${escapeHtml(preview.content)}</pre>`;
    } else if (preview.type === 'json' && preview.content) {
        html += `<pre class="preview-json">${escapeHtml(preview.content)}</pre>`;
    } else if (preview.type === 'video') {
        html += `
            <div class="preview-placeholder">
                <p>🎥 Video File</p>
                <p style="color: #888; font-size: 0.9em;">Preview not available. Click download to view.</p>
            </div>
        `;
    } else if (preview.type === 'audio') {
        html += `
            <div class="preview-placeholder">
                <p>🎵 Audio File</p>
                <p style="color: #888; font-size: 0.9em;">Preview not available. Click download to listen.</p>
            </div>
        `;
    } else {
        html += `
            <div class="preview-placeholder">
                <p>📄 ${metadata.file_type || 'Unknown'} File</p>
                <p style="color: #888; font-size: 0.9em;">No preview available</p>
            </div>
        `;
    }
    
    html += '</div></div>';
    
    // Metadata section
    html += '<div class="preview-section">';
    html += '<h3>File Information</h3>';
    html += '<table class="preview-metadata-table">';
    
    html += `<tr><td><strong>Filename:</strong></td><td>${metadata.filename}</td></tr>`;
    html += `<tr><td><strong>Type:</strong></td><td>${metadata.file_type || 'Unknown'}</td></tr>`;
    html += `<tr><td><strong>Size:</strong></td><td>${formatBytes(metadata.size)}</td></tr>`;
    html += `<tr><td><strong>Uploaded:</strong></td><td>${new Date(metadata.uploaded_at).toLocaleString()}</td></tr>`;
    
    if (metadata.folder_id) {
        html += `<tr><td><strong>Folder ID:</strong></td><td>${metadata.folder_id}</td></tr>`;
    }
    
    if (metadata.schema_id) {
        html += `<tr><td><strong>Schema ID:</strong></td><td>${metadata.schema_id}</td></tr>`;
    }
    
    html += '</table>';
    html += '</div>';
    
    // Analysis section (if available)
    if (analysis && Object.keys(analysis).length > 0) {
        html += '<div class="preview-section">';
        html += '<h3>Analysis Results</h3>';
        html += '<div class="preview-analysis">';
        
        if (metadata.file_type === 'json' && analysis.record_count) {
            html += `<p><strong>Records:</strong> ${analysis.record_count}</p>`;
            if (analysis.schema) {
                html += `<p><strong>Fields:</strong> ${Object.keys(analysis.schema).length}</p>`;
            }
        } else if (metadata.file_type === 'text' && analysis.word_count) {
            html += `<p><strong>Words:</strong> ${analysis.word_count}</p>`;
            html += `<p><strong>Characters:</strong> ${analysis.char_count}</p>`;
        } else if (metadata.file_type === 'image') {
            if (analysis.dimensions) {
                html += `<p><strong>Dimensions:</strong> ${analysis.dimensions.width} × ${analysis.dimensions.height}</p>`;
            }
            if (analysis.format) {
                html += `<p><strong>Format:</strong> ${analysis.format}</p>`;
            }
        }
        
        html += '</div>';
        html += '</div>';
    }
    
    document.getElementById('previewBody').innerHTML = html;
}

function downloadPreviewFile() {
    if (currentFileId) {
        const downloadUrl = api.getFileDownloadUrl(currentFileId);
        window.open(downloadUrl, '_blank');
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modal = document.getElementById('previewModal');
        if (modal && modal.style.display === 'flex') {
            closePreviewModal();
        }
    }
});
