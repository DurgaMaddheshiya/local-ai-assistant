@echo off
setlocal EnableDelayedExpansion

title Local AI Assistant - Setup

echo.
echo ========================================================
echo   Local AI Assistant - Setup
echo ========================================================
echo.

:: -------------------------------------------------------
:: 1. Check Python
:: -------------------------------------------------------
echo [1/7] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ERROR: Python is not installed or not on PATH.
    echo   Download Python 3.11+ from https://www.python.org/downloads/
    echo   Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VERSION=%%v
echo   Python %PY_VERSION% found.

:: Check for minimum version 3.10
for /f "tokens=1,2 delims=." %%a in ("%PY_VERSION%") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)
if %PY_MAJOR% LSS 3 (
    echo   ERROR: Python 3.10 or higher is required.
    pause
    exit /b 1
)
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 10 (
    echo   ERROR: Python 3.10 or higher is required. Found %PY_VERSION%.
    pause
    exit /b 1
)

:: -------------------------------------------------------
:: 2. Create virtual environment
:: -------------------------------------------------------
echo.
echo [2/7] Creating virtual environment...
if exist ".venv" (
    echo   Virtual environment already exists, skipping creation.
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo   ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo   Virtual environment created at .venv\
)

:: -------------------------------------------------------
:: 3. Install dependencies
:: -------------------------------------------------------
echo.
echo [3/7] Installing Python dependencies...
echo   This may take a few minutes on first run...

.venv\Scripts\pip install --quiet --upgrade pip >nul 2>&1
.venv\Scripts\pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo   ERROR: Failed to install dependencies.
    echo   Check your internet connection and try again.
    pause
    exit /b 1
)
echo   Dependencies installed successfully.

:: -------------------------------------------------------
:: 4. Create required directories
:: -------------------------------------------------------
echo.
echo [4/7] Creating required directories...
if not exist "data"  mkdir data
if not exist "logs"  mkdir logs
echo   Directories ready.

:: -------------------------------------------------------
:: 5. Set up .env file
:: -------------------------------------------------------
echo.
echo [5/7] Setting up configuration...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo   Created .env from .env.example
    echo   Edit .env to change settings such as the Ollama model.
) else (
    echo   .env already exists, skipping.
)

:: -------------------------------------------------------
:: 6. Initialize database
:: -------------------------------------------------------
echo.
echo [6/7] Initializing database...
.venv\Scripts\python -c "import sys; sys.path.insert(0, '.'); from backend.config import settings, ensure_directories; from backend.models.init_db import initialize_database; ensure_directories(settings); initialize_database(); print('  Database initialized at:', settings.database_path)"
if errorlevel 1 (
    echo   ERROR: Failed to initialize database.
    pause
    exit /b 1
)

:: -------------------------------------------------------
:: 7. Check Ollama and model
:: -------------------------------------------------------
echo.
echo [7/7] Checking Ollama...

:: Load model name from .env if available
set OLLAMA_MODEL=qwen2.5:3b
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if "%%a"=="OLLAMA_MODEL" set OLLAMA_MODEL=%%b
)

:: Check if Ollama executable is on PATH
where ollama >nul 2>&1
if errorlevel 1 (
    echo.
    echo   WARNING: Ollama is not installed or not on PATH.
    echo.
    echo   To install Ollama:
    echo     1. Download from https://ollama.com/download
    echo     2. Run the installer
    echo     3. Open a new terminal and run:
    echo.
    echo        ollama pull %OLLAMA_MODEL%
    echo.
) else (
    echo   Ollama found.

    :: Check if Ollama service is running
    curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
    if errorlevel 1 (
        echo   Ollama service is not running. Start it with:  ollama serve
    ) else (
        :: Check if the configured model is installed
        ollama list 2>nul | findstr /i "%OLLAMA_MODEL%" >nul 2>&1
        if errorlevel 1 (
            echo.
            echo   WARNING: Model "%OLLAMA_MODEL%" is not installed.
            echo   Install it by running:
            echo.
            echo      ollama pull %OLLAMA_MODEL%
            echo.
        ) else (
            echo   Model %OLLAMA_MODEL% is ready.
        )
    )
)

:: -------------------------------------------------------
:: Done
:: -------------------------------------------------------
echo.
echo ========================================================
echo   Setup complete!
echo ========================================================
echo.
echo   Next steps:
echo   1. Make sure Ollama is running:     ollama serve
echo   2. Make sure the model is pulled:   ollama pull %OLLAMA_MODEL%
echo   3. Start the application:           start.bat
echo.
pause
endlocal
