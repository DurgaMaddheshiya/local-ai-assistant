# Distribution Guide - Local AI Assistant

## Quick Summary for Users

### What Users Need to Do

**BEFORE Installing Your App:**
```
1. Download Ollama from https://ollama.com/download
2. Install it (next-next-finish)
3. Open Command Prompt and run:
   ollama pull qwen2.5:3b
   (Wait for completion - this is 2GB download)
4. Run: ollama serve
   (Keep this terminal open)
```

**THEN Install Your App:**
```
1. Download LocalAIAssistant-Setup.exe
2. Double-click it
3. Click Install
4. Done! Desktop shortcut appears automatically
```

**Launch:**
```
Double-click "Local AI Assistant" on Desktop
```

---

## Distribution Channels

### ✅ Method 1: GitHub Releases (FREE)
1. Create GitHub account (if not already)
2. Create new repository "local-ai-assistant"
3. Push your code
4. Create Release
5. Upload `LocalAIAssistant-Setup.exe`
6. Share link: `https://github.com/yourusername/local-ai-assistant/releases`

### ✅ Method 2: Direct Download Link
1. Upload to Google Drive / OneDrive / Dropbox
2. Share link publicly
3. Users download and run

### ✅ Method 3: Website
1. Create simple website
2. Add download button
3. Users download `.exe`

### ✅ Method 4: Email/Sharing
1. Send `LocalAIAssistant-Setup.exe` to users
2. They run it

---

## User Instructions Template

Share this with users:

```
👋 WELCOME TO LOCAL AI ASSISTANT

⚡ Quick Start:

1. Install Ollama (the AI engine):
   📥 https://ollama.com/download
   
2. Setup AI Model (run in Command Prompt):
   > ollama pull qwen2.5:3b
   (Wait for completion)
   
3. Start Ollama service (keep running):
   > ollama serve
   
4. Install Local AI Assistant:
   📥 [Download Link Here]
   
5. Run LocalAIAssistant-Setup.exe
   Click Install → Done!
   
6. Launch from Desktop shortcut
   Browser opens automatically
   
✅ You're all set! Start chatting!

---

📋 Requirements:
- Windows 10/11 (64-bit)
- 10GB free space
- 4GB RAM minimum

❓ Questions:
- If Ollama won't start: Install from ollama.com
- If application won't start: Check port 8000
- Slow first response: Normal, model optimizing

🎉 Enjoy your private AI assistant!
```

---

## Technical Details

### What's in the Installer
```
LocalAIAssistant-Setup.exe (250MB)
├── Python 3.10 (bundled)
├── FastAPI + dependencies
├── SQLite database
├── Web frontend
└── Startup scripts
```

### User System After Installation
```
C:\Program Files\LocalAIAssistant\
├── Application files
├── Python runtime
├── Database
└── Configuration
```

```
C:\Users\[Username]\AppData\Local\LocalAIAssistant\
└── User data (optional)
```

### Environment Variables (Optional)
Users can create `.env` in installation folder to customize:
```
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
TEMPERATURE=0.7
MAX_TOKENS=2048
```

---

## Updating Your Application

### For New Versions:

1. Update code in your repo
2. Run `build_installer.bat`
3. Generates new `LocalAIAssistant-Setup.exe`
4. Upload to distribution channel
5. Users download and install new version

### Version Management:
- Update version in `backend/config.py`
- Increment installer version in `installer.nsi`
- Tag releases: `v1.0.0`, `v1.1.0`, etc.

---

## Uninstallation

Users can uninstall via:
1. **Start Menu** → Local AI Assistant → Uninstall
2. **Control Panel** → Programs → Uninstall a Program
3. Or delete `C:\Program Files\LocalAIAssistant\`

---

## Support

### Common Issues

**"Ollama service unavailable"**
- Ensure `ollama serve` is running in Command Prompt

**"Model not found"**
- Run `ollama pull qwen2.5:3b`

**"Port 8000 already in use"**
- Close other applications using port 8000
- Or change PORT in .env

**"Application starts but no response"**
- Check Ollama is running: `curl http://127.0.0.1:11434/api/tags`

---

## Marketing/Sharing Tips

### Social Media Post Template
```
🤖 Just released: Local AI Assistant!

✨ Your private ChatGPT running locally on Windows
🔒 100% private - no data sent to cloud
⚡ Works offline after setup
🎯 Simple one-click installation

🔗 Download now: [link]

No cloud account needed. No subscriptions. Just you and your AI.

#AI #LocalAI #OpenSource #Windows #Privacy
```

### Website Description
```
Local AI Assistant - Private AI Chat for Windows

Run ChatGPT-like experience on your own computer.
- 100% offline and private
- One-click installation
- No subscriptions or cloud accounts
- Full conversation history

Download now and start chatting!
```

---

## Analytics (Optional)

Track downloads by:
1. Using GitHub Releases (has download counter)
2. Using bit.ly shortened links
3. Asking users to report success
4. Checking website analytics

---

**Ready to distribute! 🚀**

Questions? Check INSTALL_GUIDE.md for technical details.
