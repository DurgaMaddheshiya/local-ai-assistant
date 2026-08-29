# 🚀 Local AI Assistant - Complete User Setup Guide

**Built by [@durga.kr2003](https://instagram.com/durga.kr2003) on Instagram**

---

## 📋 Table of Contents
1. [What You Need](#what-you-need)
2. [Step-by-Step Installation](#step-by-step-installation)
3. [Running the Application](#running-the-application)
4. [First Time Setup](#first-time-setup)
5. [Troubleshooting](#troubleshooting)
6. [Tips & Tricks](#tips--tricks)

---

## What You Need

### System Requirements
- **Windows 10 or 11** (64-bit)
- **4GB RAM minimum** (8GB recommended for best performance)
- **10GB free storage** (for application + AI model)
- **Internet connection** (only for first-time setup)

### Free Software to Install
- **Ollama** - The AI engine (must have)
- **Local AI Assistant** - The application (we provide)

That's it! No subscriptions, no accounts, no cloud services needed.

---

## Step-by-Step Installation

### **STEP 1: Download & Install Ollama (5 minutes)**

Ollama is the AI engine that powers everything. It's completely free and open-source.

#### Download Ollama
1. Open your browser
2. Go to: **https://ollama.com/download**
3. Click **"Download for Windows"**
4. File `OllamaSetup.exe` will download (~150MB)

#### Install Ollama
1. Find the downloaded file in your Downloads folder
2. Double-click `OllamaSetup.exe`
3. Follow the installer (just click Next → Next → Finish)
4. Wait for installation to complete (~2-3 minutes)
5. Once done, close the installer

✅ **Ollama is now installed!**

---

### **STEP 2: Download AI Model (15-20 minutes)**

The AI model is what makes Ollama intelligent. We use Qwen 2.5 (3B) - it's small, fast, and smart.

#### Download the Model

1. **Open Command Prompt** (search for "cmd" in Start menu)
2. Copy this command and paste it:
   ```cmd
   ollama pull qwen2.5:3b
   ```
3. **Press Enter** and wait
   - File size: ~2GB
   - Download time: 5-15 minutes (depends on internet speed)
   - You'll see a progress bar

4. When done, you'll see:
   ```
   pulling manifest
   pulling layers
   100% complete ✓
   ```

✅ **AI Model is ready!**

---

### **STEP 3: Start Ollama Service (2 minutes)**

The Ollama service needs to run in the background while you use the application.

#### Start Ollama Service

1. **Open Command Prompt** (search for "cmd" in Start menu)
2. Type this command:
   ```cmd
   ollama serve
   ```
3. **Press Enter**
4. You'll see output like:
   ```
   Listening on 127.0.0.1:11434 (version 0.33.2)
   ```

⚠️ **Important**: Keep this Command Prompt window open while using the application!
   - You can minimize it, but don't close it
   - If you close it, the AI stops working

✅ **Ollama service is running!**

---

### **STEP 4: Extract Local AI Assistant (2 minutes)**

Now install the application we created for you.

#### Extract the Application

1. **Find the file**: `LocalAIAssistant-Portable.zip`
   - You received this from @durga.kr2003
   - Usually in Downloads folder

2. **Extract it**:
   - Right-click on `LocalAIAssistant-Portable.zip`
   - Click "Extract All..."
   - Choose where to extract (Desktop or Documents recommended)
   - Click "Extract"

3. Wait for extraction to complete
   - A new folder appears: `LocalAIAssistant`

✅ **Application extracted!**

---

### **STEP 5: Launch the Application (1 minute)**

Time to start chatting with your AI!

#### Start the Application

1. **Open the extracted folder**: `LocalAIAssistant`
2. **Find**: `START.bat` file
3. **Double-click** it
4. A Command Prompt window appears
5. Your browser opens automatically with the application
6. If browser doesn't open, go to: **http://127.0.0.1:8000**

✅ **Application is running!**

---

## Running the Application

### Every Time You Want to Use It

**Important**: Follow this order:

1. **Start Ollama Service** (if not already running)
   - Open Command Prompt
   - Type: `ollama serve`
   - Press Enter
   - Keep this window open

2. **Start Local AI Assistant**
   - Go to extracted `LocalAIAssistant` folder
   - Double-click `START.bat`
   - Wait 5-10 seconds
   - Browser opens automatically

3. **Start Chatting!**
   - Type your message
   - Press Enter
   - AI responds

---

## First Time Setup

### On First Launch

When you first open the application, you'll see:

1. **"Local AI Assistant" welcome screen**
2. Click **"Start Chatting"** button
3. A new chat window opens

### First Chat Tips

1. **Type a simple message** like "Hello"
2. **First response takes longer** (30-60 seconds) while the model loads
3. **Later responses are faster** (usually 5-15 seconds)
4. Enjoy your private AI! 🎉

### Customize Your Settings

1. Click **Settings** button (gear icon) in left sidebar
2. Adjust:
   - **Temperature**: 0.1 (precise) to 1.0 (creative)
   - **Max Tokens**: How long responses can be
   - **System Prompt**: How the AI behaves
   - **Theme**: Dark or Light mode

---

## Troubleshooting

### Problem: "Ollama service unavailable"

**Solution**:
1. Make sure `ollama serve` is running (see Step 3)
2. Check if it's running:
   - Open Command Prompt
   - Type: `ollama list`
   - If it shows your model, Ollama is working

### Problem: "Model not found"

**Solution**:
1. Open Command Prompt
2. Type: `ollama pull qwen2.5:3b`
3. Wait for download to complete

### Problem: Application won't start / "Port 8000 already in use"

**Solution**:
1. Close other applications using port 8000
2. Or: Open the `START.bat` file in a text editor
3. Change `--port 8000` to `--port 8001`
4. Save and try again

### Problem: Very slow responses

**Reasons**:
- First response is always slower (model loading)
- Your computer might be running other heavy applications
- Close other apps and try again

### Problem: "Connection refused" errors

**Solution**:
1. Make sure Ollama is running: `ollama serve`
2. Wait 5 seconds before trying again
3. Restart Ollama if needed

### Problem: Application crashes

**Solution**:
1. Close all windows
2. Stop Command Prompts
3. Wait 10 seconds
4. Start fresh: Run `ollama serve` first, then `START.bat`

---

## Tips & Tricks

### 💡 Pro Tips

1. **Keep Ollama running**
   - Minimize, don't close
   - You can use other apps while it runs

2. **Try different prompts**
   - Specific questions get better answers
   - "Explain quantum computing" works better than "Tell me about physics"

3. **Adjust temperature for your needs**
   - Creative writing: Temperature 0.8-1.0
   - Factual info: Temperature 0.1-0.3
   - Balanced: Temperature 0.5-0.7

4. **Clear chat history regularly**
   - Long conversations use more memory
   - Delete old chats to keep it fast

5. **Custom system prompt**
   - Change how the AI behaves
   - Example: "You are a Python programming expert"
   - Now all responses are about Python!

### 🎯 Example Prompts to Try

- "Write a Python script to calculate factorial"
- "Explain machine learning in simple terms"
- "Create a recipe for chocolate cake"
- "Write a funny poem about coding"
- "Help me debug this code: [paste code]"

### ⚙️ Performance Tips

1. **Close unnecessary programs** before using
2. **Use wired internet** if possible (WiFi works too)
3. **Keep Windows updated**
4. **Restart your computer** if things get slow
5. **Don't run heavy games** while using the AI

---

## Frequently Asked Questions

### Q: Is my data safe?

**A**: Completely! Everything stays on your computer. No data is sent anywhere. Your conversations are stored in a local SQLite database that you control.

### Q: Can I switch AI models?

**A**: Yes! Install other Ollama models:
```cmd
ollama pull llama2
ollama pull neural-chat
```
Then select from Settings in the app.

### Q: How much internet do I need?

**A**: Only for initial setup:
- Downloading Ollama: ~150MB
- Downloading model: ~2GB
- After that: 0% - completely offline!

### Q: Can I uninstall it easily?

**A**: Yes! Just delete the `LocalAIAssistant` folder. That's it! 
(Keep Ollama if you want to use other Ollama models)

### Q: Why is the first response slow?

**A**: The AI model loads into memory on first use. After that, responses are much faster!

### Q: Can I use it on Mac/Linux?

**A**: This version is for Windows. Mac/Linux versions can be built from the open-source code.

### Q: What if I want to switch models?

**A**: 
```cmd
ollama pull llama2:7b
```
Then select in Settings → Model Selection

### Q: Can I modify the system prompt?

**A**: Yes! Go to Settings → Scroll down → Edit "System Prompt"

---

## Getting Help

### Before Contacting Support

1. ✅ Check "Ollama is running" (ollama serve window open?)
2. ✅ Check "Model is installed" (ollama list)
3. ✅ Check "Port 8000 is available"
4. ✅ Read Troubleshooting section above
5. ✅ Restart and try again

### Contact Creator

- **Instagram**: [@durga.kr2003](https://instagram.com/durga.kr2003)
- **GitHub**: [Repository link]

### Report Issues

If you find a bug:
1. Note what you did
2. Note the error message
3. Contact @durga.kr2003 on Instagram with details

---

## Summary

### Complete Setup Checklist

- [ ] Downloaded Ollama
- [ ] Installed Ollama
- [ ] Downloaded AI model (`ollama pull qwen2.5:3b`)
- [ ] Extracted `LocalAIAssistant-Portable.zip`
- [ ] Started `ollama serve` in Command Prompt
- [ ] Started application (`START.bat`)
- [ ] Browser opened at `http://127.0.0.1:8000`
- [ ] Typed first message and got response
- [ ] ✅ All done! Enjoy! 🎉

---

## Quick Reference Card

### Every Time You Use It

```
1. Open Command Prompt
   Type: ollama serve
   Press Enter (keep open)

2. Go to LocalAIAssistant folder
   Double-click: START.bat
   Wait 5 seconds

3. Browser opens automatically
   OR go to: http://127.0.0.1:8000

4. Start chatting!
```

### Important Commands

```
Check Ollama:        ollama list
Pull new model:      ollama pull <model-name>
Start Ollama:        ollama serve
Stop application:    Close Command Prompt window
```

### Common Models to Try

```
ollama pull llama2:7b        (Larger, better)
ollama pull neural-chat:7b   (Good for chat)
ollama pull mistral:7b       (Fast & good)
ollama pull phi:2.7b         (Very fast)
```

---

## Congratulations! 🎉

You now have a **private, offline AI assistant** running on your computer!

**Built with ❤️ by [@durga.kr2003](https://instagram.com/durga.kr2003)**

### Enjoy your AI! 🚀

---

**Last Updated**: August 29, 2026  
**Version**: 1.0.0
