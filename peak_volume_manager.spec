# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Peak Volume Manager.

Usage:
    pyinstaller peak_volume_manager.spec --noconfirm

Expects the standard gui/ subfolder layout:
    gui/main_window.py, gui/meters.py, gui/graph.py, gui/controls.py, gui/tray.py
"""

import os
import sys

block_cipher = None

# Use SPECPATH so this works regardless of where PyInstaller is invoked from
PROJECT_ROOT = SPECPATH
ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')

# --- Hidden imports: all app modules must be listed ---
hiddenimports = [
    # PyQt6 plugins needed at runtime
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.sip',
    # Windows COM / audio dependencies
    'comtypes',
    'comtypes.stream',
    'comtypes.persist',
    'comtypes._comobject',
    'comtypes._meta',
    'comtypes.automation',
    'comtypes.typeinfo',
    'comtypes.client',
    'comtypes.client._events',
    'comtypes.client._generate',
    'pycaw',
    'pycaw.pycaw',
    'pycaw.constants',
    'pycaw.utils',
    # sounddevice needs these
    'sounddevice',
    '_sounddevice_data',
    # numpy internals PyInstaller sometimes misses
    'numpy',
    'numpy.core._methods',
    'numpy.lib.format',
    # App modules (root level)
    'audio_monitor',
    'compressor',
    'volume_controller',
    'presets',
    'settings',
    # App modules (gui package)
    'gui',
    'gui.main_window',
    'gui.meters',
    'gui.graph',
    'gui.controls',
    'gui.tray',
]

# --- Icon and version info ---
icon_path = os.path.join(ASSETS_DIR, 'icon.ico')
icon_file = icon_path if os.path.exists(icon_path) else None

version_path = os.path.join(PROJECT_ROOT, 'version_info.txt')
version_file = version_path if os.path.exists(version_path) else None

# --- Analysis ---
a = Analysis(
    [os.path.join(PROJECT_ROOT, 'main.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim unnecessary large packages
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'IPython',
        'notebook',
        'sphinx',
        'pytest',
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
    [],
    exclude_binaries=True,
    name='PeakVolumeManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
    version=version_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PeakVolumeManager',
)


