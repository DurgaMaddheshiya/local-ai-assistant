/**
 * Main application controller for Local AI Assistant
 */

class App {
    constructor() {
        this.chatManager = null;
        this.conversations = [];
        this.filteredConversations = [];
        this.currentTheme = 'light';
        this.connectionStatus = 'offline';
        
        this.initializeApp();
    }

    async initializeApp() {
        this.initializeElements();
        this.bindEvents();
        this.loadTheme();
        
        // Initialize chat manager
        this.chatManager = new ChatManager();
        
        // Check system status
        await this.checkSystemStatus();
        
        // Load initial data
        await this.loadConversations();
        await this.chatManager.loadModels();
        
        // Show welcome screen initially
        this.chatManager.showWelcomeScreen();
        
        console.log('Local AI Assistant initialized');
    }

    initializeElements() {
        // Sidebar elements
        this.sidebar = document.getElementById('sidebar');
        this.newChatBtn = document.getElementById('new-chat-btn');
        this.conversationList = document.getElementById('conversation-list');
        this.searchInput = document.getElementById('search-conversations');
        this.clearSearchBtn = document.getElementById('clear-search');
        this.settingsBtn = document.getElementById('settings-btn');
        this.aboutBtn = document.getElementById('about-btn');
        this.connectionStatus = document.getElementById('connection-status');
        this.connectionText = document.getElementById('connection-text');
        
        console.log('About button element:', this.aboutBtn); // DEBUG
        
        // Welcome screen
        this.startChattingBtn = document.getElementById('start-chatting');
        
        // Settings modal elements
        this.settingsModal = document.getElementById('settings-modal');
        this.closeSettingsBtn = document.getElementById('close-settings');
        this.themeSelect = document.getElementById('theme-select');
        this.temperatureSlider = document.getElementById('temperature-slider');
        this.temperatureValue = document.getElementById('temperature-value');
        this.maxTokensInput = document.getElementById('max-tokens-input');
        this.systemPromptTextarea = document.getElementById('system-prompt-textarea');
        this.clearAllDataBtn = document.getElementById('clear-all-data');
        this.saveSettingsBtn = document.getElementById('save-settings');
        
        // About modal elements
        this.aboutModal = document.getElementById('about-modal');
        this.closeAboutBtn = document.getElementById('close-about');
        
        console.log('About modal element:', this.aboutModal); // DEBUG
        
        // Confirmation modal
        this.confirmModal = document.getElementById('confirm-modal');
        this.confirmTitle = document.getElementById('confirm-title');
        this.confirmMessage = document.getElementById('confirm-message');
        this.confirmOkBtn = document.getElementById('confirm-ok');
        this.confirmCancelBtn = document.getElementById('confirm-cancel');
        
        // Toast container
        this.toastContainer = document.getElementById('toast-container');
    }

    bindEvents() {
        // Sidebar events
        this.newChatBtn.addEventListener('click', () => this.startNewChat());
        this.searchInput.addEventListener('input', () => this.handleSearch());
        this.clearSearchBtn.addEventListener('click', () => this.clearSearch());
        this.settingsBtn.addEventListener('click', () => this.openSettings());
        
        if (this.aboutBtn) {
            this.aboutBtn.addEventListener('click', () => {
                console.log('About button clicked!'); // DEBUG
                this.openAbout();
            });
        } else {
            console.warn('About button not found!'); // DEBUG
        }
        
        this.startChattingBtn.addEventListener('click', () => this.startNewChat());
        
        // Settings modal events
        this.closeSettingsBtn.addEventListener('click', () => this.closeSettings());
        this.themeSelect.addEventListener('change', () => this.handleThemeChange());
        this.temperatureSlider.addEventListener('input', () => this.updateTemperatureValue());
        this.clearAllDataBtn.addEventListener('click', () => this.confirmClearAllData());
        this.saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        
        // About modal events
        if (this.closeAboutBtn) {
            this.closeAboutBtn.addEventListener('click', () => this.closeAbout());
        }
        
        // Confirmation modal events
        this.confirmCancelBtn.addEventListener('click', () => this.closeConfirmModal());
        
        // Click outside modals to close
        window.addEventListener('click', (event) => {
            if (event.target === this.settingsModal) {
                this.closeSettings();
            }
            if (event.target === this.aboutModal) {
                this.closeAbout();
            }
            if (event.target === this.confirmModal) {
                this.closeConfirmModal();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            // Ctrl/Cmd + N for new chat
            if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
                event.preventDefault();
                this.startNewChat();
            }
            // Escape to close modals
            if (event.key === 'Escape') {
                this.closeSettings();
                this.closeAbout();
                this.closeConfirmModal();
            }
        });
    }

