# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for RecoveryAssistant Desktop

Builds a single-file Windows executable with all dependencies bundled.
"""

block_cipher = None

# Analysis: Find all Python files and dependencies
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include resources
        ('resources', 'resources'),
        # Include templates
        ('resources/templates', 'resources/templates'),
    ],
    hiddenimports=[
        # PyQt6 modules
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtCharts',

        # Database
        'sqlalchemy',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.orm',

        # PDF processing
        'PyPDF2',
        'pdfplumber',
        'camelot',
        'cv2',
        'pytesseract',

        # Data processing
        'pandas',
        'openpyxl',
        'xlrd',

        # Microsoft Office
        'win32com',
        'win32com.client',
        'pythoncom',
        'pywintypes',
        'comtypes',

        # Xero integration
        'xero_python',
        'xero_python.accounting',
        'xero_python.api_client',
        'xero_python.identity',

        # AI & Communication
        'openai',
        'stripe',

        # HTTP
        'requests',
        'httpx',

        # Utilities
        'phonenumbers',
        'email_validator',
        'pydantic',
        'cryptography',

        # Logging
        'loguru',

        # Scheduling
        'apscheduler',
        'apscheduler.schedulers.background',
        'apscheduler.triggers.cron',
        'apscheduler.triggers.interval',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'scipy',
        'numpy.distutils',
        'tkinter',
        'test',
        'unittest',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out unnecessary files
a.datas = [x for x in a.datas if not x[0].startswith('tcl')]
a.datas = [x for x in a.datas if not x[0].startswith('tk')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RecoveryAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress executable
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/app_icon.ico',  # Application icon
    version='version_info.txt',  # Version information
    uac_admin=False,  # Don't require admin rights
    uac_uiaccess=False,
)

# Optional: Create a one-folder distribution (faster startup)
# Uncomment if you prefer a folder instead of single exe
"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RecoveryAssistant',
)
"""
