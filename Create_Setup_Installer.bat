@echo off
rem ============================================================
rem  NexusMed 2077 - Build Setup Installer
rem  One double-click: installs deps -> compiles -> EXE -> Setup
rem  Requires: Python 3.10+  +  Inno Setup 6
rem ============================================================
chcp 65001 >nul
title NexusMed 2077 Builder
cd /d "%~dp0"

echo.
echo  ============================================
echo    NEXUSMED 2077 - BUILD SETUP INSTALLER
echo    bilingual medical assistant (en/fa)
echo  ============================================
echo.

rem ---------- 1) Python ----------
set PY=
py -3 --version >nul 2>&1 && set PY=py -3
if not defined PY ( python --version >nul 2>&1 && set PY=python )
if not defined PY (
  echo  [ERROR] Python not found!
  echo  Install Python 3.10+ from python.org and tick
  echo  "Add python.exe to PATH", then run this file again.
  pause & exit /b 1
)
echo  [1/6] Python OK: %PY%

rem ---------- 2) Dependencies ----------
echo  [2/6] Installing dependencies (pip install -r requirements.txt) ...
%PY% -m pip install --upgrade pip >nul 2>&1
%PY% -m pip install -r requirements.txt
if errorlevel 1 ( echo  [ERROR] pip failed & pause & exit /b 1 )

rem ---------- 3) compile check ----------
echo  [3/6] Compiling all Python files as a sanity check ...
%PY% -m compileall -q .
if errorlevel 1 ( echo  [ERROR] Syntax error in one of the files! & pause & exit /b 1 )
echo        OK - all files compiled.

rem ---------- 4) Data files ----------
echo  [4/6] Generating dataset and database ...
if not exist medical_ml_test_dataset.csv ( %PY% generate_dataset.py )
if not exist diseases_offline.db ( %PY% build_diseases_db.py )

rem ---------- 5) PyInstaller ----------
echo  [5/6] Building the EXE with PyInstaller ...
%PY% build_exe.py
if errorlevel 1 ( echo  [ERROR] Build EXE failed & pause & exit /b 1 )

rem ---------- 6) Inno Setup ----------
echo  [6/6] Building Setup.exe with Inno Setup 6 ...
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
  echo  [ERROR] Inno Setup 6 not found!
  echo  Install Inno Setup 6 from jrsoftware.org and run this again.
  start "" https://jrsoftware.org/isdl.php
  pause & exit /b 1
)
%ISCC% "NexusMed_Installer.iss"
if errorlevel 1 ( echo  [ERROR] Inno Setup failed & pause & exit /b 1 )

echo.
echo  ============================================
echo   DONE!  Output\NexusMed_Setup_v2.0.exe
echo   Not a doctor replacement. Emergency 115/112
echo  ============================================
if exist Output\NexusMed_Setup_v2.0.exe ( start "" explorer /select, Output\NexusMed_Setup_v2.0.exe )
pause
