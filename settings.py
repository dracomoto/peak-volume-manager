"""
Peak Volume Manager - Settings Persistence
Loads/saves configuration to a JSON file.
"""

import json
import os
from presets import PRESETS, DEFAULT_PRESET


SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

DEFAULT_SETTINGS = {
    "enabled": True,
    "preset": DEFAULT_PRESET,
    "auto_start": False,
    "window_geometry": None,  # saved as [x, y, width, height]
    "base_volume": None,      # user's master volume (None = use system current)
    "muted": False,
    **PRESETS[DEFAULT_PRESET],
}


def load_settings() -> dict:
    """Load settings from JSON file, falling back to defaults."""
    settings = DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                saved = json.load(f)
            settings.update(saved)
        except (json.JSONDecodeError, IOError):
            pass  # fall back to defaults
    return settings


def save_settings(settings: dict) -> None:
    """Save current settings to JSON file."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not save settings: {e}")
