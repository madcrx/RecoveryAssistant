@echo off
REM RecoveryAssistant - Build Windows Installer
REM This script builds a single-file executable and creates an installer

echo ========================================
echo RecoveryAssistant Desktop Build Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)

echo [1/6] Checking Python version...
python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.11 or higher is required
    pause
    exit /b 1
)
echo OK - Python version is sufficient

echo.
echo [2/6] Installing/upgrading build tools...
pip install --upgrade pip setuptools wheel
pip install --upgrade pyinstaller

echo.
echo [3/6] Installing application dependencies...
pip install -r requirements.txt

echo.
echo [4/6] Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "RecoveryAssistant.spec" del RecoveryAssistant.spec

echo.
echo [5/6] Building executable with PyInstaller...
echo This may take 5-10 minutes...
pyinstaller RecoveryAssistant.spec --clean --noconfirm

if not exist "dist\RecoveryAssistant.exe" (
    echo ERROR: Build failed - executable not created
    pause
    exit /b 1
)

echo.
echo OK - Executable created successfully!
echo Location: dist\RecoveryAssistant.exe
echo Size:
dir "dist\RecoveryAssistant.exe" | find "RecoveryAssistant.exe"

echo.
echo [6/6] Creating installer with Inno Setup...

REM Check if Inno Setup is installed
set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_PATH%" (
    echo.
    echo WARNING: Inno Setup is not installed
    echo.
    echo To create the installer:
    echo 1. Download Inno Setup from: https://jrsoftware.org/isdl.php
    echo 2. Install Inno Setup
    echo 3. Run: "%INNO_PATH%" installer\setup.iss
    echo.
    echo Executable is ready at: dist\RecoveryAssistant.exe
    pause
    exit /b 0
)

REM Create installer directory if it doesn't exist
if not exist "dist\installer" mkdir "dist\installer"

REM Compile installer
"%INNO_PATH%" "installer\setup.iss"

if errorlevel 1 (
    echo ERROR: Installer creation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo.
echo Executable: dist\RecoveryAssistant.exe
echo Installer:  dist\installer\RecoveryAssistant_Setup_v1.0.0.exe
echo.
echo You can now:
echo 1. Test the executable by running dist\RecoveryAssistant.exe
echo 2. Distribute the installer to end users
echo.

REM Open dist folder
explorer "dist"

pause
