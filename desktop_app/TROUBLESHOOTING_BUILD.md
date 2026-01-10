# Build Troubleshooting Guide

## Error: "python-quickbooks>=0.10.0" not found

**Problem:** The `python-quickbooks` package version 0.10.0 or higher doesn't exist.

**Solution:** This has been fixed in the latest `requirements.txt`. The line is now commented out.

If you still see this error:
1. Delete your virtual environment folder (if using one)
2. Run: `pip install -r requirements.txt` again

---

## Error: "Spec file 'RecoveryAssistant.spec' not found!"

**Problem:** You're running the build script from the wrong directory.

**Solution:**
1. Open Command Prompt
2. Navigate to the `desktop_app` folder:
   ```batch
   cd path\to\RecoveryAssistant\desktop_app
   ```
3. Verify you're in the right place:
   ```batch
   dir RecoveryAssistant.spec
   ```
   You should see the file listed.
4. Run the build script:
   ```batch
   build_simple.bat
   ```

---

## Error: Module not found during build

**Problem:** A Python package is missing from your installation.

**Solution:**
```batch
pip install -r requirements.txt --force-reinstall
```

---

## Error: "pywin32" installation fails

**Problem:** pywin32 requires Windows.

**Solutions:**

**Option A:** Install from pre-built wheel:
```batch
pip install --upgrade pywin32
python C:\Python311\Scripts\pywin32_postinstall.py -install
```

**Option B:** Use the simplified requirements:
Comment out pywin32 in `requirements.txt` for testing the build.

---

## Error: Build is very slow or hangs

**Problem:** Some packages have large dependencies (pandas, opencv).

**Solution:**

**Option A:** Be patient - first build takes 10-15 minutes

**Option B:** Reduce dependencies:
Edit `requirements.txt` and comment out:
- `pandas` (if not using CSV import)
- Heavy PDF libraries

---

## Error: Executable is too large (>200MB)

**Problem:** All dependencies are being included.

**Solutions:**

1. **Enable UPX compression** (already enabled in spec file)

2. **Exclude unnecessary packages:**
   Add to `excludes=` in `RecoveryAssistant.spec`:
   ```python
   excludes=[
       'matplotlib',
       'scipy',
       'numpy.distutils',
       'tkinter',
       'test',
       'unittest',
       'pytest',
       'IPython',
       'notebook',
   ]
   ```

3. **Use one-folder distribution:**
   Uncomment the `COLLECT` section at the end of `RecoveryAssistant.spec`

---

## Error: "Failed to execute script" when running .exe

**Problem:** Missing runtime dependency or import error.

**Solution:**

1. **Build with console enabled** to see errors:
   Edit `RecoveryAssistant.spec`:
   ```python
   console=True,  # Change from False
   ```

2. **Rebuild:**
   ```batch
   pyinstaller RecoveryAssistant.spec --clean
   ```

3. **Run and read error messages:**
   ```batch
   dist\RecoveryAssistant.exe
   ```

4. **Fix the error** (usually missing import in `hiddenimports`)

5. **Rebuild with console=False**

---

## Error: Import errors for PyQt6

**Problem:** PyQt6 modules not found.

**Solution:**
Add all PyQt6 submodules to `hiddenimports` in spec file:
```python
hiddenimports=[
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
]
```

---

## Error: Windows Defender quarantines .exe

**Problem:** Unsigned executables trigger SmartScreen.

**Solutions:**

1. **Temporary:** Add exception in Windows Defender

2. **Permanent:** Code sign the executable:
   ```batch
   signtool sign /f certificate.pfx /p password /tr http://timestamp.digicert.com dist\RecoveryAssistant.exe
   ```

---

## Simplified Build Process

If the main build script fails, try this minimal approach:

1. **Install only essential packages:**
   ```batch
   pip install PyQt6 SQLAlchemy pywin32 pyinstaller
   ```

2. **Create minimal spec file:**
   ```batch
   pyi-makespec --onefile --windowed --name RecoveryAssistant main.py
   ```

3. **Build:**
   ```batch
   pyinstaller RecoveryAssistant.spec
   ```

4. **Test:**
   ```batch
   dist\RecoveryAssistant.exe
   ```

5. **Add dependencies incrementally** until it works

---

## Quick Fixes Checklist

Before asking for help, try these:

- [ ] Are you in the `desktop_app` directory?
- [ ] Does `RecoveryAssistant.spec` exist in current directory?
- [ ] Is Python 3.11+ installed? (`python --version`)
- [ ] Are all dependencies installed? (`pip install -r requirements.txt`)
- [ ] Have you deleted `build/` and `dist/` folders?
- [ ] Is there enough disk space? (need 2-3 GB free)
- [ ] Have you tried `build_simple.bat` instead?

---

## Getting More Help

1. **Check the build log** for specific error messages

2. **Google the error message** - PyInstaller errors are common

3. **Check PyInstaller documentation:**
   https://pyinstaller.org/en/stable/

4. **Create a GitHub issue** with:
   - Full error message
   - Python version
   - Windows version
   - Output of `pip list`

---

## Alternative: Run Without Building

If you just want to test the app without creating an .exe:

```batch
cd desktop_app
python main.py
```

This runs the app directly from source code (much faster for development).

---

Last updated: 2024
