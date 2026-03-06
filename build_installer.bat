@echo off
REM ================================================================
REM  Peak Volume Manager - Build Installer
REM  Run this from the peak-volume-manager project root on Windows.
REM
REM  Prerequisites:
REM    - Python 3.10+ with pip
REM    - Inno Setup 6 installed (https://jrsoftware.org/isinfo.php)
REM
REM  This script will:
REM    1. Install build dependencies (PyInstaller, Pillow)
REM    2. Generate the application icon (.ico)
REM    3. Create a gui/__init__.py if missing
REM    4. Bundle with PyInstaller into dist/PeakVolumeManager/
REM    5. Compile the Inno Setup installer
REM
REM  Output: Output/PeakVolumeManager_Setup_1.0.0.exe
REM ================================================================

setlocal EnableDelayedExpansion

echo.
echo ============================================
echo  Peak Volume Manager - Installer Builder
echo ============================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)
echo [OK] Python found

REM --- Install build dependencies ---
echo.
echo [1/5] Installing build dependencies...
pip install pyinstaller Pillow --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] PyInstaller and Pillow installed

REM --- Install app dependencies ---
echo.
echo [2/5] Installing application dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install app dependencies.
    pause
    exit /b 1
)
echo [OK] Application dependencies installed

REM --- Generate icon ---
echo.
echo [3/5] Generating application icon...
python generate_icon.py
if errorlevel 1 (
    echo WARNING: Icon generation failed. Building without custom icon.
)
if exist assets\icon.ico (
    echo [OK] Icon created: assets\icon.ico
) else (
    echo [WARN] No icon file — installer will use default icon.
)

REM --- Ensure gui/__init__.py exists ---
if not exist gui\__init__.py (
    echo. > gui\__init__.py
    echo [OK] Created gui\__init__.py
)

REM --- PyInstaller build ---
echo.
echo [4/5] Building with PyInstaller (this may take 1-2 minutes)...
pyinstaller peak_volume_manager.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed. See output above for details.
    echo Common fixes:
    echo   - Make sure all app dependencies are installed
    echo   - Try: pip install --upgrade pyinstaller
    echo   - Check for antivirus blocking the build
    pause
    exit /b 1
)
echo [OK] PyInstaller build complete

REM --- Verify the build ---
if not exist dist\PeakVolumeManager\PeakVolumeManager.exe (
    echo ERROR: Expected dist\PeakVolumeManager\PeakVolumeManager.exe not found.
    pause
    exit /b 1
)
echo [OK] Executable verified: dist\PeakVolumeManager\PeakVolumeManager.exe

REM --- Inno Setup ---
echo.
echo [5/5] Compiling installer with Inno Setup...

REM Try common install locations for Inno Setup
set ISCC=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else (
    where iscc >nul 2>&1
    if not errorlevel 1 (
        set "ISCC=iscc"
    )
)

if defined ISCC (
    "%ISCC%" installer.iss
    if errorlevel 1 (
        echo ERROR: Inno Setup compilation failed.
        pause
        exit /b 1
    )
    echo.
    echo ============================================
    echo  BUILD COMPLETE!
    echo ============================================
    echo.
    echo  Installer: Output\PeakVolumeManager_Setup_1.0.0.exe
    echo.
    echo  You can distribute this single .exe file.
    echo  Users just double-click to install.
    echo ============================================
) else (
    echo.
    echo ============================================
    echo  PyInstaller build succeeded!
    echo  Portable app: dist\PeakVolumeManager\
    echo ============================================
    echo.
    echo  Inno Setup 6 was not found on this system.
    echo  To create the installer .exe:
    echo    1. Download Inno Setup 6 from https://jrsoftware.org/isinfo.php
    echo    2. Install it
    echo    3. Open installer.iss in Inno Setup Compiler
    echo    4. Click Build ^> Compile
    echo.
    echo  OR you can distribute dist\PeakVolumeManager\ as a portable app.
    echo ============================================
)

echo.
pause
