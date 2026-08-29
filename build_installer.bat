@echo off
setlocal EnableDelayedExpansion

title Local AI Assistant - Build Installer

echo.
echo ========================================================
echo   Building Local AI Assistant Installer
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
echo [1/4] Installing PyInstaller...
.venv\Scripts\pip install --quiet pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)
echo   PyInstaller installed.

:: Step 2: Clean old builds
echo.
echo [2/4] Cleaning old builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
echo   Old builds cleaned.

:: Step 3: Build executable with PyInstaller
echo.
echo [3/4] Building executable (this may take 2-3 minutes)...
.venv\Scripts\pyinstaller --onedir build.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)
echo   Executable built successfully.

:: Step 4: Check for NSIS
echo.
echo [4/4] Checking for NSIS installer...
where makensis >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: NSIS not installed. Installer (.exe) cannot be created.
    echo.
    echo To install NSIS:
    echo   1. Download from: https://nsis.sourceforge.io/Main_Page
    echo   2. Run installer
    echo   3. Run this script again
    echo.
    echo Portable executable is ready at: dist\LocalAIAssistant\LocalAIAssistant.exe
    pause
    exit /b 0
)

echo   NSIS found. Creating installer...
makensis installer.nsi
if errorlevel 1 (
    echo ERROR: NSIS build failed
    pause
    exit /b 1
)

echo.
echo ========================================================
echo   Build Complete!
echo ========================================================
echo.
echo   Installer created: LocalAIAssistant-Setup.exe
echo.
echo   To distribute:
echo     1. Share LocalAIAssistant-Setup.exe
echo     2. Users run it - everything installs automatically
echo     3. They just need Ollama: https://ollama.com/download
echo.
pause
