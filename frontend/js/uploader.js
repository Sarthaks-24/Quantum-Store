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
            // Check if it's a 413 (upload too large) error
            if (error.message.includes('413') || error.message.toLowerCase().includes('1gb limit')) {
                addLog('Error', `❌ File too large: ${file.name} exceeds 1GB limit`);
            } else {
                addLog('Error', `Failed to process ${file.name}: ${error.message}`);
            }
            console.error(error);
        }
    }
    
    await loadFiles();
}

async function handleFolderUpload(files) {
    const fileCount = files.length;
    addLog('System', `Starting multi-file upload (${fileCount} files)...`);
    
    // Show progress container
    const progressHtml = `
        <div id="uploadProgress" class="progress-container">
            <div class="progress-text" id="progressText">Checking folder size...</div>
            <div class="progress-bar" id="progressBar" style="width: 0%"></div>
        </div>
    `;
    
    const logContainer = document.getElementById('reasoningLog');
    const progressDiv = document.createElement('div');
    progressDiv.innerHTML = progressHtml;
    logContainer.appendChild(progressDiv);
    
    try {
        // Step 1: Pre-upload size check
        addLog('Check', `Calculating total folder size...`);
        updateProgress(5, 'Calculating total size...');
        
        let totalSize = 0;
        const MAX_FOLDER_SIZE = 1 * 1024 * 1024 * 1024; // 1GB
        
        for (const file of files) {
            totalSize += file.size;
        }
        
        const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(2);
        const maxSizeMB = (MAX_FOLDER_SIZE / (1024 * 1024)).toFixed(0);
        
        addLog('Check', `Total folder size: ${totalSizeMB} MB`);
        
        // Reject immediately if > 1GB
        if (totalSize > MAX_FOLDER_SIZE) {
            updateProgress(100, 'Error: Folder too large');
            addLog('Error', `❌ Folder exceeds ${maxSizeMB} MB limit (${totalSizeMB} MB)`);
            addLog('Error', `Please select a smaller folder or remove some files`);
            
            setTimeout(() => {
                const prog = document.getElementById('uploadProgress');
                if (prog) prog.remove();
            }, 3000);
            
            return;
        }
        
        addLog('Success', `✓ Size check passed: ${totalSizeMB} MB / ${maxSizeMB} MB`);
        updateProgress(10, 'Size check passed');
        
        // Step 2: Upload files in groups to backend
        addLog('Upload', `[UPLOAD] Starting multi-file upload (${fileCount} files)`);
        
        const folderId = generateUUID();
        const GROUP_SIZE = 25; // Files per API request
        let successCount = 0;
        let failCount = 0;
        const allResults = [];
        let processedCount = 0;
        
        // Upload files in groups sequentially
        for (let i = 0; i < files.length; i += GROUP_SIZE) {
            const group = files.slice(i, i + GROUP_SIZE);
            
            // Log each file being uploaded
            group.forEach(file => {
                const fileSizeKB = (file.size / 1024).toFixed(2);
                addLog('Upload', `[UPLOAD] → Uploading ${file.name} (${fileSizeKB} KB)...`);
            });
            
            const uploadProgress = 10 + Math.floor((processedCount / fileCount) * 40);
            updateProgress(uploadProgress, `Uploading: ${processedCount}/${fileCount}`);
            
            try {
                const result = await api.uploadBatch(group, folderId);
                
                // Log individual file upload results
                if (result.results) {
                    result.results.forEach(fileResult => {
                        if (fileResult.error || fileResult.status === 'failed' || fileResult.status === 'rejected') {
                            addLog('Error', `[UPLOAD] → ${fileResult.filename} failed: ${fileResult.error || 'Unknown error'}`);
                            failCount++;
                        } else {
                            const fileId = fileResult.file_id || 'unknown';
                            addLog('Success', `[UPLOAD] → ${fileResult.filename} uploaded (ID: ${fileId.substring(0, 8)}...) ... OK`);
                            successCount++;
                        }
                        processedCount++;
                    });
                }
                
                allResults.push(...result.results);
                
            } catch (error) {
                // If entire group fails, mark all files as failed
                group.forEach(file => {
                    addLog('Error', `[UPLOAD] → ${file.name} failed: ${error.message}`);
                    failCount++;
                    processedCount++;
                });
            }
        }
        
        updateProgress(50, 'Upload complete, starting analysis...');
        
        // Step 3: Analysis stage - call backend analyze endpoints
        addLog('Summary', `[UPLOAD] Completed (${successCount}/${fileCount} files)`);
        addLog('Analysis', `[ANALYSIS] Starting file analysis...`);
        
        // Analyze files that were successfully uploaded
        const successfulFiles = allResults.filter(r => !r.error && r.file_id);
        let analyzedCount = 0;
        let analysisSuccessCount = 0;
        
        for (const fileResult of successfulFiles) {
            try {
                addLog('Analysis', `[ANALYSIS] Starting analysis for ${fileResult.filename}`);
                
                const analysisProgress = 50 + Math.floor((analyzedCount / successfulFiles.length) * 45);
                updateProgress(analysisProgress, `Analyzing: ${analyzedCount}/${successfulFiles.length}`);
                
                // Call appropriate analysis endpoint based on file type
                let analysisResult = null;
                const fileType = fileResult.file_type;
                const fileId = fileResult.file_id;
                
                addLog('Analysis', `[ANALYSIS] → Detecting file type: ${fileType}`);
                
                if (fileType === 'json') {
                    addLog('Analysis', `[ANALYSIS] → Extracting JSON metadata...`);
                    analysisResult = await api.analyzeJSON(fileId);
                    addLog('Analysis', `[ANALYSIS] → Saving schema...`);
                } else if (fileType === 'text') {
                    addLog('Analysis', `[ANALYSIS] → Extracting text metadata...`);
                    analysisResult = await api.analyzeText(fileId);
                    addLog('Analysis', `[ANALYSIS] → Computing text features...`);
                } else if (fileType === 'image') {
                    addLog('Analysis', `[ANALYSIS] → Extracting image metadata...`);
                    analysisResult = await api.analyzeImage(fileId);
                    addLog('Analysis', `[ANALYSIS] → Computing perceptual hash...`);
                } else {
                    addLog('Analysis', `[ANALYSIS] → Unsupported type, skipping analysis`);
                }
                
                if (analysisResult) {
                    addLog('Analysis', `[ANALYSIS] ✔ Completed: ${fileResult.filename}`);
                    analysisSuccessCount++;
                } else {
                    addLog('Analysis', `[ANALYSIS] → ${fileResult.filename} ... SKIPPED`);
                }
                
            } catch (error) {
                addLog('Error', `[ANALYSIS] Failed for ${fileResult.filename}: ${error.message}`);
                console.error(`Analysis error for ${fileResult.filename}:`, error);
            }
            
            analyzedCount++;
        }
        
        updateProgress(95, 'Processing complete...');
        
        // Display summary
        addLog('Summary', `[ANALYSIS] Completed (${analysisSuccessCount}/${successfulFiles.length} files analyzed)`);
        
        // Show file type breakdown
        const typeBreakdown = {};
        allResults.forEach(r => {
            if (!r.error && r.file_type) {
                typeBreakdown[r.file_type] = (typeBreakdown[r.file_type] || 0) + 1;
            }
        });
        
        const typesList = Object.entries(typeBreakdown)
            .map(([type, count]) => `${type}: ${count}`)
            .join(', ');
        
        if (typesList) {
            addLog('Summary', `File types: ${typesList}`);
        }
        
        // Display folder summary card
        displayFolderSummary({
            folder_id: folderId,
            total_files: fileCount,
            successful: successCount,
            failed: failCount,
            results: allResults
        });
        
        updateProgress(100, 'Complete!');
        addLog('Complete', `Multi-file upload complete!`);
        
        // Remove progress bar after 2 seconds
        setTimeout(() => {
            const prog = document.getElementById('uploadProgress');
            if (prog) prog.remove();
        }, 2000);
        
    } catch (error) {
        addLog('Error', `Failed to upload folder: ${error.message}`);
        console.error(error);
        
        // Remove progress bar on error
        const prog = document.getElementById('uploadProgress');
        if (prog) prog.remove();
    }
    
    await loadFiles();
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function updateProgress(percent, text) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    if (progressBar) {
        progressBar.style.width = `${percent}%`;
    }
    
    if (progressText) {
        progressText.textContent = text;
    }
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
