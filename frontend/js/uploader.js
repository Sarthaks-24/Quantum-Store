const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const folderInput = document.getElementById('folderInput');

dropZone.addEventListener('click', () => {
    fileInput.click();
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', async (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    
    const files = Array.from(e.dataTransfer.files);
    await handleFiles(files);
});

fileInput.addEventListener('change', async (e) => {
    const files = Array.from(e.target.files);
    await handleFiles(files);
});

folderInput.addEventListener('change', async (e) => {
    const files = Array.from(e.target.files);
    await handleFolderUpload(files);
});

async function handleFiles(files) {
    addLog('System', `Processing ${files.length} file(s)...`);
    
    for (const file of files) {
        try {
            addLog('Upload', `Uploading ${file.name}...`);
            
            const uploadResult = await api.uploadFile(file);
            const fileId = uploadResult.file_id;
            const fileType = uploadResult.file_type;
            
            addLog('Success', `Uploaded ${file.name} (ID: ${fileId})`);
            
            addLog('Analysis', `Starting ${fileType} analysis for ${file.name}...`);
            
            let analysis;
            if (fileType === 'json') {
                analysis = await api.analyzeJSON(fileId);
                displayJSONAnalysis(file.name, analysis);
            } else if (fileType === 'text') {
                analysis = await api.analyzeText(fileId);
                displayTextAnalysis(file.name, analysis);
            } else if (fileType === 'image') {
                analysis = await api.analyzeImage(fileId);
                displayImageAnalysis(file.name, analysis);
            }
            
            if (analysis && analysis.reasoning_log) {
                analysis.reasoning_log.forEach(log => {
                    addLog('Reasoning', log.replace(/^\[.*?\]\s*/, ''));
                });
            }
            
            addLog('Complete', `Analysis complete for ${file.name}`);
            
        } catch (error) {
            addLog('Error', `Failed to process ${file.name}: ${error.message}`);
            console.error(error);
        }
    }
    
    await loadFiles();
}

async function handleFolderUpload(files) {
    addLog('System', `Processing folder with ${files.length} file(s)...`);
    
    try {
        addLog('Upload', `Uploading ${files.length} files from folder...`);
        
        const result = await api.uploadFolder(files);
        
        addLog('Success', `Uploaded ${result.successful} file(s) successfully`);
        
        if (result.failed > 0) {
            addLog('Warning', `Failed to upload ${result.failed} file(s)`);
        }
        
        // Display summary
        const successfulFiles = result.results.filter(r => !r.error);
        const analyzedFiles = successfulFiles.filter(r => r.analyzed);
        
        addLog('Summary', `Total: ${result.total_files} | Successful: ${result.successful} | Failed: ${result.failed}`);
        addLog('Summary', `Auto-analyzed: ${analyzedFiles.length} file(s)`);
        
        // Display detailed results
        result.results.forEach((fileResult, index) => {
            if (fileResult.error) {
                addLog('Error', `${fileResult.filename}: ${fileResult.error}`);
            } else {
                const status = fileResult.analyzed ? '✓ Analyzed' : '○ Uploaded';
                addLog('File', `${status} - ${fileResult.filename} (${fileResult.file_type}, ${(fileResult.size / 1024).toFixed(2)} KB)`);
            }
        });
        
        // Display folder summary card
        displayFolderSummary(result);
        
        addLog('Complete', `Folder upload complete!`);
        
    } catch (error) {
        addLog('Error', `Failed to upload folder: ${error.message}`);
        console.error(error);
    }
    
    await loadFiles();
}

function displayFolderSummary(result) {
    const filesList = document.getElementById('filesList');
    
    const summaryCard = document.createElement('div');
    summaryCard.className = 'file-item';
    summaryCard.style.background = 'linear-gradient(135deg, #667eea22 0%, #764ba222 100%)';
    summaryCard.style.borderLeft = '4px solid #764ba2';
    
    const typeBreakdown = {};
    result.results.forEach(r => {
        if (!r.error) {
            typeBreakdown[r.file_type] = (typeBreakdown[r.file_type] || 0) + 1;
        }
    });
    
    const typesList = Object.entries(typeBreakdown)
        .map(([type, count]) => `${type}: ${count}`)
        .join(' | ');
    
    summaryCard.innerHTML = `
        <div class="file-info">
            <div class="file-name">📂 Folder Upload Summary (ID: ${result.folder_id.substring(0, 8)}...)</div>
            <div class="file-meta">
                Total Files: ${result.total_files} | 
                Successful: ${result.successful} | 
                Failed: ${result.failed} | 
                Types: ${typesList}
            </div>
        </div>
    `;
    
    filesList.insertBefore(summaryCard, filesList.firstChild);
}

function addLog(type, message) {
    const logContainer = document.getElementById('reasoningLog');
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.innerHTML = `
        <span class="log-timestamp">[${timestamp}]</span>
        <span><strong>${type}:</strong> ${message}</span>
    `;
    
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

async function loadFiles() {
    try {
        addLog('System', 'Loading all files...');
        
        const result = await api.getAllFiles();
        const filesList = document.getElementById('filesList');
        
        if (result.files.length === 0) {
            filesList.innerHTML = '<p style="color: #888; text-align: center;">No files uploaded yet</p>';
            return;
        }
        
        filesList.innerHTML = '';
        
        result.files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const sizeKB = (file.size / 1024).toFixed(2);
            
            fileItem.innerHTML = `
                <div class="file-info">
                    <div class="file-name">📄 ${file.filename}</div>
                    <div class="file-meta">
                        Type: ${file.file_type} | Size: ${sizeKB} KB | 
                        Uploaded: ${new Date(file.uploaded_at).toLocaleString()}
                    </div>
                </div>
                <div class="file-actions">
                    <button class="btn" onclick="viewFile('${file.id}')">View Details</button>
                </div>
            `;
            
            filesList.appendChild(fileItem);
        });
        
        addLog('Success', `Loaded ${result.files.length} file(s)`);
        
    } catch (error) {
        addLog('Error', `Failed to load files: ${error.message}`);
        console.error(error);
    }
}

async function viewFile(fileId) {
    try {
        addLog('System', `Viewing file ${fileId}...`);
        
        const result = await api.getFile(fileId);
        
        if (result.analysis) {
            if (result.analysis.json) {
                displayJSONAnalysis(result.metadata.filename, result.analysis.json);
            } else if (result.analysis.text) {
                displayTextAnalysis(result.metadata.filename, result.analysis.text);
            } else if (result.analysis.image) {
                displayImageAnalysis(result.metadata.filename, result.analysis.image);
            }
        }
        
        document.getElementById('analysisCard').style.display = 'block';
        document.getElementById('analysisCard').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        addLog('Error', `Failed to view file: ${error.message}`);
        console.error(error);
    }
}

async function autoGroup() {
    try {
        addLog('System', 'Running auto-grouping algorithm...');
        
        const result = await api.autoGroup();
        
        if (result.reasoning) {
            result.reasoning.forEach(log => {
                addLog('Grouping', log.replace(/^\[.*?\]\s*/, ''));
            });
        }
        
        displayGroups(result.groups);
        
        addLog('Success', `Created ${Object.keys(result.groups).length} group(s)`);
        
    } catch (error) {
        addLog('Error', `Failed to auto-group: ${error.message}`);
        console.error(error);
    }
}
