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
:: Check Ollama
:: -------------------------------------------------------
echo   Checking Ollama service...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo.
    echo   WARNING: Ollama is not running.
    echo   Please start Ollama first:  ollama serve
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
:: Launch desktop window (no browser needed)
:: -------------------------------------------------------
echo.
echo   Opening Local AI Assistant desktop window...
echo.
echo ========================================================
echo.

.venv\Scripts\python launcher.py

echo.
echo   Application closed.
echo.
pause
endlocal
