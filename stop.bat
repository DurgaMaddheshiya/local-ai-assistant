@echo off
setlocal

title Local AI Assistant - Stop

echo.
echo ========================================================
echo   Local AI Assistant - Stopping
echo ========================================================
echo.

:: -------------------------------------------------------
:: Load port from .env (default 8000)
:: -------------------------------------------------------
set PORT=8000
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        if "%%a"=="PORT" set PORT=%%b
    )
)

:: -------------------------------------------------------
:: Find and kill the uvicorn process on the configured port
:: -------------------------------------------------------
echo   Looking for server process on port %PORT%...

set FOUND=0
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
    if not "%%p"=="0" (
        echo   Found process PID: %%p — stopping...
        taskkill /PID %%p /F >nul 2>&1
        if not errorlevel 1 (
            echo   Server stopped successfully.
            set FOUND=1
        ) else (
            echo   Could not stop process %%p ^(may need admin rights^).
            set FOUND=1
        )
    )
)

if "%FOUND%"=="0" (
    echo   No server process found on port %PORT%.
    echo   The server may already be stopped.
)

:: -------------------------------------------------------
:: Also kill any stray python/uvicorn processes by name
:: (only if they match our working directory)
:: -------------------------------------------------------
echo.
echo   Cleaning up any remaining uvicorn processes...
taskkill /IM "python.exe" /FI "WINDOWTITLE eq Local AI Assistant" /F >nul 2>&1

echo.
echo   Done.
echo.
pause
endlocal
