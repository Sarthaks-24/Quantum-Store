function displayJSONAnalysis(filename, analysis) {
    const resultsContainer = document.getElementById('analysisResults');
    document.getElementById('analysisCard').style.display = 'block';
    
    let html = `<h3 style="color: #667eea; margin-bottom: 15px;">📋 JSON Analysis: ${filename}</h3>`;
    
    if (analysis.schema) {
        html += `
            <div class="analysis-section">
                <div class="analysis-title">Schema (${analysis.record_count} records)</div>
        `;
        
        for (const [fieldName, fieldInfo] of Object.entries(analysis.schema)) {
            const confidence = Math.round((fieldInfo.confidence || 0) * 100);
            const presence = Math.round((fieldInfo.presence || 0) * 100);
            
            html += `
                <div class="schema-field">
                    <div>
                        <span class="field-name">${fieldName}</span>
                        <span class="field-type">${fieldInfo.type}</span>
                    </div>
                    <div style="font-size: 0.85em; color: #888; margin-top: 5px;">
                        Confidence: ${confidence}% | Presence: ${presence}%
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidence}%"></div>
                    </div>
                </div>
            `;
        }
        
        html += `</div>`;
    }
    
    if (analysis.inconsistencies && analysis.inconsistencies.length > 0) {
        html += `
            <div class="analysis-section">
                <div class="analysis-title">⚠️ Inconsistencies Found: ${analysis.inconsistencies.length}</div>
        `;
        
        analysis.inconsistencies.slice(0, 10).forEach(inconsistency => {
            html += `
                <div class="schema-field" style="border-left-color: #f5576c;">
                    <div><strong>Type:</strong> ${inconsistency.type}</div>
                    <div><strong>Severity:</strong> ${inconsistency.severity}</div>
                    ${inconsistency.field ? `<div><strong>Field:</strong> ${inconsistency.field}</div>` : ''}
                </div>
            `;
        });
        
        html += `</div>`;
    }
    
    if (analysis.statistics && Object.keys(analysis.statistics).length > 0) {
        html += `
            <div class="analysis-section">
                <div class="analysis-title">📊 Statistics</div>
                <div class="stat-grid">
        `;
        
        for (const [field, stats] of Object.entries(analysis.statistics)) {
            html += `
                <div class="stat-card">
                    <div style="font-weight: bold; color: #333; margin-bottom: 10px;">${field}</div>
                    <div style="font-size: 0.9em; color: #888;">
                        Min: ${stats.min?.toFixed(2)}<br>
                        Max: ${stats.max?.toFixed(2)}<br>
                        Mean: ${stats.mean?.toFixed(2)}<br>
                        Median: ${stats.median?.toFixed(2)}
                    </div>
                </div>
            `;
        }
        
        html += `</div></div>`;
    }
    
    if (analysis.outliers && Object.keys(analysis.outliers).length > 0) {
        html += `
            <div class="analysis-section">
                <div class="analysis-title">🎯 Outliers Detected</div>
        `;
        
        for (const [field, outlierInfo] of Object.entries(analysis.outliers)) {
            html += `
                <div class="schema-field">
                    <div><strong>${field}:</strong> ${outlierInfo.count} outlier(s)</div>
                    <div style="font-size: 0.85em; color: #888;">
                        Bounds: ${outlierInfo.bounds.lower.toFixed(2)} - ${outlierInfo.bounds.upper.toFixed(2)}
                    </div>
                </div>
            `;
        }
        
        html += `</div>`;
    }
    
    resultsContainer.innerHTML = html;
}

