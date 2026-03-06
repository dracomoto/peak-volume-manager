# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Peak Volume Manager.

Usage:
    python -m PyInstaller peak_volume_manager.spec --noconfirm

Handles both project layouts automatically:
  - gui/ subfolder (standard):  gui/main_window.py, gui/meters.py, ...
  - flat (all in root):         main_window.py, meters.py, ...
"""

import os
import sys
import glob

block_cipher = None

# Use SPECPATH so this works regardless of where PyInstaller is invoked from
PROJECT_ROOT = SPECPATH
GUI_DIR = os.path.join(PROJECT_ROOT, 'gui')
ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')

# --- Detect project layout ---
has_gui_folder = os.path.isdir(GUI_DIR) and os.path.exists(os.path.join(GUI_DIR, 'main_window.py'))

# --- Collect data files ---
datas = []
if has_gui_folder:
    # Standard layout: include the gui/ package
    gui_files = glob.glob(os.path.join(GUI_DIR, '*.py'))
    if gui_files:
        datas.append((os.path.join(GUI_DIR, '*.py'), 'gui'))
    init_file = os.path.join(GUI_DIR, '__init__.py')
    if os.path.exists(init_file):
        datas.append((init_file, 'gui'))

# --- Build hidden imports list ---
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
    # App modules
    'audio_monitor',
    'compressor',
    'volume_controller',
    'presets',
    'settings',
]

# Add gui module imports if gui/ folder exists
if has_gui_folder:
    hiddenimports += [
        'gui',
        'gui.main_window',
        'gui.meters',
        'gui.graph',
        'gui.controls',
        'gui.tray',
    ]
else:
    # Flat layout: modules are at root level
    hiddenimports += [
        'main_window',
        'meters',
        'graph',
        'controls',
        'tray',
    ]

# --- Icon and version info (relative to spec file location) ---
icon_path = os.path.join(ASSETS_DIR, 'icon.ico')
icon_file = icon_path if os.path.exists(icon_path) else None

version_path = os.path.join(PROJECT_ROOT, 'version_info.txt')
version_file = version_path if os.path.exists(version_path) else None

# --- Analysis ---
a = Analysis(
    [os.path.join(PROJECT_ROOT, 'main.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
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
