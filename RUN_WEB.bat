@echo off
chcp 65001 >nul
title NexusMed 2077 - Web
cd /d "%~dp0"

echo.
echo  Starting NexusMed 2077 Web...
echo  Browser will open at http://localhost:2077
echo  Press Ctrl+C to stop.
echo.

python run_web.py
if errorlevel 1 (
    echo.
    echo  ERROR: Could not start server.
    echo  Run diagnose.py to find the problem:
    echo      python diagnose.py
    echo.
    pause
)
pause
