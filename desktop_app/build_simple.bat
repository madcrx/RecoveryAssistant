@echo off
REM RecoveryAssistant - Simple Build Script
REM Builds standalone executable (no installer)

echo ========================================
echo RecoveryAssistant Build Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from python.org
    pause
    exit /b 1
)

echo [1/5] Upgrading pip and installing PyInstaller...
python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller

echo.
echo [2/5] Installing application dependencies...
echo This may take a few minutes...
python -m pip install -r requirements.txt

echo.
echo [3/5] Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo.
echo [4/5] Building executable with PyInstaller...
echo This may take 5-10 minutes...
python -m PyInstaller RecoveryAssistant.spec --clean --noconfirm

if not exist "dist\RecoveryAssistant.exe" (
    echo.
    echo ERROR: Build failed - executable not created
    echo.
    echo Check the errors above. Common issues:
    echo - Missing dependencies: Run 'pip install -r requirements.txt' again
    echo - Incorrect spec file: Make sure RecoveryAssistant.spec is in current directory
    echo.
    pause
    exit /b 1
)

echo.
echo [5/5] Build complete!
echo.
echo ========================================
echo SUCCESS!
echo ========================================
echo.
echo Executable created: dist\RecoveryAssistant.exe
echo.
dir "dist\RecoveryAssistant.exe" | find "RecoveryAssistant.exe"
echo.
echo You can now run the application from:
echo   dist\RecoveryAssistant.exe
echo.
echo To create an installer:
echo 1. Install Inno Setup from: https://jrsoftware.org/isdl.php
echo 2. Run: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
echo.

REM Open dist folder
explorer "dist"

pause
