@echo off
setlocal EnableDelayedExpansion

title Local AI Assistant - Create Portable Installer

echo.
echo ========================================================
echo   Local AI Assistant - Portable Installer Builder
echo ========================================================
echo.

:: Check if virtual environment exists
if not exist ".venv" (
    echo ERROR: Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

:: Step 1: Install PyInstaller
echo [1/3] Installing PyInstaller...
.venv\Scripts\pip install --quiet pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)
echo   ✓ PyInstaller installed.

:: Step 2: Clean old builds
echo.
echo [2/3] Cleaning old builds...
if exist "dist" rmdir /s /q dist 2>nul
if exist "build" rmdir /s /q build 2>nul
if exist "LocalAIAssistant-Portable.zip" del LocalAIAssistant-Portable.zip 2>nul
echo   ✓ Old builds cleaned.

:: Step 3: Build with PyInstaller
echo.
echo [3/3] Building application bundle (this may take 3-5 minutes)...
.venv\Scripts\pyinstaller ^
  --onedir ^
  --windowed ^
  --icon="installer_icon.ico" ^
  --add-data="frontend;frontend" ^
  --add-data=".env.example;." ^
  --name="LocalAIAssistant" ^
  --distpath="dist" ^
  backend/main.py

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo   ✓ Application bundle created.

:: Step 4: Copy additional files
echo.
echo [4/4] Preparing installer package...
copy /Y ".env.example" "dist\LocalAIAssistant\.env.example" >nul
copy /Y "README.md" "dist\LocalAIAssistant\README.md" >nul
copy /Y "INSTALL_GUIDE.md" "dist\LocalAIAssistant\INSTALL_GUIDE.md" >nul

:: Create startup launcher script
echo Creating launcher script...
(
echo @echo off
echo cd /d "%%~dp0"
echo start http://127.0.0.1:8000
echo LocalAIAssistant.exe
) > "dist\LocalAIAssistant\START.bat"

:: Create instructions file
echo Creating instructions...
(
echo ========================================================
echo   LOCAL AI ASSISTANT - PORTABLE VERSION
echo ========================================================
echo.
echo BEFORE USING THIS APPLICATION:
echo.
echo 1. Install Ollama:
echo    - Download from https://ollama.com/download
echo    - Run installer (next-next-finish^)
echo.
echo 2. Setup AI Model:
echo    - Open Command Prompt
echo    - Run: ollama pull qwen2.5:3b
echo    - Wait for completion (2GB download^)
echo.
echo 3. Start Ollama Service:
echo    - Open Command Prompt
echo    - Run: ollama serve
echo    - Keep this terminal open
echo.
echo 4. Launch Application:
echo    - Double-click START.bat
echo    - Or double-click LocalAIAssistant.exe
echo    - Browser opens automatically
echo.
echo 5. Start Chatting!
echo    - Type your message
echo    - Press Enter
echo    - AI responds!
echo.
echo ========================================================
echo   TROUBLESHOOTING
echo ========================================================
echo.
echo Q: "Ollama service unavailable"
echo A: Make sure you have "ollama serve" running in Command Prompt
echo.
echo Q: "Model not found"
echo A: Run "ollama pull qwen2.5:3b" in Command Prompt
echo.
echo Q: Application won't start
echo A: Check port 8000 is not used by other applications
echo.
echo ========================================================
) > "dist\LocalAIAssistant\QUICK_START.txt"

echo   ✓ Instructions created.

echo.
echo ========================================================
echo   ✓ BUILD COMPLETE!
echo ========================================================
echo.
echo   Portable application ready at:
echo     dist\LocalAIAssistant\
echo.
echo   To distribute:
echo     1. Zip the entire "dist\LocalAIAssistant" folder
echo     2. Name it "LocalAIAssistant-Portable.zip"
echo     3. Share with users
echo.
echo   Users just need to:
echo     1. Extract zip
echo     2. Run START.bat
echo     3. Done!
echo.
echo   Note: Users still need to install Ollama separately
echo         (it's the AI engine - can't be bundled)
echo.
pause
