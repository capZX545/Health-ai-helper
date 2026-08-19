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
echo    ( دستیار هوشمند پزشکی فارسی )
echo  ============================================
echo.

rem ---------- 1) Python ----------
set PY=
py -3 --version >nul 2>&1 && set PY=py -3
if not defined PY ( python --version >nul 2>&1 && set PY=python )
if not defined PY (
  echo  [ERROR] Python yoft nashod!
  echo  Python 3.10+ ra az python.org nasb konid va dokme
  echo  "Add python.exe to PATH" ra faal konid, dobare ejra konid.
  pause & exit /b 1
)
echo  [1/6] Python OK: %PY%

rem ---------- 2) Dependencies ----------
echo  [2/6] Nasb ketabkhane-ha (pip install -r requirements.txt) ...
%PY% -m pip install --upgrade pip >nul 2>&1
%PY% -m pip install -r requirements.txt
if errorlevel 1 ( echo  [ERROR] pip failed & pause & exit /b 1 )

rem ---------- 3) py_compile test ----------
echo  [3/6] Test compile kolan file-haye Python ...
%PY% -m compileall -q .
if errorlevel 1 ( echo  [ERROR] Syntax error dar file-ha! & pause & exit /b 1 )
echo        OK - hame file-ha sahih hastand.

rem ---------- 4) Data files ----------
echo  [4/6] Sakhte dataset va database ...
if not exist medical_ml_test_dataset.csv ( %PY% generate_dataset.py )
if not exist diseases_offline.db ( %PY% build_diseases_db.py )

rem ---------- 5) PyInstaller ----------
echo  [5/6] Sakhte EXE ba PyInstaller ...
%PY% build_exe.py
if errorlevel 1 ( echo  [ERROR] Build EXE failed & pause & exit /b 1 )

rem ---------- 6) Inno Setup ----------
echo  [6/6] Sakhte Setup.exe ba Inno Setup 6 ...
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
  echo  [ERROR] Inno Setup 6 yoft nashod!
  echo  Az jrsoftware.org  Inno Setup 6 ra nasb konid va dobare ejra konid.
  start "" https://jrsoftware.org/isdl.php
  pause & exit /b 1
)
%ISCC% "NexusMed_Installer.iss"
if errorlevel 1 ( echo  [ERROR] Inno Setup failed & pause & exit /b 1 )

echo.
echo  ============================================
echo   DONE!  Output\NexusMed_Setup_v2.0.exe
echo   Exitere bejaygozin-e pezek nist. Emergency 115/112
echo  ============================================
if exist Output\NexusMed_Setup_v2.0.exe ( start "" explorer /select, Output\NexusMed_Setup_v2.0.exe )
pause
