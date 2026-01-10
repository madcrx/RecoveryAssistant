# RecoveryAssistant Desktop - Build Guide

Complete guide for building the Windows installer from source.

## Prerequisites

### Required Software

1. **Python 3.11 or higher**
   - Download: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Microsoft Visual C++ Redistributable**
   - Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - Required for some Python packages

3. **Inno Setup 6** (for creating installer)
   - Download: https://jrsoftware.org/isdl.php
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6\`

### Optional Tools

- **Git** - For cloning repository
- **Visual Studio Code** - Recommended IDE

## Build Steps

### Option 1: Automated Build (Recommended)

1. **Open Command Prompt** in the `desktop_app` directory

2. **Run the build script:**
   ```batch
   build_installer.bat
   ```

3. **Wait for completion** (5-10 minutes)
   - Installs dependencies
   - Builds executable
   - Creates installer

4. **Output files:**
   - Executable: `dist\RecoveryAssistant.exe`
   - Installer: `dist\installer\RecoveryAssistant_Setup_v1.0.0.exe`

### Option 2: Manual Build

#### Step 1: Install Dependencies

```batch
cd desktop_app
pip install -r requirements.txt
pip install pyinstaller
```

#### Step 2: Build Executable

```batch
pyinstaller RecoveryAssistant.spec --clean --noconfirm
```

This creates: `dist\RecoveryAssistant.exe`

#### Step 3: Test Executable

```batch
cd dist
RecoveryAssistant.exe
```

Verify the application launches and setup wizard appears.

#### Step 4: Create Installer

```batch
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
```

This creates: `dist\installer\RecoveryAssistant_Setup_v1.0.0.exe`

## Build Configuration

### PyInstaller Spec File

File: `RecoveryAssistant.spec`

**Key settings:**
- `console=False` - No console window (GUI app)
- `onefile=True` - Single executable
- `upx=True` - Compression enabled
- `icon='resources/icons/app_icon.ico'` - Application icon

**Included dependencies:**
- PyQt6 (GUI framework)
- SQLAlchemy (database)
- pywin32 (Outlook integration)
- xero-python (Xero API)
- openai (AI communication)
- stripe (payment processing)
- pandas (CSV import)
- PDF processing libraries

### Inno Setup Script

File: `installer\setup.iss`

**Features:**
- Checks Windows version (10+)
- Verifies Outlook installation
- Installs VC++ Redistributable if needed
- Creates Start Menu shortcuts
- Creates Desktop shortcut (optional)
- Auto-start with Windows (optional)
- Professional uninstaller

## Customization

### Change Version Number

1. Edit `version_info.txt`:
   ```
   filevers=(1, 0, 1, 0),
   prodvers=(1, 0, 1, 0),
   FileVersion=1.0.1.0
   ProductVersion=1.0.1.0
   ```

2. Edit `installer\setup.iss`:
   ```
   #define MyAppVersion "1.0.1"
   ```

### Change Application Icon

1. Create/replace: `resources\icons\app_icon.ico`
   - Size: 256x256 pixels
   - Format: .ico (multi-resolution)

2. Update `RecoveryAssistant.spec`:
   ```python
   icon='resources/icons/app_icon.ico'
   ```

### Customize Installer Images

Create custom images for installer:
- `resources\installer\wizard_large.bmp` (164x314 pixels)
- `resources\installer\wizard_small.bmp` (55x58 pixels)

### Add/Remove Dependencies

Edit `requirements.txt` and `RecoveryAssistant.spec`:

```python
hiddenimports=[
    'your_package',
    # ...
]
```

## Troubleshooting

### Build Errors

**Error: "Module not found"**
- Solution: Add to `hiddenimports` in `.spec` file

**Error: "Failed to execute script"**
- Solution: Build with console enabled to see errors:
  ```python
  console=True  # in .spec file
  ```

**Error: "Permission denied"**
- Solution: Run Command Prompt as Administrator

### Executable Issues

**Application won't start**
- Check: `dist\RecoveryAssistant.exe` exists
- Check: Windows Defender didn't quarantine it
- Run from command line to see errors

**Large executable size**
- Normal: 100-150 MB (includes Python + all dependencies)
- Enable UPX compression in `.spec`: `upx=True`
- Exclude unnecessary packages

**Slow startup**
- Normal: First launch takes 5-10 seconds
- One-folder distribution is faster (see `.spec` comments)

### Installer Issues

**Inno Setup not found**
- Install from: https://jrsoftware.org/isdl.php
- Default path: `C:\Program Files (x86)\Inno Setup 6\`

**Installer creation fails**
- Check: All paths in `setup.iss` are correct
- Check: `dist\RecoveryAssistant.exe` exists
- Check: Resource files exist

## Build Optimization

### Reduce Executable Size

1. **Exclude test/dev packages:**
   ```python
   excludes=[
       'matplotlib',  # If not using charts
       'scipy',
       'pytest',
       'unittest',
   ]
   ```

2. **Use one-folder distribution:**
   - Faster startup
   - Easier updates
   - Slightly larger total size
   - Uncomment `COLLECT` section in `.spec`

3. **Enable UPX compression:**
   ```python
   upx=True,
   upx_exclude=[],
   ```

### Improve Startup Speed

1. **Use one-folder distribution** (vs one-file)

2. **Lazy imports** in code:
   ```python
   def function_that_uses_pandas():
       import pandas as pd  # Import when needed
       # ...
   ```

3. **Reduce hiddenimports** - only include what's needed

## Testing Checklist

Before distributing the installer:

- [ ] Executable launches successfully
- [ ] Setup wizard appears on first run
- [ ] Can enter API keys and save configuration
- [ ] Outlook connection test works
- [ ] Can import PDF/CSV files
- [ ] Database is created correctly
- [ ] GUI elements render properly
- [ ] No console window appears
- [ ] Application icon shows correctly
- [ ] Uninstaller works
- [ ] Desktop shortcut works (if created)
- [ ] Start with Windows works (if enabled)

## Distribution

### For End Users

Distribute: `RecoveryAssistant_Setup_v1.0.0.exe`

**Instructions:**
1. Download the installer
2. Double-click to run
3. Follow installation wizard
4. Launch from Start Menu
5. Complete setup wizard

### Digital Signature (Recommended)

For production release, sign the executable and installer:

```batch
signtool sign /f certificate.pfx /p password /tr http://timestamp.digicert.com dist\RecoveryAssistant.exe
signtool sign /f certificate.pfx /p password /tr http://timestamp.digicert.com dist\installer\RecoveryAssistant_Setup_v1.0.0.exe
```

Benefits:
- No Windows SmartScreen warnings
- User trust
- Professional appearance

## Continuous Integration

### GitHub Actions Example

```yaml
name: Build Windows Installer

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Build
        run: |
          cd desktop_app
          build_installer.bat
      - name: Upload
        uses: actions/upload-artifact@v2
        with:
          name: installer
          path: desktop_app/dist/installer/
```

## Support

For build issues:
- Check logs in `build\` directory
- Open GitHub issue with error details
- Include: Python version, Windows version, error message

---

**Last Updated:** 2024
**Build Script Version:** 1.0.0
