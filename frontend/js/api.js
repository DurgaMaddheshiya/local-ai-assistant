/**
 * API Client for Local AI Assistant
 */

class APIClient {
    constructor() {
        this.baseUrl = '';  // Same origin
        this.timeout = 30000;  // 30 seconds default timeout
    }

    /**
     * Make HTTP request
     */
    async request(url, options = {}) {
        const config = {
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(`${this.baseUrl}${url}`, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new APIError(
                    errorData.error || 'Request failed',
                    response.status,
                    errorData.detail
                );
            }

            // Handle different response types
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }
            throw new APIError('Network error', 0, error.message);
        }
    }

    /**
     * GET request
     */
    async get(url, params = {}) {
        const searchParams = new URLSearchParams(params);
        const queryString = searchParams.toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        return this.request(fullUrl, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(url, data = null) {
        return this.request(url, {
            method: 'POST',
            body: data ? JSON.stringify(data) : null
        });
    }

    /**
     * PATCH request
     */
    async patch(url, data = null) {
        return this.request(url, {
            method: 'PATCH',
            body: data ? JSON.stringify(data) : null
        });
    }

    /**
     * DELETE request
     */
    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }

    // Health and System endpoints
    async checkHealth() {
        return this.get('/api/health');
    }

    async getSystemStatus() {
        return this.get('/api/status');
    }

    // Model endpoints
    async getModels() {
        return this.get('/api/models');
    }

    async getCurrentModel() {
        return this.get('/api/models/current');
    }

    async selectModel(modelName) {
        return this.post('/api/models/select', { model: modelName });
    }

    // Conversation endpoints
    async getConversations(limit = 50, offset = 0, search = null) {
        const params = { limit, offset };
        if (search) params.search = search;
        return this.get('/api/conversations', params);
    }

    async createConversation(title, model = null) {
        return this.post('/api/conversations', { title, model });
    }

    async getConversation(conversationId) {
        return this.get(`/api/conversations/${conversationId}`);
    }

    async updateConversation(conversationId, updates) {
        return this.patch(`/api/conversations/${conversationId}`, updates);
    }

    async deleteConversation(conversationId) {
        return this.delete(`/api/conversations/${conversationId}`);
    }

    async deleteAllConversations() {
        return this.delete('/api/conversations?confirm=true');
    }

    async getConversationStats() {
        return this.get('/api/conversations/stats');
    }

    // Chat endpoints
    async sendMessage(message, conversationId = null, options = {}) {
        const payload = {
            message,
            conversation_id: conversationId,
            stream: false,  // Non-streaming
            ...options
        };
        return this.post('/api/chat', payload);
    }

    /**
     * Send streaming chat message
     */
    async sendStreamingMessage(message, conversationId = null, options = {}) {
        const payload = {
            message,
            conversation_id: conversationId,
            stream: true,
            ...options
        };

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new APIError(
                errorData.error || 'Chat request failed',
                response.status,
                errorData.detail
            );
        }

        return response;
    }

    async stopGeneration(conversationId = null) {
        return this.post('/api/chat/stop', { conversation_id: conversationId });
    }

    // Settings endpoints
    async getSettings() {
        return this.get('/api/settings');
    }

    async updateSettings(settings) {
        return this.patch('/api/settings', settings);
    }

    async getTheme() {
        return this.get('/api/settings/theme');
    }

    async setTheme(theme) {
        return this.post(`/api/settings/theme?theme=${theme}`);
    }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, status, detail) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.detail = detail;
    }

    toString() {
        return `${this.message}${this.detail ? ': ' + this.detail : ''}`;
    }
}

/**
 * Stream reader for handling Server-Sent Events
 */
class StreamReader {
    constructor(response) {
        this.reader = response.body.getReader();
        this.decoder = new TextDecoder();
    }

    async *readChunks() {
        try {
            while (true) {
                const { value, done } = await this.reader.read();
                
                if (done) {
                    break;
                }

                const chunk = this.decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            yield data;
                        } catch (e) {
                            console.warn('Failed to parse streaming data:', line);
                        }
                    }
                }
            }
        } finally {
            this.reader.releaseLock();
        }
    }
}

// Export API client instance
window.api = new APIClient();
window.APIError = APIError;
window.StreamReader = StreamReader;