function displayTextAnalysis(filename, analysis) {
    const resultsContainer = document.getElementById('analysisResults');
    document.getElementById('analysisCard').style.display = 'block';
    
    let html = `<h3 style="color: #667eea; margin-bottom: 15px;">📝 Text Analysis: ${filename}</h3>`;
    
    html += `
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-value">${analysis.char_count?.toLocaleString()}</div>
                <div class="stat-label">Characters</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${analysis.word_count?.toLocaleString()}</div>
                <div class="stat-label">Words</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${analysis.line_count?.toLocaleString()}</div>
                <div class="stat-label">Lines</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${analysis.tokens?.unique?.toLocaleString()}</div>
                <div class="stat-label">Unique Tokens</div>
            </div>
        </div>
    `;
    
    if (analysis.readability) {
        html += `
            <div class="analysis-section">
                <div class="analysis-title">📖 Readability</div>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-value">${analysis.readability.score?.toFixed(1)}</div>
                        <div class="stat-label">Score</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${analysis.readability.level}</div>
                        <div class="stat-label">Level</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${analysis.readability.avg_sentence_length?.toFixed(1)}</div>
                        <div class="stat-label">Avg Sentence Length</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (analysis.tokens?.top_20) {
        html += `
            <div class="analysis-section">
                <div class="analysis-title">🔤 Top Tokens</div>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
        `;
        
        analysis.tokens.top_20.slice(0, 15).forEach(token => {
            const percentage = (token.frequency * 100).toFixed(2);
            html += `
                <div style="background: white; padding: 8px 12px; border-radius: 6px; border: 1px solid #667eea;">
                    <strong>${token.token}</strong> (${token.count}, ${percentage}%)
                </div>
            `;
        });
        
        html += `</div></div>`;
    }
    
    if (analysis.tfidf?.top_terms) {
        html += `
            <div class="analysis-section">
                <div class="analysis-title">🎯 TF-IDF Top Terms</div>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
        `;
        
        analysis.tfidf.top_terms.slice(0, 15).forEach(term => {
            html += `
                <div style="background: white; padding: 8px 12px; border-radius: 6px; border: 1px solid #764ba2;">
                    <strong>${term.term}</strong> (${term.tfidf_score.toFixed(3)})
                </div>
            `;
        });
        
        html += `</div></div>`;
    }
    
    resultsContainer.innerHTML = html;
}

function displayImageAnalysis(filename, analysis) {
    const resultsContainer = document.getElementById('analysisResults');
    document.getElementById('analysisCard').style.display = 'block';
    
    let html = `<h3 style="color: #667eea; margin-bottom: 15px;">🖼️ Image Analysis: ${filename}</h3>`;
    
    html += `
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-value">${analysis.width} × ${analysis.height}</div>
                <div class="stat-label">Dimensions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${analysis.format}</div>
                <div class="stat-label">Format</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${analysis.aspect_ratio?.toFixed(2)}</div>
                <div class="stat-label">Aspect Ratio</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${analysis.mode}</div>
                <div class="stat-label">Color Mode</div>
            </div>
        </div>
    `;
    
    if (analysis.category) {
        const confidence = Math.round((analysis.category.confidence || 0) * 100);
        html += `
            <div class="analysis-section">
                <div class="analysis-title">🏷️ Heuristic Category</div>
                <div class="schema-field" style="border-left-color: #764ba2;">
                    <div><strong>Category:</strong> ${analysis.category.category}</div>
                    <div><strong>Confidence:</strong> ${confidence}%</div>
                    <div class="confidence-bar" style="margin-top: 10px;">
                        <div class="confidence-fill" style="width: ${confidence}%"></div>
                    </div>
                    ${analysis.category.reasons ? `
                        <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                            <strong>Reasons:</strong>
                            <ul style="margin-left: 20px; margin-top: 5px;">
                                ${analysis.category.reasons.map(r => `<li>${r}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    if (analysis.quality) {
        html += `
            <div class="analysis-section">
                <div class="analysis-title">✨ Quality Metrics</div>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-value">${analysis.quality.brightness?.toFixed(1)}</div>
                        <div class="stat-label">Brightness</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${analysis.quality.sharpness?.toFixed(1)}</div>
                        <div class="stat-label">Sharpness</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${(analysis.quality.edge_density * 100)?.toFixed(2)}%</div>
                        <div class="stat-label">Edge Density</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (analysis.colors?.dominant_colors) {
        html += `
            <div class="analysis-section">
                <div class="analysis-title">🎨 Dominant Colors</div>
                <div style="display: flex; flex-wrap: wrap; gap: 15px;">
        `;
        
        analysis.colors.dominant_colors.slice(0, 5).forEach(color => {
            const percentage = (color.percentage * 100).toFixed(1);
            html += `
                <div style="text-align: center;">
                    <div style="width: 80px; height: 80px; background: ${color.hex}; border-radius: 8px; border: 2px solid #ddd;"></div>
                    <div style="margin-top: 5px; font-size: 0.85em; color: #666;">
                        ${color.hex}<br>${percentage}%
                    </div>
                </div>
            `;
        });
        
        html += `</div></div>`;
    }
    
    if (analysis.phash) {
        html += `
            <div class="analysis-section">
                <div class="analysis-title">🔒 Perceptual Hash</div>
                <div style="font-family: monospace; background: white; padding: 10px; border-radius: 6px;">
                    ${analysis.phash}
                </div>
            </div>
        `;
    }
    
    resultsContainer.innerHTML = html;
}

function displayGroups(groups) {
    const groupsContainer = document.getElementById('groupsContainer');
    const groupsCard = document.getElementById('groupsCard');
    
    groupsCard.style.display = 'block';
    groupsContainer.innerHTML = '';
    
    for (const [groupName, files] of Object.entries(groups)) {
        if (files.length === 0) continue;
        
        const groupCard = document.createElement('div');
        groupCard.className = 'group-card';
        
        let html = `
            <div class="group-title">${groupName.replace(/_/g, ' ').toUpperCase()} (${files.length})</div>
        `;
        
        files.forEach(file => {
            html += `
                <div class="group-item">
                    📄 ${file.filename || file.id}
                </div>
            `;
        });
        
        groupCard.innerHTML = html;
        groupsContainer.appendChild(groupCard);
    }
    
    groupsCard.scrollIntoView({ behavior: 'smooth' });
}
