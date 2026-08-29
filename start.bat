@echo off
setlocal EnableDelayedExpansion

title Local AI Assistant

echo.
echo ========================================================
echo   Local AI Assistant
echo ========================================================
echo.

:: -------------------------------------------------------
:: Check virtual environment
:: -------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo   ERROR: Virtual environment not found.
    echo   Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

:: -------------------------------------------------------
:: Check .env
:: -------------------------------------------------------
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo   Created .env from .env.example
    )
)

:: -------------------------------------------------------
:: Load config values for display
:: -------------------------------------------------------
set HOST=127.0.0.1
set PORT=8000
set OLLAMA_MODEL=qwen2.5:3b

for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if "%%a"=="HOST"         set HOST=%%b
    if "%%a"=="PORT"         set PORT=%%b
    if "%%a"=="OLLAMA_MODEL" set OLLAMA_MODEL=%%b
)

:: -------------------------------------------------------
:: Check Ollama
:: -------------------------------------------------------
echo   Checking Ollama service...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo.
    echo   WARNING: Ollama is not running.
    echo   The application will start, but AI responses will fail until
    echo   Ollama is running.
    echo.
    echo   To start Ollama, open a new terminal and run:
    echo      ollama serve
    echo.
    echo   To install the AI model, run:
    echo      ollama pull %OLLAMA_MODEL%
    echo.
    timeout /t 3 /nobreak >nul
) else (
    echo   Ollama is running.
)

:: -------------------------------------------------------
:: Check data and logs directories
:: -------------------------------------------------------
if not exist "data"  mkdir data
if not exist "logs"  mkdir logs

:: -------------------------------------------------------
:: Start the backend
:: -------------------------------------------------------
echo.
echo   Starting Local AI Assistant backend...
echo   Model : %OLLAMA_MODEL%
echo   URL   : http://%HOST%:%PORT%
echo.
echo   Press Ctrl+C to stop the server.
echo   To stop cleanly, use stop.bat in another terminal.
echo.
echo ========================================================
echo.

:: Small delay so the user can read the info
timeout /t 2 /nobreak >nul

:: Open the browser after a short delay (background)
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://%HOST%:%PORT%"

:: Start the FastAPI server (foreground — Ctrl+C stops it)
.venv\Scripts\python -m uvicorn backend.main:app ^
    --host %HOST% ^
    --port %PORT% ^
    --log-level info

echo.
echo   Server stopped.
echo.
pause
endlocal
