# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Keyboard Macro Application.
Build: pyinstaller KeyboardMacro.spec
"""

import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Collect all submodules from our packages and dependencies
hiddenimports = [
    'keyboard',
    'keyboard._winkeyboard',
    'keyboard._nixkeyboard',
    'keyboard._generic',
    'keyboard._mouse_event',
]

# PyQt5 hidden imports
hiddenimports += collect_submodules('PyQt5')

# Our own packages
hiddenimports += collect_submodules('core')
hiddenimports += collect_submodules('ui')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'email',
        'http',
        'urllib',
        'pydoc',
        'doctest',
        'argparse',
        'difflib',
        'pdb',
        'profile',
        'pstats',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='键盘宏',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon='app_icon.ico',
)
