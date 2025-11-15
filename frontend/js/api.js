const API_BASE_URL = 'http://localhost:8000';

class QuantumStoreAPI {
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        return await response.json();
    }

    async uploadFolder(files) {
        const formData = new FormData();
        for (const file of files) {
            formData.append('files', file);
        }

        const response = await fetch(`${API_BASE_URL}/upload/folder`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Folder upload failed: ${response.statusText}`);
        }

        return await response.json();
    }

    async uploadBatch(files, folderId) {
        const formData = new FormData();
        formData.append('folder_id', folderId);
        
        // Validate that we're sending actual File objects
        for (const file of files) {
            if (!(file instanceof File)) {
                console.error('Invalid file object:', file, 'Type:', typeof file);
                throw new Error(`Expected File object, got ${typeof file}`);
            }
            console.log('Adding file to upload:', file.name, 'Size:', file.size, 'Type:', file.type);
            formData.append('files', file);
        }

        console.log(`Uploading ${files.length} files to folder ${folderId}`);

        const response = await fetch(`${API_BASE_URL}/upload/batch`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Multi-file upload failed: ${response.statusText} - ${errorText}`);
        }

        return await response.json();
    }

    async analyzeJSON(fileId) {
        const response = await fetch(`${API_BASE_URL}/analyze/json?file_id=${fileId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`Analysis failed: ${response.statusText}`);
        }

        return await response.json();
    }

    async analyzeText(fileId) {
        const response = await fetch(`${API_BASE_URL}/analyze/text?file_id=${fileId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`Analysis failed: ${response.statusText}`);
        }

        return await response.json();
    }

    async analyzeImage(fileId) {
        const response = await fetch(`${API_BASE_URL}/analyze/image?file_id=${fileId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`Analysis failed: ${response.statusText}`);
        }

        return await response.json();
    }

    async analyzePDF(fileId) {
        const response = await fetch(`${API_BASE_URL}/analyze/pdf?file_id=${fileId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`Analysis failed: ${response.statusText}`);
        }

        return await response.json();
    }

    async getFile(fileId) {
        const response = await fetch(`${API_BASE_URL}/file/${fileId}`);

        if (!response.ok) {
            throw new Error(`Failed to fetch file: ${response.statusText}`);
        }

        return await response.json();
    }

    async getAllFiles() {
        const response = await fetch(`${API_BASE_URL}/files`);

        if (!response.ok) {
            throw new Error(`Failed to fetch files: ${response.statusText}`);
        }

        return await response.json();
    }

    async autoGroup() {
        const response = await fetch(`${API_BASE_URL}/groups/auto`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`Grouping failed: ${response.statusText}`);
        }

        return await response.json();
    }

    async getSchemas() {
        const response = await fetch(`${API_BASE_URL}/schemas`);

        if (!response.ok) {
            throw new Error(`Failed to fetch schemas: ${response.statusText}`);
        }

        return await response.json();
    }

    async healthCheck() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    async getFilePreview(fileId) {
        const response = await fetch(`${API_BASE_URL}/file/${fileId}/preview`);

        if (!response.ok) {
            throw new Error(`Failed to fetch file preview: ${response.statusText}`);
        }

        return await response.json();
    }

    getFileDownloadUrl(fileId) {
        return `${API_BASE_URL}/file/${fileId}/download`;
    }
}

const api = new QuantumStoreAPI();
