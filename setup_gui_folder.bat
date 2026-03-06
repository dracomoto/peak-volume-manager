@echo off
REM ================================================================
REM  Fix folder structure: move GUI files into gui/ subfolder
REM  Run this ONCE from the project root before building.
REM ================================================================

echo Setting up gui/ subfolder...

if not exist gui mkdir gui

REM Create __init__.py
if not exist gui\__init__.py (
    echo. > gui\__init__.py
)

REM Move GUI files into gui/ (only if they exist in root AND not already in gui/)
for %%F in (main_window.py meters.py graph.py controls.py tray.py) do (
    if exist "%%F" (
        if not exist "gui\%%F" (
            echo Moving %%F -^> gui\%%F
            move "%%F" "gui\%%F"
        ) else (
            echo gui\%%F already exists, skipping %%F
        )
    )
)

echo.
echo Done! Folder structure is now correct.
echo You can run build_installer.bat next.
pause
