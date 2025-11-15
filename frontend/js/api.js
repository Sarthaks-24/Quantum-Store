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
}

const api = new QuantumStoreAPI();
