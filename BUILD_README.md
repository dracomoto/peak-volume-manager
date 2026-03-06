# Building the Peak Volume Manager Installer

This guide walks you through creating a distributable Windows installer (.exe) for Peak Volume Manager.

## What You'll End Up With

A single file — `PeakVolumeManager_Setup_1.0.0.exe` — that anyone can double-click to install the app on Windows 10/11. No Python installation required on the target machine. The installer creates Start Menu shortcuts, an optional desktop shortcut, optional auto-start with Windows, and a proper uninstaller.

## Prerequisites

You need two tools installed on your **build machine** (the computer where you create the installer):

1. **Python 3.10+** with pip — [python.org/downloads](https://www.python.org/downloads/)
2. **Inno Setup 6** — [jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php)
   - Free, lightweight installer compiler
   - Download and install with default settings

## Quick Start (Automated)

1. Copy these installer files into your `peak-volume-manager/` project folder:
   - `build_installer.bat`
   - `peak_volume_manager.spec`
   - `installer.iss`
   - `generate_icon.py`
   - `version_info.txt`

2. Double-click `build_installer.bat`

3. Wait ~2 minutes. The installer appears at:
   ```
   Output\PeakVolumeManager_Setup_1.0.0.exe
   ```

That's it. Distribute that single .exe file.

## Manual Build (Step by Step)

If the batch script doesn't work or you want more control:

### Step 1: Install build tools

```cmd
pip install pyinstaller Pillow
pip install -r requirements.txt
```

### Step 2: Generate the app icon

```cmd
python generate_icon.py
```

This creates `assets/icon.ico` (multi-resolution Windows icon) and `assets/icon_256.png`.

### Step 3: Ensure gui/__init__.py exists

PyInstaller needs this to recognize `gui/` as a Python package:

```cmd
if not exist gui\__init__.py echo. > gui\__init__.py
```

### Step 4: Run PyInstaller

```cmd
pyinstaller peak_volume_manager.spec --noconfirm --clean
```

This creates `dist/PeakVolumeManager/` containing the standalone app. You can test it right now by running `dist\PeakVolumeManager\PeakVolumeManager.exe`.

### Step 5: Compile the installer

Open `installer.iss` in Inno Setup Compiler and press Ctrl+F9 (Build > Compile), or from the command line:

```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

Output: `Output\PeakVolumeManager_Setup_1.0.0.exe`

## File Reference

| File | Purpose |
|------|---------|
| `build_installer.bat` | One-click build script that runs all steps |
| `peak_volume_manager.spec` | PyInstaller configuration — defines what to bundle, hidden imports, exclusions |
| `installer.iss` | Inno Setup script — defines the installer UI, shortcuts, registry entries |
| `generate_icon.py` | Creates the .ico file from scratch (no external icon file needed) |
| `version_info.txt` | Windows version metadata embedded in the .exe (right-click > Properties > Details) |

## What the Installer Does

When a user runs the setup .exe:

1. Shows a standard Windows install wizard
2. Lets them choose install location (default: `C:\Users\<name>\AppData\Local\Programs\Peak Volume Manager`)
3. Offers optional desktop shortcut
4. Offers optional "Start with Windows" auto-launch
5. Installs all files and creates Start Menu entries
6. Optionally launches the app immediately

The installer is ~40-60 MB depending on PyQt6 and numpy sizes.

## Customization

### Changing the version number

Update the version in three places:
- `installer.iss` — line `#define MyAppVersion "1.0.0"`
- `version_info.txt` — `filevers` and `prodvers` tuples, plus the `FileVersion` and `ProductVersion` strings
- `build_installer.bat` — the output filename reference in the echo message

### Adding a license agreement

1. Create a `LICENSE.txt` file in the project root
2. Uncomment the `LicenseFile=LICENSE.txt` line in `installer.iss`

### Changing the app icon

Replace the `generate_icon.py` script with your own, or simply place your `.ico` file at `assets/icon.ico` before building.

### Signing the installer

To avoid "Unknown publisher" warnings on Windows:
1. Get a code signing certificate (e.g., from DigiCert, Sectigo, or SSL.com)
2. After building, sign both files:
   ```cmd
   signtool sign /f cert.pfx /p password /tr http://timestamp.digicert.com /td sha256 dist\PeakVolumeManager\PeakVolumeManager.exe
   signtool sign /f cert.pfx /p password /tr http://timestamp.digicert.com /td sha256 Output\PeakVolumeManager_Setup_1.0.0.exe
   ```

## Troubleshooting

### PyInstaller: "ModuleNotFoundError: No module named 'comtypes.xxx'"

The spec file includes the most common comtypes submodules. If you hit a missing one, add it to the `hiddenimports` list in `peak_volume_manager.spec`.

### PyInstaller: "Failed to execute script"

Run the built exe from a command prompt to see the traceback:
```cmd
dist\PeakVolumeManager\PeakVolumeManager.exe
```

### Antivirus false positives

PyInstaller executables sometimes trigger antivirus warnings. Code signing (see above) largely eliminates this. You can also submit the file to your AV vendor for whitelisting.

### Build is too large

The `excludes` list in the spec file already removes common bloat (tkinter, matplotlib, etc.). For further reduction, you can try UPX compression (PyInstaller applies it automatically if UPX is on your PATH) or use `--onefile` mode instead of `--onedir` (though onefile has a slower startup time).
