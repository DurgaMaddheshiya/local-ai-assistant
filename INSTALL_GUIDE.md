# Local AI Assistant - Installation Guide

## For End Users

### Quick Start (3 Steps)

#### Step 1: Install Ollama (Required)
1. Download Ollama: https://ollama.com/download
2. Run the installer (next-next-finish)
3. Open Command Prompt and run:
   ```cmd
   ollama pull qwen2.5:3b
   ```
   This downloads the AI model (~2GB, takes 5-15 minutes)

4. Start Ollama service:
   ```cmd
   ollama serve
   ```
   Keep this terminal open while using the application.

#### Step 2: Install Local AI Assistant
1. Download `LocalAIAssistant-Setup.exe`
2. Double-click to run
3. Click "Install" and wait (2-3 minutes)
4. Application will install automatically

#### Step 3: Launch Application
1. Double-click "Local AI Assistant" from Desktop
2. Browser opens automatically
3. Click "Start Chatting"
4. Done! 🎉

### System Requirements
- **Windows 10/11** (64-bit)
- **10GB free disk space** (for application + AI model)
- **4GB RAM minimum** (8GB recommended)
- **Active internet** (only for first-time setup)

### Troubleshooting

**Q: "Ollama service unavailable"**
- A: Make sure you have `ollama serve` running in a terminal

**Q: "Model not found"**
- A: Run `ollama pull qwen2.5:3b` in Command Prompt

**Q: Application won't start**
- A: Check if port 8000 is already in use. Close other applications or change port in settings.

**Q: Slow responses**
- A: Normal for first load. Model optimizes on first use. Subsequent responses are faster.

---

## For Developers

### Building the Installer

#### Prerequisites
1. Python 3.10+
2. NSIS (Nullsoft Scriptable Install System)
   - Download: https://nsis.sourceforge.io/Main_Page
   - Install normally

#### Build Steps

1. **Clone/Download** the project:
   ```cmd
   cd c:\local-ai-agent
   ```

2. **Run setup**:
   ```cmd
   setup.bat
   ```

3. **Build installer**:
   ```cmd
   build_installer.bat
   ```

   This will:
   - Install PyInstaller
   - Bundle Python + all dependencies
   - Create executable
   - Package with NSIS
   - Generate `LocalAIAssistant-Setup.exe`

4. **Distribute**:
   - Share `LocalAIAssistant-Setup.exe`
   - Users simply run it
   - Everything installs automatically

#### Build Output
- `dist/LocalAIAssistant/` - Portable executable folder
- `LocalAIAssistant-Setup.exe` - Installer (ready to distribute)

### What's Bundled in the Installer
✅ Python 3.10
✅ FastAPI + all dependencies
✅ SQLite database
✅ Frontend (HTML/CSS/JS)
✅ All configuration files

❌ Ollama (users install separately - it's the LLM engine)

### Customization

#### Change Application Name
Edit `installer.nsi`:
```nsi
Name "Your App Name"
OutFile "YourAppName-Setup.exe"
```

#### Change Installation Directory
Edit `installer.nsi`:
```nsi
InstallDir "$PROGRAMFILES\YourAppName"
```

#### Add Custom Icon
1. Create 256x256 .ico file
2. Place as `installer_icon.ico`
3. Rebuild

#### Change System Prompt or Settings
Edit `backend/config.py` or `.env.example` before building.

### Publishing

1. **Create GitHub Release**:
   ```cmd
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Upload Installer**:
   - Go to GitHub Releases
   - Upload `LocalAIAssistant-Setup.exe`
   - Add description and instructions

3. **Share Link**:
   - Users download and run
   - No additional setup needed

### File Structure (After Installation)
```
C:\Program Files\LocalAIAssistant\
├── LocalAIAssistant.exe       (main application)
├── frontend/                   (web interface)
├── _internal/                  (Python + dependencies)
├── data/                       (SQLite database)
├── logs/                       (application logs)
└── .env                        (configuration)
```

### Performance Notes

**Build Time**: 3-5 minutes
**Installer Size**: ~200-250MB (includes Python + all dependencies)
**Installation Time**: 2-3 minutes (depends on disk speed)

### Support

- **Users**: See "Troubleshooting" above
- **Developers**: Check GitHub Issues
- **Ollama Help**: https://github.com/ollama/ollama

---

**Built with ❤️ for easy distribution**
