const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

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
