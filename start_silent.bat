@echo off
setlocal EnableDelayedExpansion

:: -------------------------------------------------------
:: Check virtual environment
:: -------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    powershell -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Virtual environment not found. Please run setup.bat first.', 'Durgara - Error')"
    exit /b 1
)

:: -------------------------------------------------------
:: Check .env
:: -------------------------------------------------------
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
    )
)

:: -------------------------------------------------------
:: Check data and logs directories
:: -------------------------------------------------------
if not exist "data"  mkdir data
if not exist "logs"  mkdir logs

:: -------------------------------------------------------
:: Launch - pythonw hides the console window entirely
:: -------------------------------------------------------
cd /d "%~dp0"
start "" .venv\Scripts\pythonw.exe launcher.py

endlocal