    async checkSystemStatus() {
        try {
            const status = await window.api.getSystemStatus();
            
            // Update connection indicator
            const isHealthy = status.backend === 'ok' && status.ollama === 'connected';
            this.updateConnectionStatus(isHealthy ? 'online' : 'offline');
            
            // Update status text
            if (isHealthy) {
                this.connectionText.textContent = `Local AI (${status.model})`;
            } else {
                this.connectionText.textContent = 'AI Service Offline';
            }
            
            return status;
        } catch (error) {
            console.error('System status check failed:', error);
            this.updateConnectionStatus('offline');
            this.connectionText.textContent = 'Connection Error';
            return null;
        }
    }

    updateConnectionStatus(status) {
        this.connectionStatus.className = `status-dot ${status}`;
    }

    async loadConversations() {
        try {
            this.showConversationLoading(true);
            const conversations = await window.api.getConversations(50);
            this.conversations = conversations;
            this.filteredConversations = conversations;
            this.renderConversations();
        } catch (error) {
            console.error('Error loading conversations:', error);
            this.showToast('Failed to load conversations', 'error');
        } finally {
            this.showConversationLoading(false);
        }
    }

    renderConversations() {
        if (this.filteredConversations.length === 0) {
            this.conversationList.innerHTML = `
                <div class="no-conversations">
                    <i class="fas fa-comments"></i>
                    <p>No conversations yet</p>
                    <p>Start a new chat to begin</p>
                </div>
            `;
            return;
        }

        this.conversationList.innerHTML = '';
        
        for (const conversation of this.filteredConversations) {
            const item = this.createConversationItem(conversation);
            this.conversationList.appendChild(item);
        }
    }

