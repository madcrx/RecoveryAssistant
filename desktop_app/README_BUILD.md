# RecoveryAssistant Desktop - Build Instructions

This directory contains the standalone Windows desktop application.

## For End Users

**Download the installer:** `RecoveryAssistant_Setup.exe`

No build required - just run the installer!

See [QUICK_START.md](QUICK_START.md) for setup instructions.

---

## For Developers

### Quick Build

**Windows:**
```batch
build_installer.bat
```

**Linux/Mac:**
```bash
./build_installer.sh
```

This creates:
- `dist/RecoveryAssistant.exe` - Standalone executable
- `dist/installer/RecoveryAssistant_Setup_v1.0.0.exe` - Full installer

### Manual Build Steps

1. **Install dependencies:**
   ```batch
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Build executable:**
   ```batch
   pyinstaller RecoveryAssistant.spec --clean --noconfirm
   ```

3. **Test executable:**
   ```batch
   dist\RecoveryAssistant.exe
   ```

4. **Create installer (requires Inno Setup):**
   ```batch
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
   ```

### Development Mode

**Run from source without building:**
```batch
python main.py
```

**Hot reload during development:**
- Edit Python files
- Restart `main.py`
- No rebuild needed

---

## Documentation

- **[BUILD_GUIDE.md](BUILD_GUIDE.md)** - Complete build guide
- **[QUICK_START.md](QUICK_START.md)** - End user setup guide
- **[INSTALL_INFO.txt](INSTALL_INFO.txt)** - Installation information
- **[LICENSE.txt](LICENSE.txt)** - End user license agreement

---

## Project Structure

```
desktop_app/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── RecoveryAssistant.spec          # PyInstaller configuration
├── version_info.txt                 # Windows version info
│
├── app/                             # Application code
│   ├── gui/                         # PyQt6 GUI components
│   ├── services/                    # Business logic
│   ├── models/                      # Database models
│   └── utils/                       # Utilities
│
├── installer/                       # Installer configuration
│   └── setup.iss                    # Inno Setup script
│
├── resources/                       # Application resources
│   ├── icons/                       # Application icons
│   ├── templates/                   # Email templates
│   └── installer/                   # Installer images
│
├── docs/                            # Documentation
│   ├── USER_GUIDE.pdf
│   └── QUICK_START.pdf
│
└── build_installer.bat              # Automated build script
```

---

## Requirements

### System Requirements
- Windows 10/11 (64-bit)
- Python 3.11+ (for development)
- Microsoft Outlook (for email integration)

### Build Requirements
- Python 3.11+
- PyInstaller
- Inno Setup 6 (for installer creation)

### Runtime Dependencies
See [requirements.txt](requirements.txt) for complete list.

Key dependencies:
- PyQt6 (GUI)
- SQLAlchemy (Database)
- pywin32 (Outlook integration)
- xero-python (Xero API)
- openai (AI communication)
- stripe (Payments)
- pandas (CSV import)
- PyPDF2, pdfplumber, camelot (PDF processing)

---

## Building for Distribution

### Release Checklist

Before creating a release:

- [ ] Update version number in:
  - `version_info.txt`
  - `installer/setup.iss`
  - Main window title
- [ ] Test all features
- [ ] Run on clean Windows install
- [ ] Test installer
- [ ] Update changelog
- [ ] Create release notes

### Code Signing (Optional but Recommended)

Sign the executable to avoid Windows SmartScreen warnings:

```batch
signtool sign /f certificate.pfx /p password /tr http://timestamp.digicert.com dist\RecoveryAssistant.exe
```

### Creating a Release

1. Build the installer
2. Test on multiple Windows versions
3. Create GitHub release
4. Upload installer
5. Update documentation

---

## Troubleshooting

### Build Issues

**"Python not found"**
- Install Python 3.11+ from python.org
- Check "Add Python to PATH" during installation

**"Module not found" errors**
- Run: `pip install -r requirements.txt`
- Add missing module to `hiddenimports` in `.spec` file

**Executable too large**
- Normal: 100-150 MB (includes Python runtime)
- Enable UPX compression: `upx=True` in `.spec`

**Slow startup**
- Normal: 5-10 seconds on first launch
- Consider one-folder distribution (faster)

### Testing

**Run with console to see errors:**
1. Edit `RecoveryAssistant.spec`:
   ```python
   console=True  # Change from False
   ```
2. Rebuild
3. Check console output

**Check logs:**
- Location: `%AppData%\RecoveryAssistant\Logs`
- Latest: `recoveryassistant_YYYYMMDD.log`

---

## Development

### Setting Up Development Environment

1. **Clone repository:**
   ```bash
   git clone https://github.com/yourusername/RecoveryAssistant.git
   cd RecoveryAssistant/desktop_app
   ```

2. **Create virtual environment:**
   ```batch
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```batch
   pip install -r requirements.txt
   ```

4. **Run application:**
   ```batch
   python main.py
   ```

### IDE Setup

**VS Code:**
- Install Python extension
- Set Python interpreter to `venv\Scripts\python.exe`
- Use integrated terminal

**PyCharm:**
- Open `desktop_app` folder
- Configure Python interpreter
- Mark `app` as sources root

### Contributing

See main [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## Support

- **Issues**: https://github.com/yourusername/RecoveryAssistant/issues
- **Discussions**: https://github.com/yourusername/RecoveryAssistant/discussions
- **Email**: support@recoveryassistant.com

---

**Happy Building!** 🚀
