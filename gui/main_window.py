"""
Peak Volume Manager - Main Window
Primary application window with meters, graph, controls, and tray integration.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QCheckBox, QLabel, QGroupBox, QStatusBar, QApplication, QSlider,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QPalette, QColor

from gui.meters import LevelMeter, GainReductionMeter
from gui.graph import LevelGraph
from gui.controls import ControlsPanel
from gui.tray import SystemTray, create_default_icon
from presets import PRESETS


class MainWindow(QMainWindow):
    """
    Main application window for Peak Volume Manager.
    """

    def __init__(self, audio_monitor, volume_controller, settings, parent=None):
        super().__init__(parent)
        self.audio_monitor = audio_monitor
        self.volume_controller = volume_controller
        self.settings = settings

        self._latest_result = {
            "input_rms_db": -60.0,
            "input_peak_db": -60.0,
            "gain_reduction_db": 0.0,
            "output_db": -60.0,
            "target_volume_scalar": 1.0,
        }

        self.setWindowTitle("Peak Volume Manager")
        self.setMinimumSize(520, 680)
        self.resize(560, 740)
        self.setWindowIcon(create_default_icon(64, True))

        self._apply_theme()
        self._build_ui()
        self._setup_tray()
        self._load_settings()

        # Update timer for GUI refresh (~20 fps for smooth meters)
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(50)  # 50ms = 20fps

    def _apply_theme(self):
        """Apply dark/light theme based on system preference."""
        app = QApplication.instance()
        # Detect system theme
        palette = app.palette()
        bg = palette.color(QPalette.ColorRole.Window)
        is_dark = bg.lightness() < 128

        if not is_dark:
            # Force dark theme for a media-friendly look
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.ColorRole.Window, QColor("#2b2b2b"))
            dark_palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
            dark_palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e1e"))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#353535"))
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2b2b2b"))
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e0e0e0"))
            dark_palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
            dark_palette.setColor(QPalette.ColorRole.Button, QColor("#353535"))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
            dark_palette.setColor(QPalette.ColorRole.Link, QColor("#42A5F5"))
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor("#2196F3"))
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            app.setPalette(dark_palette)

        app.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #444;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #2196F3;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #2196F3;
                border-radius: 3px;
            }
            QPushButton {
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton#enableBtn {
                background-color: #4CAF50;
                color: white;
                font-size: 12px;
                padding: 8px 24px;
            }
            QPushButton#enableBtn:checked {
                background-color: #F44336;
            }
        """)

    def _build_ui(self):
        """Build the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 8, 12, 8)

        # === Header row: enable button + status ===
        header_layout = QHBoxLayout()

        self._enable_btn = QPushButton("● ENABLED")
        self._enable_btn.setObjectName("enableBtn")
        self._enable_btn.setCheckable(True)
        self._enable_btn.setChecked(True)
        self._enable_btn.clicked.connect(self._on_enable_toggled)
        header_layout.addWidget(self._enable_btn)

        header_layout.addStretch()

        self._status_label = QLabel("Monitoring system audio...")
        self._status_label.setFont(QFont("", 9))
        header_layout.addWidget(self._status_label)

        main_layout.addLayout(header_layout)

        # === Meters section ===
        meters_group = QGroupBox("Levels")
        meters_layout = QVBoxLayout(meters_group)
        meters_layout.setSpacing(4)

        self._input_meter = LevelMeter("Input", -60.0, 0.0)
        meters_layout.addWidget(self._input_meter)

        self._output_meter = LevelMeter("Output", -60.0, 0.0,
                                        color_normal="#66BB6A")
        meters_layout.addWidget(self._output_meter)

        self._reduction_meter = GainReductionMeter()
        meters_layout.addWidget(self._reduction_meter)

        main_layout.addWidget(meters_group)

        # === Volume Control ===
        volume_group = QGroupBox("Master Volume")
        volume_layout = QHBoxLayout(volume_group)
        volume_layout.setSpacing(8)

        # Mute button
        self._mute_btn = QPushButton("🔊")
        self._mute_btn.setFixedSize(36, 36)
        self._mute_btn.setCheckable(True)
        self._mute_btn.setStyleSheet("""
            QPushButton { font-size: 16px; border-radius: 4px; padding: 0px; }
            QPushButton:checked { background-color: #F44336; }
        """)
        self._mute_btn.clicked.connect(self._on_mute_toggled)
        volume_layout.addWidget(self._mute_btn)

        # Volume slider (0-100)
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setMinimum(0)
        self._volume_slider.setMaximum(100)
        self._volume_slider.setValue(100)
        self._volume_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        volume_layout.addWidget(self._volume_slider, stretch=1)

        # Volume percentage readout
        self._volume_readout = QLabel("100%")
        self._volume_readout.setFixedWidth(50)
        self._volume_readout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        readout_font = QFont("Consolas", 10)
        readout_font.setBold(True)
        self._volume_readout.setFont(readout_font)
        volume_layout.addWidget(self._volume_readout)

        main_layout.addWidget(volume_group)

        # === Level history graph ===
        self._graph = LevelGraph(history_seconds=10.0, updates_per_second=20.0)
        main_layout.addWidget(self._graph)

        # === Controls ===
        self._controls = ControlsPanel()
        self._controls.paramChanged.connect(self._on_param_changed)
        self._controls.presetChanged.connect(self._on_preset_changed)
        main_layout.addWidget(self._controls)

        # === Footer: tray + autostart ===
        footer_layout = QHBoxLayout()

        self._tray_btn = QPushButton("Minimize to Tray")
        self._tray_btn.clicked.connect(self._minimize_to_tray)
        footer_layout.addWidget(self._tray_btn)

        footer_layout.addStretch()

        self._autostart_cb = QCheckBox("Auto-start with Windows")
        self._autostart_cb.stateChanged.connect(self._on_autostart_changed)
        footer_layout.addWidget(self._autostart_cb)

        main_layout.addLayout(footer_layout)

        # === Status bar ===
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("Ready")

    def _setup_tray(self):
        """Set up system tray icon."""
        self._tray = SystemTray(self)
        self._tray.show_requested.connect(self._restore_from_tray)
        self._tray.toggle_requested.connect(self._on_enable_toggled)
        self._tray.quit_requested.connect(self._quit)
        self._tray.show()

    def _load_settings(self):
        """Load saved settings into the UI."""
        s = self.settings

        # Enable state
        enabled = s.get("enabled", True)
        self._enable_btn.setChecked(enabled)
        self._on_enable_toggled()

        # Preset and slider values
        preset = s.get("preset", "Moderate")
        if preset in PRESETS:
            self._controls.load_preset(preset)
        else:
            self._controls.set_values(s)

        # Apply compressor params
        params = self._controls.get_values()
        self.audio_monitor.update_compressor(**params)

        # Auto-start
        self._autostart_cb.setChecked(s.get("auto_start", False))

        # Volume control
        base_vol = s.get("base_volume", None)
        if base_vol is not None:
            vol_pct = int(base_vol * 100)
            self._volume_slider.setValue(vol_pct)
            self.volume_controller.set_base_volume(base_vol)
        else:
            # First run: capture current system volume as the base
            current = self.volume_controller.get_current_volume()
            self._volume_slider.setValue(int(current * 100))

        muted = s.get("muted", False)
        self._mute_btn.setChecked(muted)
        self._on_mute_toggled()

        # Window geometry
        geom = s.get("window_geometry")
        if geom and len(geom) == 4:
            self.setGeometry(*geom)

    def _save_settings(self):
        """Save current state to settings."""
        params = self._controls.get_values()
        self.settings.update(params)
        self.settings["enabled"] = self._enable_btn.isChecked()
        self.settings["preset"] = self._controls.get_preset()
        self.settings["auto_start"] = self._autostart_cb.isChecked()
        self.settings["base_volume"] = self._volume_slider.value() / 100.0
        self.settings["muted"] = self._mute_btn.isChecked()
        geom = self.geometry()
        self.settings["window_geometry"] = [geom.x(), geom.y(), geom.width(), geom.height()]

    def set_audio_callback_result(self, result: dict):
        """Called from the audio monitor thread with new data."""
        self._latest_result = result

    @pyqtSlot()
    def _update_display(self):
        """Periodic GUI update from the latest audio data."""
        r = self._latest_result

        # Update meters
        self._input_meter.set_level(r["input_peak_db"])
        self._output_meter.set_level(r["output_db"])
        self._reduction_meter.set_level(r["gain_reduction_db"])

        # Update graph
        self._graph.add_data(r["input_peak_db"], r["output_db"], r["gain_reduction_db"])

        # Apply volume control
        if self._enable_btn.isChecked():
            self.volume_controller.apply_scalar(r["target_volume_scalar"])

        # Status bar
        vol_pct = self._volume_slider.value()
        reduction = r["gain_reduction_db"]
        if self._mute_btn.isChecked():
            self._statusbar.showMessage(f"MUTED | Volume: {vol_pct}%")
        elif reduction < -0.5:
            self._statusbar.showMessage(
                f"Compressing: {reduction:+.1f} dB reduction | "
                f"Volume: {vol_pct}% | Scale: {r['target_volume_scalar']:.0%}"
            )
        else:
            self._statusbar.showMessage(f"Monitoring — no reduction active | Volume: {vol_pct}%")

    @pyqtSlot()
    def _on_enable_toggled(self):
        """Toggle compression on/off."""
        enabled = self._enable_btn.isChecked()
        if enabled:
            self._enable_btn.setText("● ENABLED")
            self._enable_btn.setStyleSheet("background-color: #4CAF50; color: white;")
            self._status_label.setText("Monitoring system audio...")
        else:
            self._enable_btn.setText("○ DISABLED")
            self._enable_btn.setStyleSheet("background-color: #F44336; color: white;")
            self._status_label.setText("Compression bypassed")
            self.volume_controller.restore()

        self.audio_monitor.set_enabled(enabled)
        self._tray.set_enabled(enabled)

    @pyqtSlot(str, float)
    def _on_param_changed(self, param_name: str, value: float):
        """A compressor parameter slider was adjusted."""
        self.audio_monitor.update_compressor(**{param_name: value})

        # Update graph reference lines
        if param_name == "threshold":
            self._graph.set_threshold(value)
        elif param_name == "ceiling":
            self._graph.set_ceiling(value)

        self._save_settings()

    @pyqtSlot(str)
    def _on_preset_changed(self, preset_name: str):
        """A preset was selected."""
        if preset_name in PRESETS:
            params = PRESETS[preset_name]
            self.audio_monitor.update_compressor(**params)
            self._graph.set_threshold(params["threshold"])
            self._graph.set_ceiling(params["ceiling"])
        self._save_settings()

    @pyqtSlot()
    def _on_autostart_changed(self):
        """Toggle auto-start with Windows."""
        self._save_settings()
        # Actual Windows startup registration would go here:
        # Add/remove shortcut in shell:startup folder

    @pyqtSlot(int)
    def _on_volume_changed(self, value: int):
        """Volume slider was moved."""
        volume = value / 100.0
        self._volume_readout.setText(f"{value}%")
        self.volume_controller.set_base_volume(volume)

        # Update mute button icon based on level
        if not self._mute_btn.isChecked():
            if value == 0:
                self._mute_btn.setText("🔇")
            elif value < 33:
                self._mute_btn.setText("🔈")
            elif value < 66:
                self._mute_btn.setText("🔉")
            else:
                self._mute_btn.setText("🔊")

        self._save_settings()

    @pyqtSlot()
    def _on_mute_toggled(self):
        """Mute button was clicked."""
        muted = self._mute_btn.isChecked()
        self.volume_controller.set_muted(muted)

        if muted:
            self._mute_btn.setText("🔇")
            self._volume_slider.setEnabled(False)
            self._volume_readout.setStyleSheet("color: #666666;")
        else:
            self._volume_slider.setEnabled(True)
            self._volume_readout.setStyleSheet("")
            # Restore icon based on current level
            self._on_volume_changed(self._volume_slider.value())

        self._save_settings()

    def _minimize_to_tray(self):
        """Hide window and show tray icon."""
        self.hide()
        self._tray.show_message("Peak Volume Manager",
                                "Running in system tray. Double-click to restore.")

    def _restore_from_tray(self):
        """Restore window from tray."""
        self.showNormal()
        self.activateWindow()

    def _quit(self):
        """Clean shutdown."""
        self._save_settings()
        self.audio_monitor.stop()
        self.volume_controller.restore()
        self._tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        """Minimize to tray on close instead of quitting."""
        event.ignore()
        self._minimize_to_tray()
