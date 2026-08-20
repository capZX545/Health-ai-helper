@echo off
chcp 65001 >nul
title NexusMed 2077
cd /d "%~dp0"
echo.
echo  ================================
echo    NEXUSMED 2077 - CHOOSE VERSION
echo  ================================
echo.
echo  [1] Desktop  (window app)
echo  [2] Web      (browser app)
echo.
set /p choice="  Select (1 or 2): "
if "%choice%"=="1" goto desktop
if "%choice%"=="2" goto web
echo Invalid choice.
pause & exit /b 1

:desktop
python run_2077.py
pause & exit /b %errorlevel%

:web
python run_web.py
pause & exit /b %errorlevel%
