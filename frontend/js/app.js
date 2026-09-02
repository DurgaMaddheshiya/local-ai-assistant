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
        this.isRecording = false;
        this.incognitoMode = false;

        this.initializeApp();
    }

    async initializeApp() {
        this.initializeElements();
        this.bindEvents();
        this.loadTheme();
        this.loadSidebarState();
        this.loadAccentColor();
        this.loadZoom();
        
        // Apply app opacity from localStorage
        const appOpacity = localStorage.getItem('appOpacity') || '100';
        this.updateAppOpacityDisplay(appOpacity);
        
        // Apply disclaimer opacity from localStorage
        const disclaimerOpacity = localStorage.getItem('disclaimerOpacity') || '100';
        this.updateDisclaimerOpacityDisplay(disclaimerOpacity);
        
        // Initialize chat manager
        this.chatManager = new ChatManager();
        window.chatManager = this.chatManager; // expose for code copy buttons
        
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
        this.sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
        this.connectionStatus = document.getElementById('connection-status');
        this.connectionText = document.getElementById('connection-text');
        
        // App container
        this.app = document.getElementById('app');
        
        // Welcome screen
        this.startChattingBtn = document.getElementById('start-chatting');
        
        // Settings modal elements
        this.settingsModal = document.getElementById('settings-modal');
        this.closeSettingsBtn = document.getElementById('close-settings');
        this.themeSelect = document.getElementById('theme-select');
        this.appOpacitySlider = document.getElementById('app-opacity-slider');
        this.appOpacityValue = document.getElementById('app-opacity-value');
        this.disclaimerOpacitySlider = document.getElementById('disclaimer-opacity-slider');
        this.disclaimerOpacityValue = document.getElementById('disclaimer-opacity-value');
        this.temperatureSlider = document.getElementById('temperature-slider');
        this.temperatureValue = document.getElementById('temperature-value');
        this.maxTokensInput = document.getElementById('max-tokens-input');
        this.systemPromptTextarea = document.getElementById('system-prompt-textarea');
        this.clearAllDataBtn = document.getElementById('clear-all-data');
        this.saveSettingsBtn = document.getElementById('save-settings');
        
        this.incognitoBtn = document.getElementById('incognito-btn');
        this.incognitoBanner = document.getElementById('incognito-banner');
        this.exitIncognitoBtn = document.getElementById('exit-incognito-btn');
        this.templatesBtn = document.getElementById('templates-btn');
        this.templatesModal = document.getElementById('templates-modal');
        this.closeTemplatesBtn = document.getElementById('close-templates');
        this.screenshotBtn = document.getElementById('screenshot-btn');

        // Accent color elements
        this.accentColorPicker = document.getElementById('accent-color-picker');
        this.accentPresets = document.querySelectorAll('.accent-preset');

        // API Key inputs
        this.openaiKeyInput = document.getElementById('openai-key-input');
        this.geminiKeyInput = document.getElementById('gemini-key-input');
        this.claudeKeyInput = document.getElementById('claude-key-input');

        // Zoom controls
        this.zoomInBtn = document.getElementById('zoom-in-btn');
        this.zoomOutBtn = document.getElementById('zoom-out-btn');
        this.zoomLevel = document.getElementById('zoom-level');

        // Shortcut recorder elements
        this.shortcutDisplay = document.getElementById('shortcut-display');
        this.shortcutKeysLabel = document.getElementById('shortcut-keys-label');
        this.recordShortcutBtn = document.getElementById('record-shortcut-btn');
        this.resetShortcutBtn = document.getElementById('reset-shortcut-btn');
        this.shortcutHint = document.getElementById('shortcut-hint');

        // Sidebar disclaimer
        this.sidebarDisclaimer = document.querySelector('.sidebar-disclaimer');
        
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
        this.newChatBtn?.addEventListener('click', () => this.startNewChat());
        this.searchInput?.addEventListener('input', () => this.handleSearch());
        this.clearSearchBtn?.addEventListener('click', () => this.clearSearch());
        this.settingsBtn?.addEventListener('click', () => this.openSettings());
        this.startChattingBtn?.addEventListener('click', () => this.startNewChat());
        this.sidebarToggleBtn?.addEventListener('click', () => this.toggleSidebar());

        // Home button - go to welcome screen
        document.getElementById('home-btn')?.addEventListener('click', () => this.goHome());

        // Settings modal events
        this.closeSettingsBtn?.addEventListener('click', () => this.closeSettings());
        this.themeSelect?.addEventListener('change', () => this.handleThemeChange());
        this.appOpacitySlider?.addEventListener('input', () => this.updateAppOpacity());
        this.disclaimerOpacitySlider?.addEventListener('input', () => this.updateDisclaimerOpacity());
        this.temperatureSlider?.addEventListener('input', () => this.updateTemperatureValue());
        this.clearAllDataBtn?.addEventListener('click', () => this.confirmClearAllData());
        this.saveSettingsBtn?.addEventListener('click', () => this.saveSettings());

        // Incognito events
        this.incognitoBtn?.addEventListener('click', () => this.toggleIncognito());
        this.exitIncognitoBtn?.addEventListener('click', () => this.toggleIncognito(false));

        // Zoom events
        this.zoomInBtn?.addEventListener('click', () => this.adjustZoom(10));
        this.zoomOutBtn?.addEventListener('click', () => this.adjustZoom(-10));

        // Templates events
        this.templatesBtn?.addEventListener('click', () => this.openTemplates());
        this.closeTemplatesBtn?.addEventListener('click', () => this.closeTemplates());
        document.querySelectorAll('.template-card').forEach(card => {
            card.addEventListener('click', () => this.applyTemplate(card.dataset.prompt));
        });

        // Screenshot button event
        this.screenshotBtn?.addEventListener('click', () => this.takeScreenshot());
        
        // Academic subject shortcuts
        document.querySelectorAll('.subject-shortcut').forEach(btn => {
            btn.addEventListener('click', () => this.applySubjectTemplate(btn.dataset.subject));
        });

        // Accent color events
        this.accentColorPicker?.addEventListener('input', (e) => this.applyAccentColor(e.target.value));
        this.accentPresets.forEach(btn => {
            btn.addEventListener('click', () => {
                this.applyAccentColor(btn.dataset.color);
                if (this.accentColorPicker) this.accentColorPicker.value = btn.dataset.color;
            });
        });

        // Shortcut recorder events
        this.recordShortcutBtn?.addEventListener('click', () => this.startRecording());
        this.resetShortcutBtn?.addEventListener('click', () => this.resetShortcut());

        // Confirmation modal events
        this.confirmCancelBtn?.addEventListener('click', () => this.closeConfirmModal());

        // Click outside modals to close
        window.addEventListener('click', (event) => {
            if (event.target === this.settingsModal) this.closeSettings();
            if (event.target === this.confirmModal) this.closeConfirmModal();
            if (event.target === this.templatesModal) this.closeTemplates();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            // Dynamic hide/show shortcut
            const savedShortcut = localStorage.getItem('hideShortcut') || 'ctrl+h';
            if (this.matchesShortcut(event, savedShortcut)) {
                if (!this.isRecording) {
                    event.preventDefault();
                    if (window.pywebview && window.pywebview.api) {
                        window.pywebview.api.toggle_visibility();
                    }
                }
            }
            // Ctrl/Cmd + N for new chat
            if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
                event.preventDefault();
                this.startNewChat();
            }
            // Escape to close modals
            if (event.key === 'Escape') {
                this.closeSettings();
                this.closeConfirmModal();
                this.closeTemplates();
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
                <div class="conversation-meta">${this.formatDate(conversation.updated_at)} ΓÇó ${conversation.message_count} messages</div>
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

    // ── Incognito Mode ────────────────────────────────────────────────────

    toggleIncognito(forceState = null) {
        this.incognitoMode = forceState !== null ? forceState : !this.incognitoMode;

        // Update button appearance
        this.incognitoBtn.classList.toggle('active', this.incognitoMode);
        const icon = this.incognitoBtn.querySelector('i');
        icon.style.color = this.incognitoMode ? '#a855f7' : '';

        // Show/hide banner
        if (this.incognitoBanner) {
            this.incognitoBanner.style.display = this.incognitoMode ? 'flex' : 'none';
        }

        // Start a fresh chat in incognito (clear conversation ID)
        if (this.incognitoMode && this.chatManager) {
            this.chatManager.startNewChat();
            this.chatManager.currentConversationId = null;
        }

        this.showToast(
            this.incognitoMode ? 'Incognito mode ON — chats won\'t be saved' : 'Incognito mode OFF',
            this.incognitoMode ? 'warning' : 'success'
        );
    }

    // ── Conversation Templates ────────────────────────────────────────────

    openTemplates() {
        if (this.templatesModal) this.templatesModal.style.display = 'flex';
    }

    closeTemplates() {
        if (this.templatesModal) this.templatesModal.style.display = 'none';
    }

    async applyTemplate(systemPrompt) {
        this.closeTemplates();
        // Start new chat
        await this.chatManager.startNewChat();
        // Override system prompt for this session only (stored in chatManager)
        this.chatManager.templateSystemPrompt = systemPrompt;
        this.showToast('Template applied — start chatting!', 'success');
        // Focus input
        if (this.chatManager.messageInput) {
            this.chatManager.messageInput.focus();
        }
    }

    // ── Academic Subject Templates ────────────────────────────────────────
    async applySubjectTemplate(subject) {
        const templates = {
            math: "You are a mathematics tutor. Help me solve math problems step-by-step. Explain concepts clearly, show all working, and help me understand the logic behind each solution. Cover algebra, calculus, geometry, statistics, and more.",
            
            science: "You are a science tutor specializing in Physics, Chemistry, and Biology. Explain scientific concepts clearly, help with calculations, and provide real-world examples. Break down complex topics into understandable parts.",
            
            code: "You are a computer science instructor. Help me understand programming concepts, debug code, explain algorithms, and provide clean examples. Focus on learning and best practices, not just solutions.",
            
            essay: "You are an academic writing coach. Help me structure essays, develop arguments, improve grammar, create outlines, and strengthen thesis statements. Guide me through the writing process step-by-step.",
            
            history: "You are a history teacher. Help me understand historical events, analyze causes and effects, explain connections between past and present, and provide context for historical developments.",
            
            language: "You are a language tutor. Help me with grammar, vocabulary, sentence structure, and language learning. Provide explanations, corrections, and practice exercises as needed.",
            
            homework: "You are a homework assistant. I'll show you images of assignments or problems. Analyze them carefully, provide step-by-step solutions, and explain the concepts involved. Focus on teaching, not just answering.",
            
            research: "You are a research assistant. Help me find reliable sources, understand research methods, organize information, create proper citations, and structure academic projects effectively."
        };

        const systemPrompt = templates[subject];
        if (systemPrompt) {
            // Start new chat with subject template
            await this.chatManager.startNewChat();
            this.chatManager.templateSystemPrompt = systemPrompt;
            
            // Show subject-specific toast
            const subjectNames = {
                math: 'Mathematics', science: 'Science', code: 'Programming', 
                essay: 'Writing', history: 'History', language: 'Language',
                homework: 'Homework Scanner', research: 'Research'
            };
            
            this.showToast(`📚 ${subjectNames[subject]} tutor ready!`, 'success');
            
            // Focus input
            if (this.chatManager.messageInput) {
                this.chatManager.messageInput.focus();
                // Add helpful placeholder
                this.chatManager.messageInput.placeholder = `Ask your ${subjectNames[subject].toLowerCase()} question...`;
            }
        }
    }

    // ── Accent Color ──────────────────────────────────────────────────────

    applyAccentColor(hex) {
        // Derive hover (darken ~20%) and secondary (darken ~40%)
        const hover     = this.darkenColor(hex, 0.2);
        const secondary = this.darkenColor(hex, 0.4);

        const root = document.documentElement;
        root.style.setProperty('--primary-color',   hex);
        root.style.setProperty('--primary-hover',   hover);
        root.style.setProperty('--secondary-color', secondary);
        root.style.setProperty('--danger-color',    hex);
        root.style.setProperty('--border-hover',    hex);

        // Fix rgba hardcoded shadow (shortcut recorder blink)
        root.style.setProperty('--primary-color-alpha', this.hexToRgba(hex, 0.2));

        localStorage.setItem('accentColor', hex);

        // Update active state on presets
        this.accentPresets.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.color === hex);
        });
        if (this.accentColorPicker) this.accentColorPicker.value = hex;
    }

    darkenColor(hex, amount) {
        const num = parseInt(hex.replace('#',''), 16);
        const r = Math.max(0, (num >> 16) - Math.round(255 * amount));
        const g = Math.max(0, ((num >> 8) & 0xff) - Math.round(255 * amount));
        const b = Math.max(0, (num & 0xff) - Math.round(255 * amount));
        return '#' + [r, g, b].map(v => v.toString(16).padStart(2,'0')).join('');
    }

    hexToRgba(hex, alpha) {
        const num = parseInt(hex.replace('#',''), 16);
        const r = (num >> 16) & 0xff;
        const g = (num >> 8)  & 0xff;
        const b =  num        & 0xff;
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    loadAccentColor() {
        const saved = localStorage.getItem('accentColor') || '#f59e0b'; // Amber/Orange default
        this.applyAccentColor(saved);
    }

    // ── Shortcut Recorder ─────────────────────────────────────────────────

    matchesShortcut(event, shortcutStr) {
        // shortcutStr format: "ctrl+h", "ctrl+shift+h", "alt+h", etc.
        const parts = shortcutStr.toLowerCase().split('+');
        const key = parts[parts.length - 1];
        const needsCtrl  = parts.includes('ctrl');
        const needsShift = parts.includes('shift');
        const needsAlt   = parts.includes('alt');
        const eventKey   = event.key.toLowerCase();
        return (
            eventKey === key &&
            event.ctrlKey  === needsCtrl &&
            event.shiftKey === needsShift &&
            event.altKey   === needsAlt
        );
    }

    startRecording() {
        this.isRecording = true;
        this.recordShortcutBtn.classList.add('recording');
        this.recordShortcutBtn.innerHTML = '<i class="fas fa-stop"></i> Stop';
        this.shortcutDisplay.classList.add('recording');
        this.shortcutKeysLabel.textContent = 'Press any key combo...';
        this.shortcutHint.textContent = 'Press your desired combination. Esc cancels.';

        this._shortcutHandler = (e) => {
            // Esc cancels recording without saving
            if (e.key === 'Escape') {
                this.stopRecording(null);
                return;
            }
            // Ignore lone modifier keys
            if (['Control','Shift','Alt','Meta'].includes(e.key)) return;

            e.preventDefault();
            e.stopPropagation();

            const parts = [];
            if (e.ctrlKey)  parts.push('ctrl');
            if (e.shiftKey) parts.push('shift');
            if (e.altKey)   parts.push('alt');
            parts.push(e.key.toLowerCase());

            const shortcut = parts.join('+');
            this.stopRecording(shortcut);
        };

        document.addEventListener('keydown', this._shortcutHandler, { capture: true });
    }

    stopRecording(shortcut) {
        this.isRecording = false;
        this.recordShortcutBtn.classList.remove('recording');
        this.recordShortcutBtn.innerHTML = '<i class="fas fa-circle"></i> Record';
        this.shortcutDisplay.classList.remove('recording');
        document.removeEventListener('keydown', this._shortcutHandler, { capture: true });

        if (shortcut) {
            this.applyShortcut(shortcut);
        } else {
            // Cancelled - restore current
            const current = localStorage.getItem('hideShortcut') || 'ctrl+h';
            this.renderShortcutBadges(current);
            this.shortcutHint.textContent = 'Click Record, then press your desired key combination.';
        }
    }

    applyShortcut(shortcut) {
        localStorage.setItem('hideShortcut', shortcut);
        this.renderShortcutBadges(shortcut);
        this.shortcutHint.textContent = 'Shortcut saved!';
        setTimeout(() => {
            this.shortcutHint.textContent = 'Click Record, then press your desired key combination.';
        }, 2000);
        // Tell Python to re-register the global hotkey
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.set_hotkey(shortcut);
        }
    }

    resetShortcut() {
        this.applyShortcut('ctrl+h');
    }

    renderShortcutBadges(shortcut) {
        const parts = shortcut.split('+');
        const html = parts.map(p => {
            const label = p === 'ctrl' ? 'Ctrl'
                        : p === 'shift' ? 'Shift'
                        : p === 'alt' ? 'Alt'
                        : p.toUpperCase();
            return `<span class="key-badge">${label}</span>`;
        }).join('<span style="margin:0 2px;color:var(--text-muted)">+</span>');
        this.shortcutKeysLabel.innerHTML = html;
    }

    loadShortcutDisplay() {
        const shortcut = localStorage.getItem('hideShortcut') || 'ctrl+h';
        this.renderShortcutBadges(shortcut);
    }

    // ── Sidebar Toggle ─────────────────────────────────────────────────────

    // Sidebar toggle
    toggleSidebar() {
        const isCollapsed = this.sidebar.classList.toggle('collapsed');
        const icon = this.sidebarToggleBtn.querySelector('i');
        icon.className = isCollapsed ? 'fas fa-indent' : 'fas fa-bars';
        localStorage.setItem('sidebarCollapsed', isCollapsed);
    }

    loadSidebarState() {
        const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (collapsed) {
            this.sidebar.classList.add('collapsed');
            const icon = this.sidebarToggleBtn.querySelector('i');
            if (icon) icon.className = 'fas fa-indent';
        }
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
        this.loadShortcutDisplay();
        this.loadAccentColor();
    }

    closeSettings() {
        this.settingsModal.style.display = 'none';
    }

    async loadSettings() {
        try {
            const settings = await window.api.getSettings();
            
            this.themeSelect.value = this.currentTheme;
            
            const appOpacity = localStorage.getItem('appOpacity') || '100';
            this.appOpacitySlider.value = appOpacity;
            this.appOpacityValue.textContent = appOpacity + '%';
            this.updateAppOpacityDisplay(appOpacity);
            
            const disclaimerOpacity = localStorage.getItem('disclaimerOpacity') || '100';
            this.disclaimerOpacitySlider.value = disclaimerOpacity;
            this.disclaimerOpacityValue.textContent = disclaimerOpacity + '%';
            this.updateDisclaimerOpacityDisplay(disclaimerOpacity);
            
            this.temperatureSlider.value = settings.temperature;
            this.temperatureValue.textContent = settings.temperature;
            this.maxTokensInput.value = settings.max_tokens;
            this.systemPromptTextarea.value = settings.system_prompt;

            // API Keys (masked)
            if (this.openaiKeyInput) this.openaiKeyInput.value = settings.openai_api_key || '';
            if (this.geminiKeyInput) this.geminiKeyInput.value = settings.gemini_api_key || '';
            if (this.claudeKeyInput) this.claudeKeyInput.value = settings.claude_api_key || '';
            
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

            // Add API keys if they exist and aren't masked
            if (this.openaiKeyInput?.value && !this.openaiKeyInput.value.includes('••')) {
                settings.openai_api_key = this.openaiKeyInput.value;
            }
            if (this.geminiKeyInput?.value && !this.geminiKeyInput.value.includes('••')) {
                settings.gemini_api_key = this.geminiKeyInput.value;
            }
            if (this.claudeKeyInput?.value && !this.claudeKeyInput.value.includes('••')) {
                settings.claude_api_key = this.claudeKeyInput.value;
            }
            
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

    updateAppOpacity() {
        const opacity = this.appOpacitySlider.value;
        this.appOpacityValue.textContent = opacity + '%';
        this.updateAppOpacityDisplay(opacity);
        localStorage.setItem('appOpacity', opacity);
    }

    updateAppOpacityDisplay(opacity) {
        if (this.app) {
            const opacityValue = opacity / 100;
            this.app.style.opacity = opacityValue;
        }
    }

    updateDisclaimerOpacity() {
        const opacity = this.disclaimerOpacitySlider.value;
        this.disclaimerOpacityValue.textContent = opacity + '%';
        this.updateDisclaimerOpacityDisplay(opacity);
        localStorage.setItem('disclaimerOpacity', opacity);
    }

    updateDisclaimerOpacityDisplay(opacity) {
        if (this.sidebarDisclaimer) {
            const opacityValue = opacity / 100;
            this.sidebarDisclaimer.style.opacity = opacityValue;
        }
    }

    goHome() {
        // Hide chat interface, show welcome screen
        const chatInterface = document.getElementById('chat-interface');
        const welcomeScreen = document.getElementById('welcome-screen');
        
        if (chatInterface) chatInterface.style.display = 'none';
        if (welcomeScreen) welcomeScreen.style.display = 'flex';
        
        // Reset current conversation
        this.currentConversationId = null;
        
        // Update page title
        document.title = 'Durgara';
    }

    // Zoom functionality
    adjustZoom(change) {        const current = parseInt(localStorage.getItem('zoomLevel') || '100');
        let newZoom = current + change;
        
        // Limit zoom between 50% and 150%
        newZoom = Math.max(50, Math.min(150, newZoom));
        
        localStorage.setItem('zoomLevel', newZoom);
        this.applyZoom(newZoom);
    }

    applyZoom(level) {
        const zoomDecimal = level / 100;
        document.body.style.zoom = zoomDecimal;
        if (this.zoomLevel) {
            this.zoomLevel.textContent = level + '%';
        }
    }

    loadZoom() {
        const saved = localStorage.getItem('zoomLevel') || '100';
        this.applyZoom(parseInt(saved));
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
        const savedTheme = localStorage.getItem('theme') || 'dark';
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

    // Screenshot functionality
    async takeScreenshot() {
        try {
            if (!window.pywebview || !window.pywebview.api) {
                this.showToast('Screenshot feature requires desktop app', 'error');
                return;
            }

            // Call Python API to take screenshot
            // Window will hide briefly, capture background, then show again
            const result = await window.pywebview.api.take_screenshot();
            
            if (result && result.success) {
                // Show success with path and Open Folder button
                this.showScreenshotToast(result.path, result.folder);
            } else {
                const errorMsg = result?.error || 'Unknown error';
                this.showToast(`Screenshot failed: ${errorMsg}`, 'error');
            }
        } catch (error) {
            console.error('Screenshot error:', error);
            this.showToast('Failed to take screenshot', 'error');
        }
    }

    showScreenshotToast(filepath, folder) {
        const toast = document.createElement('div');
        toast.className = 'toast success';
        
        // Extract filename from path
        const filename = filepath.split('\\').pop();
        
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-message">
                    <strong>📸 Screenshot saved & copied!</strong><br>
                    <small style="opacity: 0.8;">${filename}</small><br>
                    <small style="opacity: 0.7; margin-top: 4px; display: block;">💡 Paste in chat (Ctrl+V) to analyze image with AI</small><br>
                    <button class="open-folder-btn" style="margin-top: 8px; padding: 4px 12px; background: var(--primary-color); border: none; border-radius: 4px; color: white; cursor: pointer; font-size: 12px;">
                        📁 Open Folder
                    </button>
                </div>
            </div>
            <button class="toast-close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.removeToast(toast));
        
        const openFolderBtn = toast.querySelector('.open-folder-btn');
        openFolderBtn.addEventListener('click', () => {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.open_folder(folder);
            }
            this.removeToast(toast);
        });
        
        this.toastContainer.appendChild(toast);
        
        // Auto-remove after 10 seconds (extra time to read the hint)
        setTimeout(() => this.removeToast(toast), 10000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

// Export for global access
window.App = App;
