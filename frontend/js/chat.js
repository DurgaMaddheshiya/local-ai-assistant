/**
 * Chat functionality for Local AI Assistant
 */

class ChatManager {
    constructor() {
        this.currentConversationId = null;
        this.isGenerating = false;
        this.currentStreamReader = null;
        
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        // Chat elements
        this.chatInterface = document.getElementById('chat-interface');
        this.welcomeScreen = document.getElementById('welcome-screen');
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.conversationTitle = document.getElementById('current-conversation-title');
        
        // Control elements
        this.modelSelect = document.getElementById('model-select');
        this.clearConversationBtn = document.getElementById('clear-conversation');
        this.editTitleBtn = document.getElementById('edit-title-btn');
    }

    bindEvents() {
        // Message input events
        this.messageInput.addEventListener('input', () => this.handleInputChange());
        this.messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Button events
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.stopBtn.addEventListener('click', () => this.stopGeneration());
        this.clearConversationBtn.addEventListener('click', () => this.clearConversation());
        this.editTitleBtn.addEventListener('click', () => this.editConversationTitle());
        
        // Model selection
        this.modelSelect.addEventListener('change', () => this.handleModelChange());
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.resizeTextarea());
    }

    handleInputChange() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendBtn.disabled = !hasText || this.isGenerating;
    }

    handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            if (!this.sendBtn.disabled) {
                this.sendMessage();
            }
        }
    }

    resizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 200) + 'px';
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isGenerating) return;

        try {
            this.setGenerating(true);
            this.clearInput();
            
            // Show user message
            this.addMessage('user', message);
            
            // Show typing indicator
            const typingId = this.addTypingIndicator();
            
            // Send streaming request
            const response = await window.api.sendStreamingMessage(
                message, 
                this.currentConversationId,
                {
                    model: this.modelSelect.value || null,
                    temperature: parseFloat(localStorage.getItem('temperature') || '0.7'),
                    max_tokens: parseInt(localStorage.getItem('max_tokens') || '2048')
                }
            );

            // Handle streaming response
            await this.handleStreamingResponse(response, typingId);

        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator();
            this.showError('Failed to send message: ' + error.toString());
        } finally {
            this.setGenerating(false);
        }
    }

    async handleStreamingResponse(response, typingId) {
        const streamReader = new StreamReader(response);
        this.currentStreamReader = streamReader;
        
        let assistantMessage = '';
        let messageElement = null;

        try {
            for await (const chunk of streamReader.readChunks()) {
                if (chunk.error) {
                    throw new Error(chunk.error);
                }

                if (chunk.content) {
                    assistantMessage += chunk.content;
                    
                    // Create or update message element
                    if (!messageElement) {
                        this.removeTypingIndicator(typingId);
                        messageElement = this.addMessage('assistant', assistantMessage);
                    } else {
                        this.updateMessageContent(messageElement, assistantMessage);
                    }
                }

                if (chunk.done) {
                    // Update conversation ID if this was a new conversation
                    if (chunk.conversation_id && !this.currentConversationId) {
                        this.currentConversationId = chunk.conversation_id;
                        this.updateConversationTitle();
                        window.app.loadConversations(); // Refresh sidebar
                    }
                    break;
                }
            }
        } catch (error) {
            this.removeTypingIndicator(typingId);
            throw error;
        }
    }

    addMessage(role, content, messageId = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.dataset.messageId = messageId || Date.now().toString();
        messageDiv.dataset.rawContent = content;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';

        if (role === 'assistant') {
            textDiv.innerHTML = this.formatMessage(content);
        } else {
            textDiv.textContent = content;
        }

        contentDiv.appendChild(textDiv);

        // User messages: edit button + inline edit area
        if (role === 'user') {
            const editBtn = document.createElement('button');
            editBtn.className = 'edit-message-btn';
            editBtn.innerHTML = '<i class="fas fa-pencil-alt"></i> Edit';
            editBtn.title = 'Edit message';
            editBtn.addEventListener('click', () => this.startEditMessage(messageDiv));
            contentDiv.appendChild(editBtn);

            const editArea = document.createElement('div');
            editArea.className = 'message-edit-area';
            editArea.innerHTML = `
                <textarea class="message-edit-textarea"></textarea>
                <div class="message-edit-actions">
                    <button class="edit-cancel-btn">Cancel</button>
                    <button class="edit-save-btn"><i class="fas fa-paper-plane"></i> Send</button>
                </div>`;
            editArea.querySelector('.edit-cancel-btn').addEventListener('click', () => this.cancelEditMessage(messageDiv));
            editArea.querySelector('.edit-save-btn').addEventListener('click', () => this.saveEditMessage(messageDiv));
            contentDiv.appendChild(editArea);
        }

        // Assistant messages: action bar
        if (role === 'assistant') {
            const actionsDiv = this.createMessageActions(content);
            contentDiv.appendChild(actionsDiv);
        }

        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        return messageDiv;
    }

    startEditMessage(messageDiv) {
        const textDiv = messageDiv.querySelector('.message-text');
        const editArea = messageDiv.querySelector('.message-edit-area');
        const textarea = editArea.querySelector('.message-edit-textarea');
        textarea.value = messageDiv.dataset.rawContent;
        textDiv.style.display = 'none';
        editArea.classList.add('active');
        textarea.focus();
        textarea.selectionStart = textarea.value.length;
    }

    cancelEditMessage(messageDiv) {
        const textDiv = messageDiv.querySelector('.message-text');
        const editArea = messageDiv.querySelector('.message-edit-area');
        textDiv.style.display = '';
        editArea.classList.remove('active');
    }

    async saveEditMessage(messageDiv) {
        const editArea = messageDiv.querySelector('.message-edit-area');
        const textarea = editArea.querySelector('.message-edit-textarea');
        const newContent = textarea.value.trim();
        if (!newContent) return;

        // Update display
        messageDiv.dataset.rawContent = newContent;
        messageDiv.querySelector('.message-text').textContent = newContent;
        this.cancelEditMessage(messageDiv);

        // Remove all messages after this one
        let next = messageDiv.nextElementSibling;
        while (next) {
            const toRemove = next;
            next = next.nextElementSibling;
            toRemove.remove();
        }

        // Re-send the edited message
        if (!this.isGenerating) {
            try {
                this.setGenerating(true);
                const typingId = this.addTypingIndicator();
                const response = await window.api.sendStreamingMessage(
                    newContent,
                    this.currentConversationId,
                    {
                        model: this.modelSelect.value || null,
                        temperature: parseFloat(localStorage.getItem('temperature') || '0.7'),
                        max_tokens: parseInt(localStorage.getItem('max_tokens') || '2048')
                    }
                );
                await this.handleStreamingResponse(response, typingId);
            } catch (error) {
                this.showError('Failed to send edited message: ' + error.toString());
            } finally {
                this.setGenerating(false);
            }
        }
    }

    updateMessageContent(messageElement, content) {
        const textDiv = messageElement.querySelector('.message-text');
        textDiv.innerHTML = this.formatMessage(content);
        this.scrollToBottom();
    }

    formatMessage(text) {
        // Basic markdown-style formatting
        let formatted = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');

        // Handle code blocks - wrap in .code-block-wrapper with copy button
        formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            const escaped = code.trim()
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            return `<div class="code-block-wrapper">
                <button class="copy-code-btn" onclick="window.chatManager.copyCodeBlock(this)">
                    <i class="fas fa-copy"></i> Copy
                </button>
                <pre><code class="${lang || ''}">${escaped}</code></pre>
            </div>`;
        });

        return formatted;
    }

    copyCodeBlock(btn) {
        const code = btn.closest('.code-block-wrapper').querySelector('code').innerText;
        navigator.clipboard.writeText(code).then(() => {
            btn.innerHTML = '<i class="fas fa-check"></i> Copied';
            btn.classList.add('copied');
            setTimeout(() => {
                btn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                btn.classList.remove('copied');
            }, 2000);
        }).catch(() => {
            window.app.showToast('Failed to copy code', 'error');
        });
    }

    createMessageActions(content) {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';

        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-action';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
        copyBtn.title = 'Copy message';
        copyBtn.addEventListener('click', () => this.copyMessage(content));

        actionsDiv.appendChild(copyBtn);
        return actionsDiv;
    }

    addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
            <span>AI is thinking...</span>
        `;

        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
        
        return typingDiv;
    }

    removeTypingIndicator(typingElement = null) {
        if (typingElement && typingElement.parentNode) {
            typingElement.remove();
        } else {
            const existing = this.chatMessages.querySelector('.typing-indicator');
            if (existing) existing.remove();
        }
    }

    async stopGeneration() {
        if (this.currentStreamReader) {
            try {
                await window.api.stopGeneration(this.currentConversationId);
            } catch (error) {
                console.warn('Error stopping generation:', error);
            }
            this.currentStreamReader = null;
        }
        
        this.removeTypingIndicator();
        this.setGenerating(false);
    }

    setGenerating(isGenerating) {
        this.isGenerating = isGenerating;
        this.sendBtn.style.display = isGenerating ? 'none' : 'flex';
        this.stopBtn.style.display = isGenerating ? 'flex' : 'none';
        this.sendBtn.disabled = isGenerating || !this.messageInput.value.trim();
        this.messageInput.disabled = isGenerating;
    }

    clearInput() {
        this.messageInput.value = '';
        this.resizeTextarea();
        this.handleInputChange();
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    async copyMessage(content) {
        try {
            await navigator.clipboard.writeText(content);
            window.app.showToast('Message copied to clipboard', 'success');
        } catch (error) {
            console.error('Failed to copy:', error);
            window.app.showToast('Failed to copy message', 'error');
        }
    }

    async startNewChat() {
        this.currentConversationId = null;
        this.clearMessages();
        this.showChatInterface();
        this.updateConversationTitle('New Conversation');
        this.messageInput.focus();
    }

    async loadConversation(conversationId) {
        try {
            this.clearMessages();
            this.showChatInterface();
            
            const conversation = await window.api.getConversation(conversationId);
            this.currentConversationId = conversationId;
            this.updateConversationTitle(conversation.title);
            
            // Load messages
            for (const message of conversation.messages) {
                if (message.role !== 'system') {
                    this.addMessage(message.role, message.content, message.id);
                }
            }
            
            this.scrollToBottom();
            this.messageInput.focus();
            
        } catch (error) {
            console.error('Error loading conversation:', error);
            window.app.showToast('Failed to load conversation', 'error');
        }
    }

    clearMessages() {
        this.chatMessages.innerHTML = '';
    }

    showWelcomeScreen() {
        this.welcomeScreen.style.display = 'flex';
        this.chatInterface.style.display = 'none';
    }

    showChatInterface() {
        this.welcomeScreen.style.display = 'none';
        this.chatInterface.style.display = 'flex';
    }

    updateConversationTitle(title = null) {
        if (title) {
            this.conversationTitle.textContent = title;
        } else if (this.currentConversationId) {
            // Auto-generate title from first message if available
            const firstUserMessage = this.chatMessages.querySelector('.message.user .message-text');
            if (firstUserMessage) {
                const text = firstUserMessage.textContent.trim();
                const autoTitle = this.generateTitle(text);
                this.conversationTitle.textContent = autoTitle;
            }
        }
    }

    generateTitle(message) {
        if (!message) return 'New Conversation';
        
        // Clean and shorten message for title
        let title = message.replace(/^\s*(please|can you|could you|help me|i want to|i need to)\s*/i, '');
        title = title.charAt(0).toUpperCase() + title.slice(1);
        
        if (title.length > 50) {
            title = title.substring(0, 47) + '...';
        }
        
        return title || 'New Conversation';
    }

    async editConversationTitle() {
        if (!this.currentConversationId) return;

        const currentTitle = this.conversationTitle.textContent;
        const newTitle = prompt('Enter new conversation title:', currentTitle);
        
        if (newTitle && newTitle !== currentTitle) {
            try {
                await window.api.updateConversation(this.currentConversationId, { title: newTitle });
                this.updateConversationTitle(newTitle);
                window.app.loadConversations(); // Refresh sidebar
                window.app.showToast('Conversation title updated', 'success');
            } catch (error) {
                console.error('Error updating title:', error);
                window.app.showToast('Failed to update title', 'error');
            }
        }
    }

    async clearConversation() {
        if (!this.currentConversationId) return;

        const confirmed = confirm('Delete this conversation? This cannot be undone.');
        if (confirmed) {
            try {
                await window.api.deleteConversation(this.currentConversationId);
                this.currentConversationId = null;
                this.showWelcomeScreen();
                window.app.loadConversations(); // Refresh sidebar
                window.app.showToast('Conversation deleted', 'success');
            } catch (error) {
                console.error('Error deleting conversation:', error);
                window.app.showToast('Failed to delete conversation', 'error');
            }
        }
    }

    async loadModels() {
        try {
            const response = await window.api.getModels();
            const currentModel = await window.api.getCurrentModel();
            
            this.modelSelect.innerHTML = '';
            
            if (response.models && response.models.length > 0) {
                for (const model of response.models) {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = `${model.name} (${model.size || 'Unknown size'})`;
                    
                    if (model.name === currentModel.current_model) {
                        option.selected = true;
                    }
                    
                    this.modelSelect.appendChild(option);
                }
            } else {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No models available';
                this.modelSelect.appendChild(option);
            }
        } catch (error) {
            console.error('Error loading models:', error);
            this.modelSelect.innerHTML = '<option value="">Error loading models</option>';
        }
    }

    async handleModelChange() {
        if (!this.modelSelect.value) return;

        try {
            await window.api.selectModel(this.modelSelect.value);
            window.app.showToast(`Switched to model: ${this.modelSelect.value}`, 'success');
        } catch (error) {
            console.error('Error changing model:', error);
            window.app.showToast('Failed to change model', 'error');
            this.loadModels(); // Reload to reset selection
        }
    }

    showError(message) {
        window.app.showToast(message, 'error');
    }
}

// Export chat manager
window.ChatManager = ChatManager;
window.chatManager = null; // set by app.js after init