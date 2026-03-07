"""
Peak Volume Manager
===================
A real-time system audio compressor/limiter for Windows.
Monitors audio output and automatically reduces volume during spikes
(like loud commercials) while keeping normal content at a comfortable level.

Usage:
    python main.py

Requirements:
    - Windows 10/11
    - Python 3.10+
    - PyQt6, numpy, sounddevice, pycaw, comtypes

For audio capture on Windows, one of:
    - WASAPI loopback device (many sound cards support this natively)
    - "Stereo Mix" enabled in Windows Sound settings
    - VB-Audio Virtual Cable (free) for guaranteed loopback capture

If no capture device is found, the app runs in simulation mode for
testing and configuration.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from audio_monitor import AudioMonitor
from volume_controller import VolumeController
from settings import load_settings, save_settings
from gui.main_window import MainWindow


def main():
    # High-DPI support
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("Peak Volume Manager")
    app.setOrganizationName("PeakVolumeManager")
    app.setQuitOnLastWindowClosed(False)  # allow tray-only operation

    # Load settings
    settings = load_settings()

    # Initialize volume controller
    vol_controller = VolumeController()

    # Initialize audio monitor
    audio_monitor = AudioMonitor(callback=None, block_duration_ms=50)

    # Create main window
    window = MainWindow(audio_monitor, vol_controller, settings)

    # Connect audio monitor callback to window
    # The GUI timer in MainWindow handles volume application at 20fps.
    # We do NOT apply volume here — doing so from both the audio thread
    # and the GUI timer causes a race condition that fights the volume slider.
    def on_audio_data(result):
        window.set_audio_callback_result(result)

    audio_monitor.callback = on_audio_data

    # Start monitoring
    audio_monitor.start()

    # Show window
    window.show()

    # Run
    exit_code = app.exec()

    # Cleanup
    audio_monitor.stop()
    vol_controller.restore()
    save_settings(settings)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
