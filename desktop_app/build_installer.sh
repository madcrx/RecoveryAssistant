#!/bin/bash
# RecoveryAssistant - Build Windows Installer (from Linux/Mac)
# Requires wine to run PyInstaller on non-Windows systems

echo "========================================"
echo "RecoveryAssistant Desktop Build Script"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

echo "[1/6] Checking Python version..."
python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
if [ $? -ne 0 ]; then
    echo "ERROR: Python 3.11 or higher is required"
    exit 1
fi
echo "OK - Python version is sufficient"

echo ""
echo "[2/6] Installing/upgrading build tools..."
pip3 install --upgrade pip setuptools wheel
pip3 install --upgrade pyinstaller

echo ""
echo "[3/6] Installing application dependencies..."
pip3 install -r requirements.txt

echo ""
echo "[4/6] Cleaning previous builds..."
rm -rf dist build

echo ""
echo "[5/6] Building executable with PyInstaller..."
echo "This may take 5-10 minutes..."
pyinstaller RecoveryAssistant.spec --clean --noconfirm

if [ ! -f "dist/RecoveryAssistant.exe" ]; then
    echo "ERROR: Build failed - executable not created"
    exit 1
fi

echo ""
echo "OK - Executable created successfully!"
echo "Location: dist/RecoveryAssistant.exe"
ls -lh "dist/RecoveryAssistant.exe"

echo ""
echo "[6/6] For installer creation:"
echo "Run this script on Windows with Inno Setup installed"
echo "Or use: wine 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' installer/setup.iss"

echo ""
echo "========================================"
echo "BUILD COMPLETE!"
echo "========================================"
echo ""
echo "Executable: dist/RecoveryAssistant.exe"
echo ""
echo "To create installer, run on Windows:"
echo "  build_installer.bat"
echo ""
