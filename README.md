# Local AI Assistant

A privacy-focused offline AI chat application for Windows that runs entirely on your computer using local LLMs via Ollama. No internet required for AI conversations, no data sent to cloud providers.

![Local AI Assistant](https://img.shields.io/badge/Platform-Windows-blue) ![Python](https://img.shields.io/badge/Python-3.10+-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **🔒 100% Private** - All conversations stay on your computer
- **🌐 Offline Capable** - Works without internet after setup
- **⚡ Fast & Local** - No API delays, instant responses
- **💬 Modern Chat UI** - Clean, responsive interface with dark/light themes
- **📚 Conversation History** - Search and manage your chat history
- **🔧 Configurable** - Adjust AI settings, system prompts, and models
- **🛡️ Safe Architecture** - Prepared for future local file and automation tools
- **📱 Responsive Design** - Works on different screen sizes

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI        │    │   Local LLM     │
│   HTML/CSS/JS   │◄──►│   Backend        │◄──►│   (Ollama)      │
│                 │    │   + SQLite       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

- **Frontend**: Modern web interface with vanilla HTML/CSS/JavaScript
- **Backend**: FastAPI with SQLite database for conversation storage
- **AI Engine**: Ollama running local models (default: Qwen 2.5 3B)
- **Database**: SQLite for conversations, messages, and settings
- **No Cloud Dependencies**: Everything runs locally

## Quick Start

### Prerequisites

1. **Python 3.10+** - [Download from python.org](https://www.python.org/downloads/)
   - ⚠️ **Important**: Check "Add Python to PATH" during installation
2. **Ollama** - [Download from ollama.com](https://ollama.com/download)
3. **Windows 10/11** (64-bit)
4. **10-15 GB free storage** (for application + AI model)

### Installation

1. **Download or Clone** this repository:
   ```cmd
   git clone <repository-url>
   cd local-ai-agent
   ```

2. **Run Setup**:
   ```cmd
   setup.bat
   ```
   This will:
   - Create Python virtual environment
   - Install all dependencies
   - Initialize the database
   - Check Ollama installation

3. **Install AI Model**:
   ```cmd
   ollama pull qwen2.5:3b
   ```
   *Note: This downloads ~2GB and may take several minutes*

4. **Start Ollama Service**:
   ```cmd
   ollama serve
   ```
   *Keep this terminal open*

5. **Start the Application**:
   ```cmd
   start.bat
   ```
   *The app will open automatically in your browser*

### Usage

1. Open your browser to `http://127.0.0.1:8000`
2. Click "Start Chatting" or "New Chat"
3. Type your message and press Enter
4. Watch the AI response stream in real-time

To stop the application, use `stop.bat` or press `Ctrl+C` in the terminal.

## Configuration

### Environment Settings

Edit `.env` to customize settings:

```env
# Ollama Configuration
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b

# Server Settings
HOST=127.0.0.1
PORT=8000

# AI Settings (can also be changed in UI)
TEMPERATURE=0.7
MAX_TOKENS=2048
```

### Available Models

The application works with any Ollama-compatible model. Popular options:

- **qwen2.5:3b** (default) - Good balance of speed and quality (~2GB)
- **llama3.2:3b** - Meta's latest small model (~2GB)
- **phi3:mini** - Microsoft's compact model (~2GB)
- **llama3.1:8b** - Larger, higher quality (~4.7GB)

To switch models:
1. Pull the model: `ollama pull <model-name>`
2. Change it in the Settings panel or update `OLLAMA_MODEL` in `.env`

### System Prompt

Customize the AI's behavior by editing the system prompt in Settings:

```
You are a helpful local AI assistant running on the user's computer. 
You do not have internet access unless the user explicitly enables an external feature. 
Be honest about your capabilities. Give clear, useful and accurate answers. 
Never claim to have accessed information that you did not access.
```

## Project Structure

```
local-ai-agent/
├── backend/               # FastAPI backend
│   ├── routes/           # API endpoints
│   ├── services/         # Business logic
│   ├── models/           # Database models
│   ├── utils/            # Utilities
│   └── tools/            # Future agent tools
├── frontend/             # Web interface
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript
├── data/                # SQLite database
├── logs/                # Application logs
├── tests/               # Automated tests
├── setup.bat            # Installation script
├── start.bat            # Start application
└── stop.bat             # Stop application
```

## API Documentation

When the application is running, visit:
- **Interactive API Docs**: `http://127.0.0.1:8000/docs`
- **Health Check**: `http://127.0.0.1:8000/api/health`
- **System Status**: `http://127.0.0.1:8000/api/status`

### Key Endpoints

- `GET /api/conversations` - List conversations
- `POST /api/conversations` - Create new conversation
- `POST /api/chat` - Send message (supports streaming)
- `GET /api/models` - List available models
- `GET /api/settings` - Get/update settings

## Development

### Running Tests

```cmd
# Install test dependencies (done by setup.bat)
.venv\Scripts\pip install pytest pytest-asyncio

# Run all tests
.venv\Scripts\python -m pytest tests/ -v

# Run specific test file
.venv\Scripts\python -m pytest tests/test_chat.py -v
```

### Manual Testing

1. **Backend Only**:
   ```cmd
   .venv\Scripts\python -m uvicorn backend.main:app --reload
   ```

2. **Database Operations**:
   ```cmd
   .venv\Scripts\python -c "from backend.models.init_db import initialize_database; initialize_database()"
   ```

### Code Quality

The codebase follows these practices:
- Type hints throughout Python code
- Comprehensive error handling
- Input validation and sanitization
- Modular, testable architecture
- Clear separation of concerns

## Troubleshooting

### Common Issues

**"Ollama service unavailable"**
- Solution: Make sure Ollama is running with `ollama serve`
- Check the service at `http://127.0.0.1:11434/api/tags`

**"Model not found"**
- Solution: Install the model with `ollama pull qwen2.5:3b`
- Check installed models with `ollama list`

**"Python not found"**
- Solution: Install Python 3.10+ and add it to PATH
- Restart terminal after installation

**"Permission denied" errors**
- Solution: Run setup as Administrator if needed
- Check antivirus software isn't blocking files

**Port already in use**
- Solution: Change PORT in `.env` or stop other services using port 8000
- Use `netstat -ano | findstr :8000` to find conflicting processes

### Performance Tips

1. **Choose the right model size** for your hardware:
   - 4GB RAM: phi3:mini or qwen2.5:3b
   - 8GB RAM: llama3.1:8b or qwen2.5:7b
   - 16GB+ RAM: llama3.1:70b or larger models

2. **Adjust temperature** in Settings:
   - Lower (0.1-0.4): More consistent, factual responses
   - Higher (0.7-1.0): More creative, varied responses

3. **Manage conversation length**:
   - Long conversations use more memory
   - Start new conversations for different topics

### Logs and Debugging

- **Application logs**: `logs/app.log`
- **Browser console**: F12 → Console tab for frontend issues
- **Ollama logs**: Check terminal where `ollama serve` is running

## Security Considerations

### Current Security Posture

✅ **Secure by Design**:
- No cloud API dependencies
- Local-only data storage
- Input validation and sanitization
- No arbitrary code execution from AI responses

⚠️ **Planned Features** (not yet implemented):
- Future versions will add local file access tools
- Command execution capabilities will require explicit user approval
- Tool registry with permission levels already implemented

### Privacy

- **No telemetry**: Application doesn't phone home
- **No analytics**: No usage tracking or data collection  
- **Local storage**: All conversations stored in local SQLite database
- **No cloud sync**: Data never leaves your computer

### Network Access

The application only makes network requests to:
- `127.0.0.1:11434` (local Ollama service)
- No external URLs or cloud services

## Future Roadmap

### Phase 1: Current ✅
- Local chat interface
- Conversation management
- Model selection
- Basic settings

### Phase 2: Planned 🚧
- Local file reading/writing tools
- PDF and document analysis  
- Advanced conversation search
- Voice input/output

### Phase 3: Future 🔮
- Safe command execution tools
- Local automation workflows
- n8n integration
- Advanced agent capabilities

## Contributing

### Architecture Principles

1. **Privacy First**: No cloud dependencies for core functionality
2. **Safety First**: Tools require explicit permission and validation
3. **Local First**: Everything works offline after initial setup
4. **Extensible**: Clean architecture for adding future capabilities

### Development Setup

1. Fork the repository
2. Run `setup.bat` to install dependencies  
3. Make your changes
4. Run tests with `pytest tests/ -v`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- **Ollama** - For excellent local LLM runtime
- **FastAPI** - For the robust Python web framework
- **Qwen Team** - For the excellent default model

## Support

- **Documentation**: This README and `/docs` endpoint
- **Issues**: Use GitHub Issues for bug reports
- **Discussions**: Use GitHub Discussions for questions

---

**Built with ❤️ for privacy-conscious AI users**