    createConversationItem(conversation) {
        const item = document.createElement('div');
        item.className = 'conversation-item';
        item.dataset.conversationId = conversation.id;
        
        const isActive = this.chatManager && this.chatManager.currentConversationId === conversation.id;
        if (isActive) {
            item.classList.add('active');
        }

        item.innerHTML = `
            <div class="conversation-info">
                <div class="conversation-title">${this.escapeHtml(conversation.title)}</div>
                <div class="conversation-meta">${this.formatDate(conversation.updated_at)} • ${conversation.message_count} messages</div>
            </div>
            <div class="conversation-actions">
                <button class="conversation-action delete-conversation" title="Delete conversation">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;

        // Click to open conversation
        item.addEventListener('click', (event) => {
            if (!event.target.closest('.conversation-actions')) {
                this.openConversation(conversation.id);
            }
        });

        // Delete button
        const deleteBtn = item.querySelector('.delete-conversation');
        deleteBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            this.deleteConversation(conversation.id);
        });

        return item;
    }

    showConversationLoading(show) {
        if (show) {
            this.conversationList.innerHTML = `
                <div class="loading-conversations">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Loading conversations...</span>
                </div>
            `;
        }
    }

    handleSearch() {
        const query = this.searchInput.value.trim().toLowerCase();
        
        if (query) {
            this.clearSearchBtn.style.display = 'block';
            this.filteredConversations = this.conversations.filter(conv => 
                conv.title.toLowerCase().includes(query)
            );
        } else {
            this.clearSearchBtn.style.display = 'none';
            this.filteredConversations = this.conversations;
        }
        
        this.renderConversations();
    }

    clearSearch() {
        this.searchInput.value = '';
        this.clearSearchBtn.style.display = 'none';
        this.filteredConversations = this.conversations;
        this.renderConversations();
    }

    async startNewChat() {
        await this.chatManager.startNewChat();
        this.clearConversationSelection();
    }

    async openConversation(conversationId) {
        await this.chatManager.loadConversation(conversationId);
        this.updateConversationSelection(conversationId);
    }

    updateConversationSelection(conversationId) {
        // Remove active class from all items
        this.conversationList.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to selected item
        const selectedItem = this.conversationList.querySelector(`[data-conversation-id="${conversationId}"]`);
        if (selectedItem) {
            selectedItem.classList.add('active');
        }
    }

    clearConversationSelection() {
        this.conversationList.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
    }

    async deleteConversation(conversationId) {
        const conversation = this.conversations.find(c => c.id === conversationId);
        const confirmMessage = `Delete "${conversation?.title || 'this conversation'}"? This cannot be undone.`;
        
        const confirmed = await this.showConfirmDialog('Delete Conversation', confirmMessage);
        if (confirmed) {
            try {
                await window.api.deleteConversation(conversationId);
                
                // If this was the current conversation, show welcome screen
                if (this.chatManager.currentConversationId === conversationId) {
                    this.chatManager.showWelcomeScreen();
                    this.chatManager.currentConversationId = null;
                }
                
                await this.loadConversations();
                this.showToast('Conversation deleted', 'success');
            } catch (error) {
                console.error('Error deleting conversation:', error);
                this.showToast('Failed to delete conversation', 'error');
            }
        }
    }

    // Settings management
    async openSettings() {
        this.settingsModal.style.display = 'flex';
        await this.loadSettings();
        await this.updateSystemStatusInSettings();
    }

    closeSettings() {
        this.settingsModal.style.display = 'none';
    }

    async loadSettings() {
        try {
            const settings = await window.api.getSettings();
            
            this.themeSelect.value = this.currentTheme;
            this.temperatureSlider.value = settings.temperature;
            this.temperatureValue.textContent = settings.temperature;
            this.maxTokensInput.value = settings.max_tokens;
            this.systemPromptTextarea.value = settings.system_prompt;
            
        } catch (error) {
            console.error('Error loading settings:', error);
            this.showToast('Failed to load settings', 'error');
        }
    }

    async saveSettings() {
        try {
            const settings = {
                temperature: parseFloat(this.temperatureSlider.value),
                max_tokens: parseInt(this.maxTokensInput.value),
                system_prompt: this.systemPromptTextarea.value
            };
            
            await window.api.updateSettings(settings);
            
            // Save local settings
            localStorage.setItem('temperature', settings.temperature);
            localStorage.setItem('max_tokens', settings.max_tokens);
            
            this.showToast('Settings saved successfully', 'success');
            this.closeSettings();
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showToast('Failed to save settings', 'error');
        }
    }

    updateTemperatureValue() {
        this.temperatureValue.textContent = this.temperatureSlider.value;
    }

    async updateSystemStatusInSettings() {
        const statusElements = {
            'backend-status': 'Checking...',
            'ollama-status': 'Checking...',
            'model-status': 'Checking...',
            'database-status': 'Checking...'
        };
        
        // Reset all status elements
        Object.keys(statusElements).forEach(id => {
            const element = document.getElementById(id);
            element.textContent = statusElements[id];
            element.className = 'status-unknown';
        });
        
        try {
            const status = await this.checkSystemStatus();
            if (status) {
                this.updateStatusElement('backend-status', status.backend);
                this.updateStatusElement('ollama-status', status.ollama);
                this.updateStatusElement('model-status', status.model);
                this.updateStatusElement('database-status', status.database);
            }
        } catch (error) {
            console.error('Error updating system status:', error);
        }
    }

    updateStatusElement(elementId, status) {
        const element = document.getElementById(elementId);
        
        if (status === 'ok' || status === 'connected') {
            element.textContent = 'Online';
            element.className = 'status-ok';
        } else if (status === 'error' || status === 'disconnected') {
            element.textContent = 'Offline';
            element.className = 'status-error';
        } else {
            element.textContent = status;
            element.className = 'status-unknown';
        }
    }

    // Theme management
    loadTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
    }

    setTheme(theme) {
        this.currentTheme = theme;
        document.body.className = `${theme}-theme`;
        localStorage.setItem('theme', theme);
        
        if (this.themeSelect) {
            this.themeSelect.value = theme;
        }
    }

    async handleThemeChange() {
        const newTheme = this.themeSelect.value;
        this.setTheme(newTheme);
        
        try {
            await window.api.setTheme(newTheme);
        } catch (error) {
            console.warn('Failed to save theme to server:', error);
        }
    }

    // About modal
    openAbout() {
        this.aboutModal.style.display = 'flex';
    }

    closeAbout() {
        this.aboutModal.style.display = 'none';
    }

    // Confirmation dialog
    async showConfirmDialog(title, message) {
        return new Promise((resolve) => {
            this.confirmTitle.textContent = title;
            this.confirmMessage.textContent = message;
            this.confirmModal.style.display = 'flex';
            
            const handleOk = () => {
                this.closeConfirmModal();
                resolve(true);
                cleanup();
            };
            
            const handleCancel = () => {
                this.closeConfirmModal();
                resolve(false);
                cleanup();
            };
            
            const cleanup = () => {
                this.confirmOkBtn.removeEventListener('click', handleOk);
                this.confirmCancelBtn.removeEventListener('click', handleCancel);
            };
            
            this.confirmOkBtn.addEventListener('click', handleOk);
            this.confirmCancelBtn.addEventListener('click', handleCancel);
        });
    }

    closeConfirmModal() {
        this.confirmModal.style.display = 'none';
    }

    async confirmClearAllData() {
        const confirmed = await this.showConfirmDialog(
            'Clear All Data',
            'This will delete ALL conversations permanently. This action cannot be undone.'
        );
        
        if (confirmed) {
            try {
                await window.api.deleteAllConversations();
                await this.loadConversations();
                this.chatManager.showWelcomeScreen();
                this.chatManager.currentConversationId = null;
                this.showToast('All conversations deleted', 'success');
            } catch (error) {
                console.error('Error clearing all data:', error);
                this.showToast('Failed to clear conversations', 'error');
            }
        }
    }

    // Toast notifications
    showToast(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-message">${this.escapeHtml(message)}</div>
            </div>
            <button class="toast-close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.removeToast(toast));
        
        this.toastContainer.appendChild(toast);
        
        // Auto-remove after duration
        setTimeout(() => this.removeToast(toast), duration);
    }

    removeToast(toast) {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }

    // Utility functions
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffHours < 1) {
            return 'Just now';
        } else if (diffHours < 24) {
            return `${diffHours}h ago`;
        } else if (diffDays < 7) {
            return `${diffDays}d ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

// Export for global access
window.App = App;